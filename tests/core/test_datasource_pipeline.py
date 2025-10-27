"""
Integration tests for DataSource 2-stage pipeline (v0.15.0).

Tests the 2-stage data processing pipeline:
- Stage 1: Build (load + process)
- Stage 2: Filter
- Staged caching

:hierarchy: [Tests | Core | Pipeline | Integration]
:relates-to:
 - motivated_by: "Need integration tests for v0.15.0 2-stage pipeline"
 - implements: "test_suite: 'Pipeline Integration v0.15'"
 - uses: ["class: 'DataSource'", "class: 'DataBuilder'", "class: 'DataTransformer'"]

:contract:
 - pre: "Pipeline components are functional"
 - post: "2-stage pipeline behavior is validated"

:complexity: 5
"""

import os
import tempfile

import pandas as pd
import pytest

from dashboard_lego.core import DataBuilder, DataSource, DataTransformer


# Test fixtures
@pytest.fixture
def sample_csv_file():
    """Create a temporary CSV file for testing."""
    df = pd.DataFrame(
        {
            "Date": pd.date_range("2024-01-01", periods=10),
            "Product": ["A", "B"] * 5,
            "Category": ["X", "Y"] * 5,
            "Price": [10, 20, 15, 25, 12, 22, 18, 28, 14, 24],
            "Quantity": [2, 3, 4, 5, 2, 3, 4, 5, 2, 3],
        }
    )
    fd, path = tempfile.mkstemp(suffix=".csv")
    os.close(fd)
    df.to_csv(path, index=False)
    yield path
    try:
        if os.path.exists(path):
            os.unlink(path)
    except PermissionError:
        pass


@pytest.fixture
def temp_cache_dir():
    """Create temporary cache directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    try:
        import shutil

        shutil.rmtree(temp_dir, ignore_errors=True)
    except PermissionError:
        pass


class SampleDataBuilder(DataBuilder):
    """Sample data builder that loads CSV and adds Revenue column."""

    def __init__(self, file_path: str, **kwargs):
        super().__init__(**kwargs)
        self.file_path = file_path

    def build(self, **kwargs):
        """Load CSV and add calculated Revenue column."""
        df = pd.read_csv(self.file_path)

        # Only add Revenue if columns exist
        if "Price" in df.columns and "Quantity" in df.columns:
            df["Revenue"] = df["Price"] * df["Quantity"]

        return df


class SampleDataTransformer(DataTransformer):
    """Test filter that filters by category and price."""

    def transform(self, data, **kwargs):
        df = data.copy()

        if "category" in kwargs and kwargs["category"]:
            df = df[df["Category"] == kwargs["category"]]

        if "min_price" in kwargs and kwargs["min_price"]:
            df = df[df["Price"] >= kwargs["min_price"]]

        return df


def test_pipeline_full_flow(sample_csv_file, temp_cache_dir):
    """Test complete 2-stage pipeline: build -> filter."""

    # Arrange
    def classifier(key):
        return (
            ("transform", key) if key in ["category", "min_price"] else ("build", key)
        )

    datasource = DataSource(
        data_builder=SampleDataBuilder(sample_csv_file),
        data_transformer=SampleDataTransformer(),
        param_classifier=classifier,
        cache_dir=temp_cache_dir,
    )

    # Act
    result = datasource.get_processed_data({"category": "X"})

    # Assert
    assert len(result) == 5  # Only category X
    assert "Revenue" in result.columns  # DataBuilder added this
    assert all(result["Category"] == "X")  # Filter applied


def test_pipeline_staged_caching_filter_only(sample_csv_file, temp_cache_dir):
    """Test that filter changes don't trigger rebuild."""

    # Arrange
    def classifier(key):
        return ("transform", key) if key in ["category"] else ("build", key)

    datasource = DataSource(
        data_builder=SampleDataBuilder(sample_csv_file),
        data_transformer=SampleDataTransformer(),
        param_classifier=classifier,
        cache_dir=temp_cache_dir,
    )

    # Act - First load
    result1 = datasource.get_processed_data({"category": "X"})

    # Act - Change only filter param
    result2 = datasource.get_processed_data({"category": "Y"})

    # Assert
    assert len(result1) == 5  # Category X
    assert len(result2) == 5  # Category Y
    assert all(result1["Category"] == "X")
    assert all(result2["Category"] == "Y")
    # Both should have Revenue column from builder
    assert "Revenue" in result1.columns
    assert "Revenue" in result2.columns


def test_pipeline_no_builder(sample_csv_file, temp_cache_dir):
    """Test pipeline with only filter (no builder)."""

    datasource = DataSource(
        data_transformer=SampleDataTransformer(),
        cache_dir=temp_cache_dir,
    )

    # Act - should work with default no-op builder
    result = datasource.get_processed_data({"category": "X"})

    # Assert - Returns empty DataFrame from default builder
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_pipeline_no_filter(sample_csv_file, temp_cache_dir):
    """Test pipeline with only builder (no filter)."""

    datasource = DataSource(
        data_builder=SampleDataBuilder(sample_csv_file),
        cache_dir=temp_cache_dir,
    )

    # Act - should work with default no-op filter
    result = datasource.get_processed_data({})

    # Assert
    assert len(result) == 10  # All rows (no filter)
    assert "Revenue" in result.columns  # Builder processed


def test_pipeline_cache_reuse(sample_csv_file, temp_cache_dir):
    """Test that pipeline reuses cached data."""
    # Arrange
    call_count = {"build": 0, "filter": 0}

    class CountingDataBuilder(DataBuilder):
        def __init__(self, file_path, **kwargs):
            super().__init__(**kwargs)
            self.file_path = file_path

        def build(self, **params):
            call_count["build"] += 1
            df = pd.read_csv(self.file_path)
            df["Revenue"] = df["Price"] * df["Quantity"]
            return df

    class CountingFilter(DataTransformer):
        def transform(self, data, **kwargs):
            call_count["filter"] += 1
            return data.copy()

    datasource = DataSource(
        data_builder=CountingDataBuilder(sample_csv_file),
        data_transformer=CountingFilter(),
        cache_dir=temp_cache_dir,
    )

    # Act - Load twice with same params
    datasource.get_processed_data({})
    datasource.get_processed_data({})

    # Assert - Should only call once (cached on second call)
    assert call_count["build"] == 1
    assert call_count["filter"] == 1


def test_pipeline_combined_filters(sample_csv_file, temp_cache_dir):
    """Test multiple filter parameters working together."""

    def classifier(key):
        return (
            ("transform", key) if key in ["category", "min_price"] else ("build", key)
        )

    datasource = DataSource(
        data_builder=SampleDataBuilder(sample_csv_file),
        data_transformer=SampleDataTransformer(),
        param_classifier=classifier,
        cache_dir=temp_cache_dir,
    )

    # Act
    result = datasource.get_processed_data({"category": "X", "min_price": 15})

    # Assert
    assert len(result) == 2  # Category X AND Price >= 15
    assert all(result["Category"] == "X")
    assert all(result["Price"] >= 15)


def test_pipeline_no_param_classifier(sample_csv_file, temp_cache_dir):
    """Test pipeline without param classifier (backward compatible)."""

    datasource = DataSource(
        data_builder=SampleDataBuilder(sample_csv_file),
        data_transformer=SampleDataTransformer(),
        cache_dir=temp_cache_dir,
    )

    # Act - Without classifier, all params go to build stage
    result = datasource.get_processed_data({"category": "X"})

    # Assert - Filter won't work because category is classified as build param
    # But should not error
    assert isinstance(result, pd.DataFrame)
    assert "Revenue" in result.columns
