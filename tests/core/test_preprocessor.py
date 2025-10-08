"""
Unit tests for PreProcessor class.

:hierarchy: [Tests | Core | PreProcessor]
:relates-to:
 - motivated_by: "Need comprehensive tests for PreProcessor"
 - implements: "test_suite: 'PreProcessor'"
 - uses: ["class: 'PreProcessor'"]

:contract:
 - pre: "PreProcessor class is importable"
 - post: "All PreProcessor functionality is tested"

:complexity: 3
"""

import pandas as pd
import pytest

from dashboard_lego.core.preprocessor import PreProcessor


class CustomPreProcessor(PreProcessor):
    """Test preprocessor that adds a calculated column."""

    def process(self, raw_data, params):
        df = raw_data.copy()

        # Add calculated column
        if "value" in df.columns:
            df["double_value"] = df["value"] * 2

        # Apply conditional transformation based on params
        if params.get("add_squared"):
            df["squared_value"] = df["value"] ** 2

        return df


def test_preprocessor_default_returns_unchanged_data():
    """Test that default PreProcessor returns data unchanged."""
    # Arrange
    preprocessor = PreProcessor()
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

    # Act
    result = preprocessor.process(df, {})

    # Assert
    pd.testing.assert_frame_equal(result, df)


def test_preprocessor_does_not_modify_input():
    """Test that PreProcessor doesn't modify input DataFrame."""
    # Arrange
    preprocessor = PreProcessor()
    df = pd.DataFrame({"a": [1, 2, 3]})
    df_copy = df.copy()

    # Act
    result = preprocessor.process(df, {})

    # Assert - input unchanged
    pd.testing.assert_frame_equal(df, df_copy)


def test_custom_preprocessor_adds_columns():
    """Test that custom PreProcessor adds calculated columns."""
    # Arrange
    preprocessor = CustomPreProcessor()
    df = pd.DataFrame({"value": [1, 2, 3]})

    # Act
    result = preprocessor.process(df, {})

    # Assert
    assert "double_value" in result.columns
    assert list(result["double_value"]) == [2, 4, 6]


def test_custom_preprocessor_respects_params():
    """Test that PreProcessor respects params."""
    # Arrange
    preprocessor = CustomPreProcessor()
    df = pd.DataFrame({"value": [2, 3, 4]})

    # Act - without param
    result1 = preprocessor.process(df, {})

    # Act - with param
    result2 = preprocessor.process(df, {"add_squared": True})

    # Assert
    assert "squared_value" not in result1.columns
    assert "squared_value" in result2.columns
    assert list(result2["squared_value"]) == [4, 9, 16]


def test_preprocessor_handles_empty_dataframe():
    """Test that PreProcessor handles empty DataFrame."""
    # Arrange
    preprocessor = CustomPreProcessor()
    df = pd.DataFrame({"value": []})

    # Act
    result = preprocessor.process(df, {})

    # Assert
    assert len(result) == 0
    assert "double_value" in result.columns  # Column still added


def test_preprocessor_handles_missing_columns_gracefully():
    """Test that PreProcessor handles missing columns."""
    # Arrange
    preprocessor = CustomPreProcessor()
    df = pd.DataFrame({"other_column": [1, 2, 3]})

    # Act
    result = preprocessor.process(df, {})

    # Assert - should not crash, just not add double_value
    assert "double_value" not in result.columns
    assert "other_column" in result.columns


def test_preprocessor_preserves_row_count():
    """Test that PreProcessor preserves row count."""
    # Arrange
    preprocessor = CustomPreProcessor()
    df = pd.DataFrame({"value": range(100)})

    # Act
    result = preprocessor.process(df, {})

    # Assert
    assert len(result) == len(df)


def test_preprocessor_handles_nulls():
    """Test that PreProcessor handles null values."""
    # Arrange
    preprocessor = CustomPreProcessor()
    df = pd.DataFrame({"value": [1, None, 3, None, 5]})

    # Act
    result = preprocessor.process(df, {})

    # Assert
    assert "double_value" in result.columns
    # Null * 2 should still be null
    assert pd.isna(result["double_value"].iloc[1])
    assert pd.isna(result["double_value"].iloc[3])


def test_preprocessor_maintains_data_types():
    """Test that PreProcessor maintains appropriate data types."""
    # Arrange
    preprocessor = CustomPreProcessor()
    df = pd.DataFrame(
        {
            "value": [1, 2, 3],
            "text": ["a", "b", "c"],
            "date": pd.date_range("2024-01-01", periods=3),
        }
    )

    # Act
    result = preprocessor.process(df, {})

    # Assert
    assert result["text"].dtype == object
    assert pd.api.types.is_datetime64_any_dtype(result["date"])


def test_preprocessor_with_multiple_params():
    """Test PreProcessor with multiple parameters."""

    # Arrange
    class MultiParamPreProcessor(PreProcessor):
        def process(self, raw_data, params):
            df = raw_data.copy()
            if params.get("multiply_by"):
                df["result"] = df["value"] * params["multiply_by"]
            if params.get("add_constant"):
                df["result"] = df.get("result", df["value"]) + params["add_constant"]
            return df

    preprocessor = MultiParamPreProcessor()
    df = pd.DataFrame({"value": [1, 2, 3]})

    # Act
    result = preprocessor.process(df, {"multiply_by": 3, "add_constant": 10})

    # Assert
    assert "result" in result.columns
    # (value * 3) + 10
    assert list(result["result"]) == [13, 16, 19]
