"""
Tests for CsvDataSource (v0.15.0).

:hierarchy: [Testing | Unit Tests | Core | Datasources | CsvDataSource]
:relates-to:
 - motivated_by: "Test CsvDataSource with 2-stage pipeline"
 - implements: "test_suite: 'CsvDataSource v0.15'"

:complexity: 3
"""

from unittest.mock import patch

import pandas as pd
import pytest

from dashboard_lego.core.datasources.csv_source import CsvDataSource
from dashboard_lego.core.exceptions import DataLoadError


@pytest.fixture
def sample_csv_path(tmp_path):
    """Create sample CSV file for testing."""
    csv_content = "col1,col2,col3\n1,a,True\n2,b,False\n3,c,True\n4,d,True"
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(csv_content)
    return str(csv_file)


def test_csv_source_loads_file(sample_csv_path):
    """Test that CsvDataSource loads CSV file correctly."""
    # Arrange
    source = CsvDataSource(file_path=sample_csv_path)

    # Act
    data = source.get_processed_data()

    # Assert
    assert data is not None
    assert isinstance(data, pd.DataFrame)
    assert data.shape == (4, 3)
    assert list(data.columns) == ["col1", "col2", "col3"]
    assert data["col1"].tolist() == [1, 2, 3, 4]


def test_csv_source_invalid_path():
    """Test that CsvDataSource raises DataLoadError on non-existent file.

    In v0.16.0+, DataLoadError is raised.
    """
    source = CsvDataSource(file_path="nonexistent_file_that_does_not_exist.csv")

    # Should raise DataLoadError
    with pytest.raises(DataLoadError, match="CSV file not found"):
        source.get_processed_data()


def test_csv_source_with_filters(sample_csv_path):
    """Test CsvDataSource with data filtering."""
    from dashboard_lego.core import DataTransformer

    class SimpleFilter(DataTransformer):
        def transform(self, data, **kwargs):
            df = data.copy()
            if "min_col1" in kwargs:
                df = df[df["col1"] >= kwargs["min_col1"]]
            return df

    def classifier(key):
        return ("transform", key) if key == "min_col1" else ("build", key)

    source = CsvDataSource(
        file_path=sample_csv_path,
        data_transformer=SimpleFilter(),
        param_classifier=classifier,
    )

    # Act - filter data
    data = source.get_processed_data({"min_col1": 3})

    # Assert
    assert len(data) == 2  # Only rows 3, 4
    assert data["col1"].tolist() == [3, 4]


def test_csv_source_caching(sample_csv_path, tmp_path):
    """Test that CsvDataSource caches data correctly."""
    cache_dir = str(tmp_path / "cache")
    source = CsvDataSource(file_path=sample_csv_path, cache_dir=cache_dir)

    # First call - cache miss
    data1 = source.get_processed_data()

    # Second call - cache hit (should be faster)
    data2 = source.get_processed_data()

    # Assert
    assert data1.equals(data2)
    assert len(data1) == 4


def test_csv_source_with_custom_delimiter(tmp_path):
    """Test CsvDataSource with custom delimiter."""
    # Create CSV with semicolon delimiter
    csv_content = "col1;col2;col3\n1;a;True\n2;b;False"
    csv_file = tmp_path / "custom.csv"
    csv_file.write_text(csv_content)

    source = CsvDataSource(file_path=str(csv_file), read_csv_options={"sep": ";"})

    data = source.get_processed_data()

    assert data.shape == (2, 3)
    assert list(data.columns) == ["col1", "col2", "col3"]


def test_csv_source_empty_file(tmp_path):
    """Test CsvDataSource with empty CSV file."""
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("col1,col2\n")

    source = CsvDataSource(file_path=str(csv_file))
    data = source.get_processed_data()

    assert isinstance(data, pd.DataFrame)
    assert len(data) == 0
    assert list(data.columns) == ["col1", "col2"]


def test_get_processed_data_with_params(sample_csv_path):
    """Test that params are passed through pipeline."""
    from dashboard_lego.core import DataTransformer

    class ParamFilter(DataTransformer):
        def transform(self, data, **kwargs):
            df = data.copy()
            if "category" in kwargs:
                df = df[df["col2"] == kwargs["category"]]
            return df

    def classifier(key):
        return ("transform", key) if key == "category" else ("build", key)

    source = CsvDataSource(
        file_path=sample_csv_path,
        data_transformer=ParamFilter(),
        param_classifier=classifier,
    )

    # Act with params
    data = source.get_processed_data({"category": "b"})

    # Assert
    assert len(data) == 1
    assert data["col2"].iloc[0] == "b"
