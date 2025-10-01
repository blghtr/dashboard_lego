"""
Tests for the CsvDataSource.

:hierarchy: [Testing | Unit Tests | Core | Datasources | CsvDataSource]
:relates-to:
 - motivated_by: "Architectural Conclusion: CSV data source requires testing
   to ensure reliable data loading and caching functionality"
 - implements: "test_suite: 'CsvDataSource'"

:strategy: "Use pytest with tmp_path fixtures to create temporary CSV files for isolated testing."
:contract:
 - pre: "Test environment is set up with pytest and pandas."
 - post: "All tests for CsvDataSource pass and code coverage is 100%."

"""

from unittest.mock import patch

import pandas as pd
import pytest

from dashboard_lego.core.datasources.csv_source import CsvDataSource


@pytest.fixture
def sample_csv_path(tmp_path):
    """
    Pytest fixture to create a sample CSV file in a temporary directory.

    :hierarchy: [Testing | Fixtures | sample_csv_path]
    :covers:
     - object: "CsvDataSource file loading"
    :scenario: "Creates a temporary CSV file with sample data for tests to consume."
    :returns: The path to the created CSV file.
    """
    csv_content = "col1,col2,col3\n1,a,True\n2,b,False\n3,c,True\n4,d,True"
    csv_file = tmp_path / "sample.csv"
    csv_file.write_text(csv_content)
    return str(csv_file)


def test_csv_source_loads_file(sample_csv_path):
    """
    Tests that CsvDataSource can successfully load a well-formed CSV file.

    :hierarchy: [Testing | Unit Tests | Core | Datasources | CsvDataSource | LoadFile]
    :covers:
     - object: "CsvDataSource._load_data"
     - requirement: "The data source must load data from a valid CSV file."
    :scenario: "Given a valid file path, the data source loads the data into a pandas DataFrame."
    :contract:
     - pre: "A valid CSV file exists at the provided path."
     - post: "The get_data() method returns a DataFrame with the correct shape and content."
    """
    # Arrange
    source = CsvDataSource(file_path=sample_csv_path)

    # Act
    assert source.init_data() is True
    data = source.get_processed_data()

    # Assert
    assert data is not None
    assert isinstance(data, pd.DataFrame)
    assert data.shape == (4, 3)
    assert list(data.columns) == ["col1", "col2", "col3"]
    assert data["col1"].tolist() == [1, 2, 3, 4]


def test_csv_source_invalid_path():
    """
    Tests that CsvDataSource raises FileNotFoundError for a non-existent path.

    :hierarchy: [Testing | Unit Tests | Core | Datasources | CsvDataSource | InvalidPath]
    :covers:
     - object: "CsvDataSource._load_data"
     - requirement: "The data source must handle non-existent files gracefully."
    :scenario: "Given a path to a non-existent file, the data source raises FileNotFoundError."
    :contract:
     - pre: "The file_path provided to CsvDataSource does not exist."
     - post: "A FileNotFoundError is raised when get_data() is called."
    """
    # Arrange
    source = CsvDataSource(file_path="/non/existent/path.csv")

    # Act
    result = source.init_data()
    data = source.get_processed_data()

    # Assert
    assert result is False
    assert data.empty


def test_csv_source_with_filters(sample_csv_path):
    """
    Tests that CsvDataSource correctly applies filters to the loaded data.

    :hierarchy: [Testing | Unit Tests | Core | Datasources | CsvDataSource | Filtering]
    :covers:
     - object: "CsvDataSource._load_data"
     - requirement: "The data source must support filtering via pandas query strings."
    :scenario: "Given a filter query, the data source returns a DataFrame containing only the filtered rows."
    :contract:
     - pre: "A valid filter query is passed to the get_data method."
     - post: "The returned DataFrame's shape and content match the expected filtered result."
    """
    # Arrange
    source = CsvDataSource(file_path=sample_csv_path)
    filters = ["col1 > 2", "col3 == True"]

    # Act
    assert source.init_data(params={"filters": filters}) is True
    data = source.get_processed_data()

    # Assert
    assert data is not None
    assert data.shape == (2, 3)
    assert data["col1"].tolist() == [3, 4]


def test_csv_source_caching(sample_csv_path):
    """
    Tests that the caching mechanism in the base class is utilized.

    :hierarchy: [Testing | Unit Tests | Core | Datasources | CsvDataSource | Caching]
    :covers:
     - object: "BaseDataSource.get_data"
     - requirement: "The data source should cache results to avoid redundant file reads."
    :scenario: "When get_data() is called multiple times with the same parameters, the underlying _load_data method should only be called once."
    :contract:
     - pre: "get_data() is called."
     - post: "_load_data is called once. Subsequent calls to get_data() do not trigger _load_data again."
    """
    # Arrange
    source = CsvDataSource(file_path=sample_csv_path)

    # Act
    with patch.object(source, "_load_data", wraps=source._load_data) as mock_load_data:
        source.init_data()  # First call, should trigger load
        source.init_data()  # Second call, should use cache
        source.init_data()  # Third call, should use cache

    # Assert
    mock_load_data.assert_called_once()


def test_csv_source_with_custom_delimiter(tmp_path):
    """
    Tests that CsvDataSource can use custom delimiters via read_csv_options.

    :hierarchy: [Testing | Unit Tests | Core | Datasources | CsvDataSource | CustomDelimiter]
    :covers:
     - object: "CsvDataSource.__init__"
     - requirement: "The data source must be configurable to handle various CSV formats."
    :scenario: "Given a CSV with a semicolon delimiter and the corresponding read_csv_options, the data is parsed correctly."
    :contract:
     - pre: "A CSV file with a custom delimiter is created."
     - post: "The DataFrame is loaded correctly with the expected shape and columns."
    """
    # Arrange
    csv_content = "col1;col2\n1;a\n2;b"
    csv_file = tmp_path / "sample_semi.csv"
    csv_file.write_text(csv_content)

    options = {"delimiter": ";"}
    source = CsvDataSource(file_path=str(csv_file), read_csv_options=options)

    # Act
    assert source.init_data() is True
    data = source.get_processed_data()

    # Assert
    assert data.shape == (2, 2)
    assert list(data.columns) == ["col1", "col2"]


def test_csv_source_empty_file(tmp_path):
    """
    Tests that CsvDataSource handles empty or header-only CSV files gracefully.

    :hierarchy: [Testing | Unit Tests | Core | Datasources | CsvDataSource | EmptyFile]
    :covers:
     - object: "CsvDataSource._load_data"
     - requirement: "The data source must not fail when processing empty files."
    :scenario: "Given an empty CSV file, the data source returns an empty DataFrame."
    :contract:
     - pre: "An empty CSV file is created."
     - post: "The get_data() method returns an empty DataFrame."
    """
    # Arrange
    csv_file = tmp_path / "empty.csv"
    csv_file.write_text("col1,col2")  # Header only

    source = CsvDataSource(file_path=str(csv_file))

    # Act
    assert source.init_data() is True
    data = source.get_processed_data()

    # Assert
    assert data.empty
    assert data.shape == (0, 2)


def test_placeholder_methods(sample_csv_path):
    """
    Tests that placeholder methods return default empty values.

    :hierarchy: [Testing | Unit Tests | Core | Datasources | CsvDataSource | Placeholders]
    :covers:
     - object: "CsvDataSource.get_kpis"
     - object: "CsvDataSource.get_filter_options"
    :scenario: "Call placeholder methods to ensure they return the correct empty types."
    :contract:
     - pre: "A CsvDataSource is initialized."
     - post: "The methods return empty dicts or lists as specified."
    """
    # Arrange
    source = CsvDataSource(file_path=sample_csv_path)

    # Act & Assert
    assert source.get_kpis() == {}
    assert source.get_filter_options("any_filter") == []


def test_get_summary(sample_csv_path):
    """
    Tests the get_summary method for both loaded and unloaded data.

    :hierarchy: [Testing | Unit Tests | Core | Datasources | CsvDataSource | Summary]
    :covers:
     - object: "CsvDataSource.get_summary"
    :scenario: "Check the summary string before and after data is loaded."
    :contract:
     - pre: "A CsvDataSource is initialized."
     - post: "The summary reflects the state of the data (loaded or not loaded)."
    """
    # Arrange
    source = CsvDataSource(file_path=sample_csv_path)

    # Assert (before load)
    assert source.get_summary() == "No data loaded."

    # Act
    source.init_data()

    # Assert (after load)
    summary = source.get_summary()
    assert summary.startswith("CSV data loaded from")
    assert "Shape: (4, 3)" in summary


def test_get_processed_data_before_init(sample_csv_path):
    """
    Tests that get_processed_data returns an empty frame if called before init.

    :hierarchy: [Testing | Unit Tests | Core | Datasources | CsvDataSource | ProcessedDataEdgeCase]
    :covers:
     - object: "CsvDataSource.get_processed_data"
    :scenario: "Call get_processed_data on a new instance to ensure it doesn't crash."
    :contract:
     - pre: "A CsvDataSource is initialized but init_data is not called."
     - post: "get_processed_data returns an empty DataFrame."
    """
    # Arrange
    source = CsvDataSource(file_path=sample_csv_path)

    # Act
    data = source.get_processed_data()

    # Assert
    assert data.empty
