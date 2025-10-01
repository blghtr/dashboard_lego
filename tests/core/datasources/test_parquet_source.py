"""
Tests for the ParquetDataSource.

:hierarchy: [Testing | Unit Tests | Core | DataSources | ParquetDataSource]
:relates-to:
 - motivated_by: "Architectural Conclusion: Parquet data source requires testing
   to ensure reliable columnar data loading and edge case handling"
 - implements: "test_suite: 'ParquetDataSource'"

:strategy: "Use pytest with the tmp_path fixture to create temporary Parquet files for isolated testing."
:contract:
 - pre: "Test environment is set up with pytest, pandas, and pyarrow."
 - post: "All tests for ParquetDataSource pass, and code coverage for the module is high."

"""

from unittest.mock import patch

import pandas as pd
import pytest

from dashboard_lego.core.datasources.parquet_source import ParquetDataSource


@pytest.fixture
def sample_df():
    """Fixture to create a sample pandas DataFrame."""
    return pd.DataFrame(
        {
            "col1": [1, 2, 3, 4],
            "col2": ["a", "b", "c", "d"],
            "col3": [10.1, 20.2, 30.3, 40.4],
        }
    )


@pytest.fixture
def sample_parquet_path(tmp_path, sample_df):
    """
    Fixture to create a sample Parquet file for testing.

    :hierarchy: [Testing | Fixtures | sample_parquet_path]
    :scenario: "Creates a temporary Parquet file with sample data and returns its path."
    :contract:
     - post: "A valid path to a Parquet file with known content is returned."

    """
    parquet_file = tmp_path / "sample.parquet"
    sample_df.to_parquet(parquet_file)
    return str(parquet_file)


def test_parquet_source_loads_file(sample_parquet_path, sample_df):
    """
    Tests that the ParquetDataSource can successfully load a Parquet file.

    :hierarchy: [Testing | Unit Tests | Core | DataSources | ParquetDataSource | LoadFile]
    :scenario: "Given a valid path to a Parquet file, the data source loads it into a pandas DataFrame."
    :contract:
     - post: "The get_processed_data() method returns a DataFrame with the correct content."

    """
    # Arrange
    source = ParquetDataSource(file_path=sample_parquet_path)

    # Act
    source.init_data()
    data = source.get_processed_data()

    # Assert
    pd.testing.assert_frame_equal(data, sample_df)


def test_parquet_source_invalid_path():
    """
    Tests that ParquetDataSource handles a non-existent file path gracefully.

    :hierarchy: [Testing | Unit Tests | Core | DataSources | ParquetDataSource | InvalidPath]
    :scenario: "Given a path to a non-existent file, the data source returns an empty DataFrame."
    :contract:
     - post: "init_data() returns False and get_processed_data() returns an empty DataFrame."

    """
    # Arrange
    source = ParquetDataSource(file_path="/path/to/non_existent_file.parquet")

    # Act
    result = source.init_data()
    data = source.get_processed_data()

    # Assert
    assert not result
    assert data.empty


def test_parquet_source_with_filters(sample_parquet_path):
    """
    Tests that the ParquetDataSource can apply filters to the loaded data.

    :hierarchy: [Testing | Unit Tests | Core | DataSources | ParquetDataSource | Filtering]
    :scenario: "Given a filter expression, the datasource returns a filtered DataFrame."
    :contract:
     - post: "The returned DataFrame contains only rows matching the filter."

    """
    # Arrange
    source = ParquetDataSource(file_path=sample_parquet_path)
    filter_expression = "col1 > 2"
    expected_df = pd.DataFrame(
        {"col1": [3, 4], "col2": ["c", "d"], "col3": [30.3, 40.4]}
    ).reset_index(drop=True)

    # Act
    source.init_data(params={"filters": [filter_expression]})
    data = source.get_processed_data()

    # Assert
    pd.testing.assert_frame_equal(data.reset_index(drop=True), expected_df)


def test_parquet_source_columns_selection(sample_parquet_path):
    """
    Tests that the ParquetDataSource can select specific columns.

    :hierarchy: [Testing | Unit Tests | Core | DataSources | ParquetDataSource | ColumnSelection]
    :scenario: "Given a list of columns, the datasource returns a DataFrame with only those columns."
    :contract:
     - post: "The returned DataFrame contains only the specified columns."

    """
    # Arrange
    source = ParquetDataSource(file_path=sample_parquet_path)
    columns = ["col1", "col3"]
    expected_df = pd.DataFrame({"col1": [1, 2, 3, 4], "col3": [10.1, 20.2, 30.3, 40.4]})

    # Act
    source.init_data(params={"columns": columns})
    data = source.get_processed_data()

    # Assert
    pd.testing.assert_frame_equal(data, expected_df)


def test_parquet_source_caching(sample_parquet_path):
    """
    Tests that the data is cached and _load_data is not called on subsequent requests.

    :hierarchy: [Testing | Unit Tests | Core | DataSources | ParquetDataSource | Caching]
    :scenario: "When init_data is called multiple times with the same params, _load_data is only called once."
    :contract:
     - post: "_load_data is invoked only on the first call."

    """
    # Arrange
    source = ParquetDataSource(file_path=sample_parquet_path)

    # Act
    with patch.object(source, "_load_data", wraps=source._load_data) as mock_load:
        source.init_data(params={"columns": ["col1"]})
        source.init_data(params={"columns": ["col1"]})

        # Assert
        mock_load.assert_called_once()


def test_parquet_source_caching_with_different_params(sample_parquet_path):
    """
    Tests that changing params results in a new cache entry.

    :hierarchy: [Testing | Unit Tests | Core | DataSources | ParquetDataSource | Caching]
    :scenario: "When init_data is called with different params, _load_data is called each time."
    :contract:
     - post: "_load_data is invoked for each unique set of parameters."

    """
    # Arrange
    source = ParquetDataSource(file_path=sample_parquet_path)

    # Act
    with patch.object(source, "_load_data", wraps=source._load_data) as mock_load:
        source.init_data(params={"columns": ["col1"]})  # First call
        source.init_data(
            params={"columns": ["col2"]}
        )  # Second call with different params
        source.init_data(params={"columns": ["col1"]})  # Third call, same as first

        # Assert
        assert mock_load.call_count == 2


def test_parquet_placeholder_methods(sample_parquet_path):
    """
    Tests that placeholder methods return their expected empty default values.

    :hierarchy: [Testing | Unit Tests | Core | DataSources | ParquetDataSource | Placeholders]
    :scenario: "Call placeholder methods on a ParquetDataSource instance."
    :contract:
     - post: "The methods return empty dicts, lists, or strings as specified."

    """
    # Arrange
    source = ParquetDataSource(file_path=sample_parquet_path)

    # Act & Assert
    assert source.get_kpis() == {}
    assert source.get_filter_options("any_filter") == []
    assert source.get_summary() == "No data loaded."


def test_parquet_source_empty_file(tmp_path):
    """
    Tests that the ParquetDataSource handles an empty file gracefully.

    :hierarchy: [Testing | Unit Tests | Core | DataSources | ParquetDataSource | EmptyFile]
    :scenario: "Given an empty Parquet file, the datasource returns an empty DataFrame."
    :contract:
     - post: "The returned DataFrame is empty."

    """
    # Arrange
    empty_df = pd.DataFrame({"col1": []})
    parquet_file = tmp_path / "empty.parquet"
    empty_df.to_parquet(parquet_file)
    source = ParquetDataSource(file_path=str(parquet_file))

    # Act
    source.init_data()
    data = source.get_processed_data()

    # Assert
    assert data.empty
