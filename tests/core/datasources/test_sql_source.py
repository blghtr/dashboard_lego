"""
Tests for SqlDataSource (v0.15.0).

:hierarchy: [Testing | Unit Tests | Core | Datasources | SqlDataSource]
:complexity: 3
"""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

from dashboard_lego.core.datasources.sql_source import SqlDataSource
from dashboard_lego.utils.exceptions import DataLoadError


def test_sql_source_executes_query():
    """Test that SqlDataSource executes SQL query correctly."""
    # Mock sqlalchemy
    with patch(
        "dashboard_lego.core.datasources.sql_source.create_engine"
    ) as mock_engine:
        mock_conn = Mock()
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

        # Mock pandas read_sql
        with patch("pandas.read_sql") as mock_read_sql:
            df = pd.DataFrame({"col1": [1, 2], "col2": ["a", "b"]})
            mock_read_sql.return_value = df

            source = SqlDataSource(
                connection_uri="sqlite:///:memory:", query="SELECT * FROM test"
            )

            data = source.get_processed_data()

            assert data.equals(df)
            mock_read_sql.assert_called_once()


def test_sql_source_invalid_connection_string():
    """Test that SqlDataSource handles invalid connection gracefully.

    In v0.15.0, errors are caught and empty DataFrame is returned.
    """
    source = SqlDataSource(connection_uri="invalid://connection", query="SELECT 1")

    result = source.get_processed_data()
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_sql_source_invalid_query():
    """Test that SqlDataSource handles invalid SQL query gracefully."""
    with patch(
        "dashboard_lego.core.datasources.sql_source.create_engine"
    ) as mock_engine:
        mock_conn = Mock()
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

        with patch("pandas.read_sql") as mock_read_sql:
            mock_read_sql.side_effect = Exception("SQL error")

            source = SqlDataSource(
                connection_uri="sqlite:///:memory:", query="INVALID SQL"
            )

            result = source.get_processed_data()
            assert isinstance(result, pd.DataFrame)
            assert result.empty


def test_sql_source_with_parameters():
    """Test SqlDataSource with query parameters."""
    from dashboard_lego.core import DataTransformer

    class SqlFilter(DataTransformer):
        def transform(self, data, params):
            df = data.copy()
            if "min_id" in params:
                df = df[df["id"] >= params["min_id"]]
            return df

    def classifier(key):
        return "transform"

    with patch(
        "dashboard_lego.core.datasources.sql_source.create_engine"
    ) as mock_engine:
        mock_conn = Mock()
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

        with patch("pandas.read_sql") as mock_read_sql:
            df = pd.DataFrame({"id": [1, 2, 3, 4], "value": ["a", "b", "c", "d"]})
            mock_read_sql.return_value = df

            source = SqlDataSource(
                connection_uri="sqlite:///:memory:",
                query="SELECT * FROM test",
                data_transformer=SqlFilter(),
                param_classifier=classifier,
            )

            data = source.get_processed_data({"min_id": 3})

            assert len(data) == 2  # Only id 3, 4


def test_sql_source_caching(tmp_path):
    """Test that SqlDataSource caches query results."""
    cache_dir = str(tmp_path / "cache")

    with patch(
        "dashboard_lego.core.datasources.sql_source.create_engine"
    ) as mock_engine:
        mock_conn = Mock()
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

        with patch("pandas.read_sql") as mock_read_sql:
            df = pd.DataFrame({"col1": [1, 2]})
            mock_read_sql.return_value = df

            source = SqlDataSource(
                connection_uri="sqlite:///:memory:",
                query="SELECT * FROM test",
                cache_dir=cache_dir,
            )

            # Two calls with same params
            data1 = source.get_processed_data()
            data2 = source.get_processed_data()

            # Should only call read_sql once (second is cached)
            assert mock_read_sql.call_count == 1
            assert data1.equals(data2)


def test_sql_source_caching_with_different_params(tmp_path):
    """Test caching with different filter parameters."""
    from dashboard_lego.core import DataTransformer

    class SqlFilter(DataTransformer):
        def transform(self, data, params):
            df = data.copy()
            if "status" in params:
                df = df[df["status"] == params["status"]]
            return df

    def classifier(key):
        return "transform"

    cache_dir = str(tmp_path / "cache")

    with patch(
        "dashboard_lego.core.datasources.sql_source.create_engine"
    ) as mock_engine:
        mock_conn = Mock()
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

        with patch("pandas.read_sql") as mock_read_sql:
            df = pd.DataFrame(
                {"id": [1, 2, 3], "status": ["active", "inactive", "active"]}
            )
            mock_read_sql.return_value = df

            source = SqlDataSource(
                connection_uri="sqlite:///:memory:",
                query="SELECT * FROM test",
                data_transformer=SqlFilter(),
                param_classifier=classifier,
                cache_dir=cache_dir,
            )

            data1 = source.get_processed_data({"status": "active"})
            data2 = source.get_processed_data({"status": "inactive"})

            assert len(data1) == 2  # Two active
            assert len(data2) == 1  # One inactive
