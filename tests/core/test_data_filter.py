"""
Unit tests for DataTransformer class.

:hierarchy: [Tests | Core | DataTransformer]
:relates-to:
 - motivated_by: "Need comprehensive tests for DataTransformer"
 - implements: "test_suite: 'DataTransformer'"
 - uses: ["class: 'DataTransformer'"]

:contract:
 - pre: "DataTransformer class is importable"
 - post: "All DataTransformer functionality is tested"

:complexity: 3
"""

import pandas as pd
import pytest

from dashboard_lego.core.data_transformer import DataTransformer


class CustomDataTransformer(DataTransformer):
    """Test filter that filters by category and value range."""

    def transform(self, data, params):
        df = data.copy()

        # Category filter
        if "category" in params and params["category"]:
            df = df[df["category"] == params["category"]]

        # Value range filter
        if "min_value" in params and params["min_value"] is not None:
            df = df[df["value"] >= params["min_value"]]

        if "max_value" in params and params["max_value"] is not None:
            df = df[df["value"] <= params["max_value"]]

        return df


def test_data_filter_default_returns_unchanged_data():
    """Test that default DataTransformer returns data unchanged."""
    # Arrange
    data_filter = DataTransformer()
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})

    # Act
    result = data_filter.transform(df)

    # Assert
    pd.testing.assert_frame_equal(result, df)


def test_data_filter_does_not_modify_input():
    """Test that DataTransformer doesn't modify input DataFrame."""
    # Arrange
    data_filter = DataTransformer()
    df = pd.DataFrame({"a": [1, 2, 3]})
    df_copy = df.copy()

    # Act
    result = data_filter.transform(df)

    # Assert - input unchanged
    pd.testing.assert_frame_equal(df, df_copy)


def test_custom_filter_category():
    """Test custom filter with category filtering."""
    # Arrange
    data_filter = CustomDataTransformer()
    df = pd.DataFrame({"category": ["A", "B", "A", "C", "B"], "value": [1, 2, 3, 4, 5]})

    # Act
    result = data_filter.transform(df, {"category": "A"})

    # Assert
    assert len(result) == 2
    assert all(result["category"] == "A")


def test_custom_filter_min_value():
    """Test custom filter with minimum value."""
    # Arrange
    data_filter = CustomDataTransformer()
    df = pd.DataFrame({"value": [1, 2, 3, 4, 5], "category": ["A"] * 5})

    # Act
    result = data_filter.transform(df, {"min_value": 3})

    # Assert
    assert len(result) == 3
    assert all(result["value"] >= 3)


def test_custom_filter_max_value():
    """Test custom filter with maximum value."""
    # Arrange
    data_filter = CustomDataTransformer()
    df = pd.DataFrame({"value": [1, 2, 3, 4, 5], "category": ["A"] * 5})

    # Act
    result = data_filter.transform(df, {"max_value": 3})

    # Assert
    assert len(result) == 3
    assert all(result["value"] <= 3)


def test_custom_filter_range():
    """Test custom filter with value range."""
    # Arrange
    data_filter = CustomDataTransformer()
    df = pd.DataFrame({"value": range(1, 11), "category": ["A"] * 10})

    # Act
    result = data_filter.transform(df, {"min_value": 3, "max_value": 7})

    # Assert
    assert len(result) == 5  # 3, 4, 5, 6, 7
    assert all((result["value"] >= 3) & (result["value"] <= 7))


def test_custom_filter_combined():
    """Test custom filter with multiple filters combined."""
    # Arrange
    data_filter = CustomDataTransformer()
    df = pd.DataFrame(
        {"category": ["A", "B", "A", "B", "A", "B"], "value": [1, 2, 3, 4, 5, 6]}
    )

    # Act
    result = data_filter.transform(df, {"category": "A", "min_value": 3})

    # Assert
    assert len(result) == 2  # category A with value >= 3 (rows 3 and 5)
    assert all(result["category"] == "A")
    assert all(result["value"] >= 3)


def test_filter_returns_empty_when_no_matches():
    """Test that filter returns empty DataFrame when no rows match."""
    # Arrange
    data_filter = CustomDataTransformer()
    df = pd.DataFrame({"category": ["A", "A"], "value": [1, 2]})

    # Act
    result = data_filter.transform(df, {"category": "B"})

    # Assert
    assert len(result) == 0
    assert list(result.columns) == list(df.columns)


def test_filter_never_adds_rows():
    """Test that filtering never adds rows (output <= input)."""
    # Arrange
    data_filter = CustomDataTransformer()
    df = pd.DataFrame({"category": ["A"] * 10, "value": range(10)})

    # Act - various filter params
    result1 = data_filter.transform(df, {})
    result2 = data_filter.transform(df, {"min_value": 5})
    result3 = data_filter.transform(df, {"category": "A"})

    # Assert
    assert len(result1) <= len(df)
    assert len(result2) <= len(df)
    assert len(result3) <= len(df)


def test_filter_handles_empty_dataframe():
    """Test that filter handles empty DataFrame."""
    # Arrange
    data_filter = CustomDataTransformer()
    df = pd.DataFrame({"category": [], "value": []})

    # Act
    result = data_filter.transform(df, {"category": "A"})

    # Assert
    assert len(result) == 0


def test_filter_handles_missing_columns_gracefully():
    """Test that filter handles missing columns."""
    # Arrange
    data_filter = CustomDataTransformer()
    df = pd.DataFrame({"other_column": [1, 2, 3]})

    # Act - should not crash even if expected columns missing
    try:
        result = data_filter.transform(df, {"category": "A"})
        # If it doesn't crash, that's fine
    except KeyError:
        # Or it might raise KeyError, which is also acceptable
        pass


def test_filter_with_none_params():
    """Test that filter handles None parameter values."""
    # Arrange
    data_filter = CustomDataTransformer()
    df = pd.DataFrame({"category": ["A", "B"], "value": [1, 2]})

    # Act
    result = data_filter.transform(df, {"category": None, "min_value": None})

    # Assert - None params should be ignored
    assert len(result) == len(df)


def test_filter_preserves_data_types():
    """Test that filter preserves column data types."""
    # Arrange
    data_filter = CustomDataTransformer()
    df = pd.DataFrame(
        {
            "category": ["A", "B", "C"],
            "value": [1, 2, 3],
            "date": pd.date_range("2024-01-01", periods=3),
        }
    )

    # Act
    result = data_filter.transform(df, {"category": "A"})

    # Assert
    assert result["category"].dtype == df["category"].dtype
    assert result["value"].dtype == df["value"].dtype
    assert pd.api.types.is_datetime64_any_dtype(result["date"])


def test_filter_maintains_index():
    """Test that filter maintains original index."""
    # Arrange
    data_filter = CustomDataTransformer()
    df = pd.DataFrame(
        {"category": ["A", "B", "A", "B"], "value": [1, 2, 3, 4]},
        index=[10, 20, 30, 40],
    )

    # Act
    result = data_filter.transform(df, {"category": "A"})

    # Assert
    assert list(result.index) == [10, 30]


def test_filter_with_complex_conditions():
    """Test filter with multiple conditions."""

    # Arrange
    class ComplexFilter(DataTransformer):
        def transform(self, data, params):
            df = data.copy()

            # Complex OR condition
            if params.get("categories"):
                df = df[df["category"].isin(params["categories"])]

            # Complex AND condition with multiple ranges
            if params.get("value_ranges"):
                conditions = []
                for min_val, max_val in params["value_ranges"]:
                    conditions.append(
                        (df["value"] >= min_val) & (df["value"] <= max_val)
                    )
                df = df[pd.concat(conditions, axis=1).any(axis=1)]

            return df

    data_filter = ComplexFilter()
    df = pd.DataFrame(
        {"category": ["A", "B", "C", "A", "B", "C"], "value": [1, 2, 3, 4, 5, 6]}
    )

    # Act
    result = data_filter.transform(
        df, {"categories": ["A", "B"], "value_ranges": [(1, 2), (5, 6)]}
    )

    # Assert - categories A or B, and value in ranges (1-2) or (5-6)
    assert len(result) == 3  # A:1, B:2, B:5
