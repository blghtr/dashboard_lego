"""
Tests for the SqlDataSource.

:hierarchy: [Testing | Unit Tests | Core | DataSources | SqlDataSource]
:relates-to:
 - motivated_by: "Ensure SqlDataSource works correctly and handles edge cases"
 - implements: "test_suite: 'SqlDataSource'"

:strategy: "Use pytest with a file-based SQLite database for isolated testing. Use a fixture to set up the database and a sample table."
:contract:
 - pre: "Test environment is set up with pytest, pandas, and sqlalchemy."
 - post: "All tests for SqlDataSource pass, and code coverage for the module is high."

"""

import importlib
import sys
from unittest.mock import patch

import pandas as pd
import pytest
from sqlalchemy import create_engine

# Import the module so we can reload it
from dashboard_lego.core.datasources import sql_source
from dashboard_lego.core.datasources.sql_source import SqlDataSource


@pytest.fixture
def db_uri(tmp_path):
    """Fixture to create a file-based SQLite database and return the URI."""
    db_path = tmp_path / "test.db"
    uri = f"sqlite:///{db_path}"
    engine = create_engine(uri)
    df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
    with engine.connect() as connection:
        df.to_sql("test_table", connection, index=False, if_exists="replace")
    return uri


def test_sql_source_executes_query(db_uri):
    """
    Tests that the SqlDataSource can successfully execute a query.

    :hierarchy: [Testing | Unit Tests | Core | DataSources | SqlDataSource | ExecuteQuery]
    :scenario: "Given a valid connection and query, the data source loads the results into a DataFrame."
    :contract:
     - post: "The get_processed_data() method returns a DataFrame with the correct content."

    """
    # Arrange
    source = SqlDataSource(connection_uri=db_uri, query="SELECT * FROM test_table")
    expected_df = pd.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})

    # Act
    source.init_data()
    data = source.get_processed_data()

    # Assert
    pd.testing.assert_frame_equal(data, expected_df)


def test_sql_source_invalid_connection_string():
    """
    Tests that SqlDataSource handles an invalid connection string gracefully.

    :hierarchy: [Testing | Unit Tests | Core | DataSources | SqlDataSource | InvalidConnection]
    :scenario: "Given an invalid connection string, init_data() returns False."
    :contract:
     - post: "init_data() returns False and get_processed_data() returns an empty DataFrame."

    """
    # Arrange
    source = SqlDataSource(connection_uri="invalid-uri", query="SELECT 1")

    # Act
    result = source.init_data()
    data = source.get_processed_data()

    # Assert
    assert not result
    assert data.empty


def test_sql_source_invalid_query(db_uri):
    """
    Tests that SqlDataSource handles an invalid SQL query gracefully.

    :hierarchy: [Testing | Unit Tests | Core | DataSources | SqlDataSource | InvalidQuery]
    :scenario: "Given an invalid SQL query, init_data() returns False."
    :contract:
     - post: "init_data() returns False and get_processed_data() returns an empty DataFrame."

    """
    # Arrange
    source = SqlDataSource(
        connection_uri=db_uri, query="SELECT * FROM non_existent_table"
    )

    # Act
    result = source.init_data()
    data = source.get_processed_data()

    # Assert
    assert not result
    assert data.empty


def test_sql_source_with_parameters(db_uri):
    """
    Tests that the SqlDataSource can execute a parameterized query.

    :hierarchy: [Testing | Unit Tests | Core | DataSources | SqlDataSource | ParameterizedQuery]
    :scenario: "Given a query with bind parameters and corresponding params, the correct filtered data is returned."
    :contract:
     - post: "The returned DataFrame contains only rows matching the parameters."

    """
    # Arrange
    query = "SELECT * FROM test_table WHERE col1 > :val"
    source = SqlDataSource(connection_uri=db_uri, query=query)
    expected_df = pd.DataFrame({"col1": [2, 3], "col2": ["b", "c"]}).reset_index(
        drop=True
    )

    # Act
    source.init_data(params={"val": 1})
    data = source.get_processed_data()

    # Assert
    pd.testing.assert_frame_equal(data.reset_index(drop=True), expected_df)


def test_sql_source_caching(db_uri):
    """
    Tests that query results are cached.

    :hierarchy: [Testing | Unit Tests | Core | DataSources | SqlDataSource | Caching]
    :scenario: "When init_data is called multiple times with the same params, _load_raw_data is only called once."
    :contract:
     - pre: "init_data called multiple times with identical params"
     - post: "_load_raw_data is invoked only on the first call (stage 1 cache hit)."
    """
    # Arrange
    source = SqlDataSource(connection_uri=db_uri, query="SELECT * FROM test_table")

    # Act
    with patch.object(
        source, "_load_raw_data", wraps=source._load_raw_data
    ) as mock_load:
        source.init_data()
        source.init_data()

        # Assert
        mock_load.assert_called_once()


def test_sql_source_caching_with_different_params(db_uri):
    """
    Tests that changing query params affects raw data loading in SQL.

    :hierarchy: [Testing | Unit Tests | Core | DataSources | SqlDataSource | Caching]
    :scenario: "When init_data is called with different query params, raw data is reloaded."
    :contract:
     - pre: "init_data called with different SQL query params"
     - post: "Raw data loaded for each unique query param set (SQL executes different queries)"

    :decision_cache: "SQL query params affect stage 1 because they change the SQL query itself"
    """
    # Arrange
    query = "SELECT * FROM test_table WHERE col1 > :val"
    source = SqlDataSource(connection_uri=db_uri, query=query)

    # Act
    with patch.object(
        source, "_load_raw_data", wraps=source._load_raw_data
    ) as mock_load:
        source.init_data(params={"val": 1})  # First call - query with val=1
        source.init_data(
            params={"val": 2}
        )  # Second call - query with val=2 (different!)
        source.init_data(params={"val": 1})  # Third call - cache hit for val=1

        # Assert - SQL executes 2 different queries (2 unique param sets)
        assert mock_load.call_count == 2


def test_sql_placeholder_and_summary_methods(db_uri):
    """
    Tests that placeholder and summary methods return their expected values.

    :hierarchy: [Testing | Unit Tests | Core | DataSources | SqlDataSource | Placeholders]
    :scenario: "Call placeholder and summary methods on a SqlDataSource instance before and after loading data."
    :contract:
     - post: "The methods return empty values or a correct summary as specified."

    """
    # Arrange
    source = SqlDataSource(connection_uri=db_uri, query="SELECT * FROM test_table")

    # Act & Assert (before load)
    assert source.get_kpis() == {}
    assert source.get_filter_options("any_filter") == []
    assert source.get_summary() == "No data loaded."

    # Act (load data)
    source.init_data()

    # Assert (after load)
    summary = source.get_summary()
    assert summary.startswith("SQL data loaded via query.")
    assert "Shape: (3, 2)" in summary


def test_sql_source_missing_sqlalchemy():
    """
    Tests that an ImportError is raised if sqlalchemy is not installed.

    :hierarchy: [Testing | Unit Tests | Core | DataSources | SqlDataSource | MissingDependency]
    :scenario: "The sql_source module is reloaded after sqlalchemy is removed from sys.modules."
    :contract:
     - post: "An ImportError with a specific message is raised."

    """
    # Arrange
    with patch.dict(sys.modules, {"sqlalchemy": None}):
        # Act & Assert
        with pytest.raises(ImportError, match="SQLAlchemy is required"):
            importlib.reload(sql_source)

    # Clean up by reloading the module with dependencies
    importlib.reload(sql_source)
