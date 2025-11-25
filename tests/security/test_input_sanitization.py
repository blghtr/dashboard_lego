"""
Tests for input sanitization (XSS prevention).

:hierarchy: [Testing | Security | Sanitization]
:complexity: 2
"""

import pytest

from dashboard_lego.core.datasources.sql_source import SqlDataSource, validate_sql_query
from dashboard_lego.core.exceptions import DataLoadError
from dashboard_lego.utils.sanitization import sanitize_dict, sanitize_html


# Basic XSS prevention tests
def test_sanitize_html_basic():
    """Test basic script tag sanitization."""
    assert (
        sanitize_html("<script>alert(1)</script>")
        == "&lt;script&gt;alert(1)&lt;/script&gt;"
    )


def test_sanitize_html_quotes():
    """Test quote escaping."""
    assert sanitize_html('"><script>') == "&quot;&gt;&lt;script&gt;"


def test_sanitize_html_single_quotes():
    """Test single quote escaping."""
    result = sanitize_html("'<script>alert('XSS')</script>'")
    assert "&#x27;" in result or "&#39;" in result
    assert "&lt;script&gt;" in result


# Edge cases
def test_sanitize_html_none():
    """Test None value handling."""
    assert sanitize_html(None) == ""


def test_sanitize_html_empty_string():
    """Test empty string handling."""
    assert sanitize_html("") == ""


def test_sanitize_html_non_string():
    """Test non-string value conversion."""
    assert sanitize_html(123) == "123"
    assert sanitize_html(True) == "True"
    assert sanitize_html(3.14) == "3.14"


# XSS attack vectors
def test_sanitize_html_event_handlers():
    """Test event handler injection prevention."""
    attacks = [
        '<img onerror="alert(1)">',
        '<div onclick="alert(1)">',
        '<body onload="alert(1)">',
        '<svg onload="alert(1)">',
    ]
    for attack in attacks:
        result = sanitize_html(attack)
        assert "&lt;" in result
        assert "&gt;" in result
        assert "alert(1)" not in result or "&quot;" in result


def test_sanitize_html_data_uri():
    """Test data URI injection prevention."""
    attack = '<a href="javascript:alert(1)">Click</a>'
    result = sanitize_html(attack)
    assert "&lt;" in result
    assert "&gt;" in result


def test_sanitize_html_iframe():
    """Test iframe injection prevention."""
    attack = '<iframe src="javascript:alert(1)"></iframe>'
    result = sanitize_html(attack)
    assert "&lt;iframe" in result
    assert "&gt;" in result


def test_sanitize_html_style_injection():
    """Test style attribute injection prevention."""
    attack = '<div style="background:url(javascript:alert(1))">'
    result = sanitize_html(attack)
    assert "&lt;div" in result
    assert "&gt;" in result


def test_sanitize_html_legitimate_content():
    """Test that legitimate content is not broken."""
    # These should be escaped but readable
    text = "Hello <world> & friends"
    result = sanitize_html(text)
    assert "Hello" in result
    assert "&lt;world&gt;" in result
    assert "&amp;" in result
    assert "friends" in result


# Dictionary sanitization tests
def test_sanitize_dict():
    """Test basic dictionary sanitization."""
    input_dict = {
        "safe": "hello",
        "unsafe": "<script>",
        "nested": {"attack": "<img onerror=alert(1)>"},
    }

    result = sanitize_dict(input_dict)

    assert result["safe"] == "hello"
    assert "&lt;script&gt;" in result["unsafe"]
    assert "&lt;img" in result["nested"]["attack"]


def test_sanitize_dict_nested_lists():
    """Test sanitization of nested lists."""
    input_dict = {
        "items": [
            "safe text",
            "<script>alert(1)</script>",
            {"nested": "<img onerror=alert(1)>"},
        ]
    }

    result = sanitize_dict(input_dict)

    assert result["items"][0] == "safe text"
    assert "&lt;script&gt;" in result["items"][1]
    assert isinstance(result["items"][2], dict)
    assert "&lt;img" in result["items"][2]["nested"]


def test_sanitize_dict_empty():
    """Test empty dictionary handling."""
    assert sanitize_dict({}) == {}


def test_sanitize_dict_non_string_values():
    """Test that non-string values are preserved."""
    input_dict = {
        "number": 123,
        "boolean": True,
        "none": None,
        "list": [1, 2, 3],
    }

    result = sanitize_dict(input_dict)

    assert result["number"] == 123
    assert result["boolean"] is True
    assert result["none"] is None
    assert result["list"] == [1, 2, 3]


# SQL injection prevention tests
def test_validate_sql_query_select_allowed():
    """Test that SELECT queries are allowed."""
    validate_sql_query("SELECT * FROM users")
    validate_sql_query("SELECT id, name FROM users WHERE id = 1")
    validate_sql_query("SELECT * FROM users WHERE name LIKE '%test%'")


def test_validate_sql_query_drop_blocked():
    """Test that DROP statements are blocked."""
    with pytest.raises(DataLoadError, match="Dangerous SQL operation"):
        validate_sql_query("DROP TABLE users")


def test_validate_sql_query_delete_blocked():
    """Test that DELETE statements are blocked."""
    with pytest.raises(DataLoadError, match="Dangerous SQL operation"):
        validate_sql_query("DELETE FROM users WHERE id = 1")


def test_validate_sql_query_update_blocked():
    """Test that UPDATE statements are blocked."""
    with pytest.raises(DataLoadError, match="Dangerous SQL operation"):
        validate_sql_query("UPDATE users SET name = 'test' WHERE id = 1")


def test_validate_sql_query_alter_blocked():
    """Test that ALTER statements are blocked."""
    with pytest.raises(DataLoadError, match="Dangerous SQL operation"):
        validate_sql_query("ALTER TABLE users ADD COLUMN test VARCHAR(100)")


def test_validate_sql_query_create_blocked():
    """Test that CREATE statements are blocked."""
    with pytest.raises(DataLoadError, match="Dangerous SQL operation"):
        validate_sql_query("CREATE TABLE test (id INT)")


def test_validate_sql_query_truncate_blocked():
    """Test that TRUNCATE statements are blocked."""
    with pytest.raises(DataLoadError, match="Dangerous SQL operation"):
        validate_sql_query("TRUNCATE TABLE users")


def test_validate_sql_query_insert_blocked():
    """Test that INSERT statements are blocked."""
    with pytest.raises(DataLoadError, match="Dangerous SQL operation"):
        validate_sql_query("INSERT INTO users (name) VALUES ('test')")


def test_validate_sql_query_multiple_statements():
    """Test that multiple statements are validated."""
    with pytest.raises(DataLoadError, match="Dangerous SQL operation"):
        validate_sql_query("SELECT * FROM users; DROP TABLE users")


def test_validate_sql_query_unknown_statement():
    """Test that unknown statement types are blocked."""
    with pytest.raises(DataLoadError, match="Unknown SQL statement"):
        validate_sql_query("GRANT SELECT ON users TO admin")


def test_validate_sql_query_custom_allowed():
    """Test custom allowed statements."""
    validate_sql_query("SELECT * FROM users", allowed_statements=["SELECT", "WITH"])
    validate_sql_query(
        "WITH cte AS (SELECT * FROM users) SELECT * FROM cte",
        allowed_statements=["SELECT", "WITH"],
    )


def test_validate_sql_query_empty_query():
    """Test that empty queries are rejected."""
    with pytest.raises(DataLoadError, match="Empty SQL query"):
        validate_sql_query("")


def test_sql_datasource_blocks_dangerous_queries():
    """Test that SqlDataSource blocks dangerous queries."""
    with pytest.raises(DataLoadError, match="Dangerous SQL operation"):
        SqlDataSource(connection_uri="sqlite:///:memory:", query="DROP TABLE users")


def test_sql_datasource_allows_select():
    """Test that SqlDataSource allows SELECT queries."""
    from unittest.mock import Mock, patch

    with patch(
        "dashboard_lego.core.datasources.sql_source.create_engine"
    ) as mock_engine:
        mock_conn = Mock()
        mock_engine.return_value.connect.return_value.__enter__.return_value = mock_conn

        with patch("pandas.read_sql") as mock_read_sql:
            import pandas as pd

            df = pd.DataFrame({"col1": [1, 2]})
            mock_read_sql.return_value = df

            source = SqlDataSource(
                connection_uri="sqlite:///:memory:", query="SELECT * FROM users"
            )

            # Should not raise an error
            assert source is not None
