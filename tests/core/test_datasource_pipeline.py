"""
Integration tests for BaseDataSource pipeline.

Tests the complete data processing pipeline:
- Load raw data
- Preprocess
- Filter
- Staged caching

:hierarchy: [Tests | Core | Pipeline | Integration]
:relates-to:
 - motivated_by: "Need integration tests for pipeline flow and caching"
 - implements: "test_suite: 'Pipeline Integration'"
 - uses: ["class: 'BaseDataSource'", "class: 'PreProcessor'", "class: 'DataFilter'"]

:contract:
 - pre: "Pipeline components are functional"
 - post: "Complete pipeline behavior is validated"

:complexity: 5
"""

import os
import tempfile

import pandas as pd
import pytest

from dashboard_lego.core import DataFilter, PreProcessor
from dashboard_lego.core.datasources import CsvDataSource


# Test fixtures
@pytest.fixture
def sample_csv_file():
    """Create a temporary CSV file for testing."""
    df = pd.DataFrame(
        {
            "Date": pd.date_range("2024-01-01", periods=10),
            "Product": ["A", "B"] * 5,
            "Category": ["X", "Y"] * 5,
            "Price": [10.0, 20.0, 15.0, 25.0, 12.0, 22.0, 18.0, 28.0, 11.0, 21.0],
            "Quantity": [5, 10, 7, 12, 6, 11, 8, 13, 5, 10],
        }
    )

    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", newline=""
    ) as f:
        df.to_csv(f, index=False)
        temp_path = f.name

    yield temp_path

    # Cleanup
    if os.path.exists(temp_path):
        os.unlink(temp_path)


@pytest.fixture
def temp_cache_dir():
    """Create a temporary cache directory."""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    # Cleanup - wait a bit for Windows file locks to release
    import shutil
    import time

    time.sleep(0.1)  # Give cache time to close
    if os.path.exists(temp_dir):
        try:
            shutil.rmtree(temp_dir)
        except PermissionError:
            # Windows file locking - ignore cleanup errors in tests
            pass


class SamplePreProcessor(PreProcessor):
    """Sample preprocessor that adds Revenue column."""

    def process(self, raw_data, params):
        df = raw_data.copy()

        # Only add Revenue if columns exist (handles empty DataFrame)
        if "Price" in df.columns and "Quantity" in df.columns:
            df["Revenue"] = df["Price"] * df["Quantity"]

        return df


class SampleDataFilter(DataFilter):
    """Test filter that filters by category."""

    def filter(self, data, params):
        df = data.copy()

        if "category" in params and params["category"]:
            df = df[df["Category"] == params["category"]]

        if "min_price" in params and params["min_price"] is not None:
            df = df[df["Price"] >= params["min_price"]]

        return df


def test_pipeline_full_flow(sample_csv_file, temp_cache_dir):
    """Test complete pipeline flow: load -> preprocess -> filter."""

    # Arrange
    def classifier(key):
        return "filter" if key in ["category", "min_price"] else "preprocess"

    datasource = CsvDataSource(
        file_path=sample_csv_file,
        preprocessor=SamplePreProcessor(),
        data_filter=SampleDataFilter(),
        param_classifier=classifier,
        cache_dir=temp_cache_dir,
    )

    # Act
    success = datasource.init_data({"category": "X"})
    result = datasource.get_processed_data()

    # Assert
    assert success
    assert len(result) == 5  # Only category X
    assert "Revenue" in result.columns  # Preprocessor added this
    assert all(result["Category"] == "X")  # Filter applied


def test_pipeline_staged_caching_filter_only(sample_csv_file, temp_cache_dir):
    """Test that filter changes don't reload raw data."""

    # Arrange
    def classifier(key):
        return "filter" if key in ["category"] else "preprocess"

    datasource = CsvDataSource(
        file_path=sample_csv_file,
        preprocessor=SamplePreProcessor(),
        data_filter=SampleDataFilter(),
        param_classifier=classifier,
        cache_dir=temp_cache_dir,
    )

    # Act - First load
    datasource.init_data({"category": "X"})
    result1 = datasource.get_processed_data()

    # Act - Change only filter param
    datasource.init_data({"category": "Y"})
    result2 = datasource.get_processed_data()

    # Assert
    assert len(result1) == 5  # Category X
    assert len(result2) == 5  # Category Y
    assert all(result1["Category"] == "X")
    assert all(result2["Category"] == "Y")
    # Both should have Revenue column from preprocessing
    assert "Revenue" in result1.columns
    assert "Revenue" in result2.columns


def test_pipeline_raw_data_access(sample_csv_file, temp_cache_dir):
    """Test access to raw data before preprocessing."""
    # Arrange
    datasource = CsvDataSource(
        file_path=sample_csv_file,
        preprocessor=SamplePreProcessor(),
        data_filter=SampleDataFilter(),
        cache_dir=temp_cache_dir,
    )

    # Act
    datasource.init_data()
    raw_data = datasource.get_data()
    preprocessed_data = datasource.get_preprocessed_data()
    filtered_data = datasource.get_processed_data()

    # Assert
    assert "Revenue" not in raw_data.columns  # Raw data unchanged
    assert "Revenue" in preprocessed_data.columns  # Preprocessed has it
    assert "Revenue" in filtered_data.columns  # Filtered also has it
    assert len(raw_data) == 10
    assert len(preprocessed_data) == 10
    assert len(filtered_data) == 10  # No filter applied


def test_pipeline_preprocessed_data_access(sample_csv_file, temp_cache_dir):
    """Test access to preprocessed data before filtering."""

    # Arrange
    def classifier(key):
        return "filter"

    datasource = CsvDataSource(
        file_path=sample_csv_file,
        preprocessor=SamplePreProcessor(),
        data_filter=SampleDataFilter(),
        param_classifier=classifier,
        cache_dir=temp_cache_dir,
    )

    # Act
    datasource.init_data({"category": "X"})
    preprocessed = datasource.get_preprocessed_data()
    filtered = datasource.get_processed_data()

    # Assert
    assert len(preprocessed) == 10  # All data before filtering
    assert len(filtered) == 5  # Filtered to category X
    assert "Revenue" in preprocessed.columns
    assert "Revenue" in filtered.columns


def test_pipeline_no_preprocessor(sample_csv_file, temp_cache_dir):
    """Test pipeline without custom preprocessor."""

    # Arrange
    def classifier(key):
        return "filter" if key == "category" else "preprocess"

    datasource = CsvDataSource(
        file_path=sample_csv_file,
        # No preprocessor provided - should use default
        data_filter=SampleDataFilter(),
        param_classifier=classifier,
        cache_dir=temp_cache_dir,
    )

    # Act
    datasource.init_data({"category": "X"})
    result = datasource.get_processed_data()

    # Assert
    assert len(result) == 5
    assert "Revenue" not in result.columns  # No preprocessing happened


def test_pipeline_no_filter(sample_csv_file, temp_cache_dir):
    """Test pipeline without custom filter."""
    # Arrange
    datasource = CsvDataSource(
        file_path=sample_csv_file,
        preprocessor=SamplePreProcessor(),
        # No filter provided - should use default
        cache_dir=temp_cache_dir,
    )

    # Act
    datasource.init_data({"category": "X"})
    result = datasource.get_processed_data()

    # Assert
    assert len(result) == 10  # No filtering happened
    assert "Revenue" in result.columns  # Preprocessing happened


def test_pipeline_cache_reuse(sample_csv_file, temp_cache_dir):
    """Test that pipeline reuses cached data."""
    # Arrange
    call_count = {"raw": 0, "preprocess": 0, "filter": 0}

    class CountingPreProcessor(PreProcessor):
        def process(self, raw_data, params):
            call_count["preprocess"] += 1
            df = raw_data.copy()
            df["Revenue"] = df["Price"] * df["Quantity"]
            return df

    class CountingFilter(DataFilter):
        def filter(self, data, params):
            call_count["filter"] += 1
            return data.copy()

    datasource = CsvDataSource(
        file_path=sample_csv_file,
        preprocessor=CountingPreProcessor(),
        data_filter=CountingFilter(),
        cache_dir=temp_cache_dir,
    )

    # Act - Load twice with same params
    datasource.init_data({})
    datasource.init_data({})

    # Assert - should only call once each (cache hit on second call)
    assert call_count["preprocess"] == 1
    assert call_count["filter"] == 1


def test_pipeline_combined_filters(sample_csv_file, temp_cache_dir):
    """Test pipeline with multiple filter params."""

    # Arrange
    def classifier(key):
        return "filter"

    datasource = CsvDataSource(
        file_path=sample_csv_file,
        preprocessor=SamplePreProcessor(),
        data_filter=SampleDataFilter(),
        param_classifier=classifier,
        cache_dir=temp_cache_dir,
    )

    # Act
    datasource.init_data({"category": "X", "min_price": 15})
    result = datasource.get_processed_data()

    # Assert
    assert len(result) == 2  # Category X AND price >= 15
    assert all(result["Category"] == "X")
    assert all(result["Price"] >= 15)


def test_pipeline_error_handling_empty_file(temp_cache_dir):
    """Test pipeline handles empty CSV file."""
    # Arrange - Create empty CSV
    with tempfile.NamedTemporaryFile(
        mode="w", delete=False, suffix=".csv", newline=""
    ) as f:
        f.write("col1,col2\n")  # Header only
        empty_file = f.name

    try:
        datasource = CsvDataSource(
            file_path=empty_file,
            preprocessor=SamplePreProcessor(),
            data_filter=SampleDataFilter(),
            cache_dir=temp_cache_dir,
        )

        # Act
        success = datasource.init_data()
        result = datasource.get_processed_data()

        # Assert
        assert success  # Should succeed even with empty data
        assert len(result) == 0

    finally:
        if os.path.exists(empty_file):
            os.unlink(empty_file)


def test_pipeline_no_param_classifier(sample_csv_file, temp_cache_dir):
    """Test pipeline without param classifier (all params as preprocessing)."""
    # Arrange
    datasource = CsvDataSource(
        file_path=sample_csv_file,
        preprocessor=SamplePreProcessor(),
        data_filter=SampleDataFilter(),
        # No param_classifier - defaults to all preprocessing
        cache_dir=temp_cache_dir,
    )

    # Act - Pass filter param but without classifier
    datasource.init_data({"category": "X"})
    result = datasource.get_processed_data()

    # Assert - Filter won't apply because param classified as preprocessing
    assert len(result) == 10  # All rows (no filtering)
    assert "Revenue" in result.columns  # Preprocessing happened
