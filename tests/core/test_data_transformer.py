"""
Unit tests for DataTransformer and ChainedTransformer.

:hierarchy: [Testing | Unit Tests | Core | DataTransformer]
:relates-to:
 - motivated_by: "v0.15.0: Block-specific data transformations"
 - implements: "test_suite: 'DataTransformer'"
 - uses: ["class: 'DataTransformer'", "class: 'ChainedTransformer'"]

:contract:
 - pre: "Test environment set up with pytest and pandas"
 - post: "All tests pass, code coverage comprehensive"

:complexity: 5
:decision_cache: "Test chaining order, params flow, and error handling"
"""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from dashboard_lego.core.data_transformer import ChainedTransformer, DataTransformer


# <semantic_block: test_fixtures>
@pytest.fixture
def sample_data():
    """
    Sample DataFrame for testing transformations.

    :hierarchy: [Testing | Fixtures | SampleData]
    :relates-to:
     - motivated_by: "Consistent test data across test cases"
     - implements: "fixture: 'sample_data'"

    :contract:
     - pre: "None"
     - post: "Returns DataFrame with category, value, price columns"
    """
    return pd.DataFrame(
        {
            "category": ["A", "B", "A", "B", "C"],
            "value": [10, 20, 30, 40, 50],
            "price": [100, 200, 150, 250, 300],
        }
    )


# <semantic_block: test_transformers>
class FilterByCategoryTransformer(DataTransformer):
    """
    Test transformer that filters by category param.

    :hierarchy: [Testing | Transformers | FilterByCategory]
    :relates-to:
     - motivated_by: "Simulate global filter behavior"
     - implements: "class: 'FilterByCategoryTransformer'"
    """

    def transform(self, data, **kwargs):
        """Filter data by category if param provided."""
        df = data.copy()
        if "category" in kwargs:
            df = df[df["category"] == kwargs["category"]]
        return df


class AggregateTransformer(DataTransformer):
    """
    Test transformer that aggregates by category.

    :hierarchy: [Testing | Transformers | Aggregate]
    :relates-to:
     - motivated_by: "Simulate block-specific aggregation"
     - implements: "class: 'AggregateTransformer'"
    """

    def transform(self, data, **kwargs):
        """Aggregate value by category (ignores params)."""
        return data.groupby("category")["value"].sum().reset_index()


class MultiplyTransformer(DataTransformer):
    """
    Test transformer that multiplies values by factor.

    :hierarchy: [Testing | Transformers | Multiply]
    :relates-to:
     - motivated_by: "Test params usage in transformer"
     - implements: "class: 'MultiplyTransformer'"
    """

    def transform(self, data, **kwargs):
        """Multiply value by factor from params."""
        df = data.copy()
        factor = kwargs.get("factor", 1)
        df["value"] = df["value"] * factor
        return df


# </semantic_block: test_transformers>


# </semantic_block: test_fixtures>


# <semantic_block: test_base_transformer>
def test_default_transformer_returns_data_unchanged(sample_data):
    """
    Test that default DataTransformer returns data unchanged.

    :hierarchy: [Testing | Unit Tests | DataTransformer | Default]
    :covers:
     - target: "DataTransformer.transform"
     - requirement: "Default behavior returns data as-is"

    :scenario: "Calling transform without override returns original data"
    :priority: "P0"
    :complexity: 1
    """
    transformer = DataTransformer()
    result = transformer.transform(sample_data)
    assert_frame_equal(result, sample_data)


def test_filter_transformer_with_params(sample_data):
    """
    Test custom transformer filters data based on params.

    :hierarchy: [Testing | Unit Tests | DataTransformer | Filter]
    :covers:
     - target: "FilterByCategoryTransformer.transform"
     - requirement: "Transformer can use params to filter data"

    :scenario: "Filter transformer receives params and filters data"
    :priority: "P0"
    :complexity: 2
    """
    transformer = FilterByCategoryTransformer()
    result = transformer.transform(sample_data, category="A")

    expected = sample_data[sample_data["category"] == "A"]
    assert_frame_equal(result.reset_index(drop=True), expected.reset_index(drop=True))
    assert len(result) == 2


def test_filter_transformer_without_params(sample_data):
    """
    Test filter transformer returns all data when no params provided.

    :hierarchy: [Testing | Unit Tests | DataTransformer | NoFilter]
    :covers:
     - target: "FilterByCategoryTransformer.transform"
     - requirement: "Transformer handles missing params gracefully"

    :scenario: "No params provided, returns original data"
    :priority: "P1"
    :complexity: 1
    """
    transformer = FilterByCategoryTransformer()
    result = transformer.transform(sample_data)
    assert_frame_equal(result, sample_data)


# </semantic_block: test_base_transformer>


# <semantic_block: test_chained_transformer>
def test_chained_transformer_applies_sequential(sample_data):
    """
    Test ChainedTransformer applies transformers sequentially.

    :hierarchy: [Testing | Unit Tests | ChainedTransformer | Sequential]
    :covers:
     - target: "ChainedTransformer.transform"
     - requirement: "Chained transformer applies both transformers in order"

    :scenario: "Filter → Aggregate pipeline"
    :priority: "P0"
    :complexity: 3
    """
    filter_transformer = FilterByCategoryTransformer()
    agg_transformer = AggregateTransformer()
    chained = ChainedTransformer(filter_transformer, agg_transformer)

    # Should filter first (category='A'), then aggregate
    result = chained.transform(sample_data, category="A")

    # After filter: 2 rows with category A (values 10, 30)
    # After aggregate: 1 row with category A, value 40
    assert len(result) == 1
    assert result.iloc[0]["category"] == "A"
    assert result.iloc[0]["value"] == 40  # 10 + 30


def test_chained_transformer_params_flow(sample_data):
    """
    Test ChainedTransformer passes params only to first transformer.

    :hierarchy: [Testing | Unit Tests | ChainedTransformer | ParamsFlow]
    :covers:
     - target: "ChainedTransformer.transform"
     - requirement: "First transformer gets params, second gets empty dict"

    :scenario: "Verify params only flow to first transformer"
    :priority: "P0"
    :complexity: 3
    """
    # Create transformers that track what params they received
    params_received_1 = []
    params_received_2 = []

    class TrackingTransformer1(DataTransformer):
        def transform(self, data, **kwargs):
            params_received_1.append(kwargs.copy())
            return data

    class TrackingTransformer2(DataTransformer):
        def transform(self, data, **kwargs):
            params_received_2.append(kwargs.copy())
            return data

    transformer1 = TrackingTransformer1()
    transformer2 = TrackingTransformer2()
    chained = ChainedTransformer(transformer1, transformer2)

    chained.transform(sample_data, category="A")

    # First transformer should receive the params
    assert len(params_received_1) == 1
    assert params_received_1[0] == {"category": "A"}

    # Second transformer should receive empty dict
    assert len(params_received_2) == 1
    assert params_received_2[0] == {}


def test_chained_transformer_preserves_order(sample_data):
    """
    Test ChainedTransformer preserves transformation order.

    :hierarchy: [Testing | Unit Tests | ChainedTransformer | Order]
    :covers:
     - target: "ChainedTransformer.transform"
     - requirement: "Order matters: T1(data) then T2(result)"

    :scenario: "Different order produces different results"
    :priority: "P1"
    :complexity: 3
    """
    filter_transformer = FilterByCategoryTransformer()
    multiply_transformer = MultiplyTransformer()

    # Order 1: Filter then Multiply
    chain1 = ChainedTransformer(filter_transformer, multiply_transformer)
    result1 = chain1.transform(sample_data, category="A")  # Filter gets this
    # Filter to category A (2 rows), then multiply by 1 (no change from multiply)
    assert len(result1) == 2

    # Order 2: Multiply then Filter
    chain2 = ChainedTransformer(multiply_transformer, filter_transformer)
    result2 = chain2.transform(sample_data, factor=2)  # Multiply gets this
    # Multiply all values by 2, then no filter (all rows returned)
    assert len(result2) == 5
    assert result2["value"].tolist() == [20, 40, 60, 80, 100]


def test_chained_transformer_multiple_filters(sample_data):
    """
    Test chaining multiple filters works correctly.

    :hierarchy: [Testing | Unit Tests | ChainedTransformer | MultiFilter]
    :covers:
     - target: "ChainedTransformer.transform"
     - requirement: "Can chain multiple filter operations"

    :scenario: "Filter by category, then filter by price threshold"
    :priority: "P1"
    :complexity: 3
    """
    filter_category = FilterByCategoryTransformer()

    class FilterByPriceTransformer(DataTransformer):
        def transform(self, data, **kwargs):
            df = data.copy()
            min_price = kwargs.get("min_price")
            if min_price:
                df = df[df["price"] >= min_price]
            return df

    filter_price = FilterByPriceTransformer()
    chained = ChainedTransformer(filter_category, filter_price)

    # Filter to category A (2 rows), then no price filter
    result = chained.transform(sample_data, category="A")
    assert len(result) == 2


def test_chained_transformer_empty_result(sample_data):
    """
    Test ChainedTransformer handles empty intermediate results.

    :hierarchy: [Testing | Unit Tests | ChainedTransformer | EmptyResult]
    :covers:
     - target: "ChainedTransformer.transform"
     - requirement: "Handles empty DataFrame from first transformer"

    :scenario: "First transformer returns empty, second receives empty"
    :priority: "P1"
    :complexity: 2
    """
    filter_transformer = FilterByCategoryTransformer()
    agg_transformer = AggregateTransformer()
    chained = ChainedTransformer(filter_transformer, agg_transformer)

    # Filter to non-existent category
    result = chained.transform(sample_data, category="Z")

    # Should return empty DataFrame
    assert len(result) == 0


# </semantic_block: test_chained_transformer>


# <semantic_block: test_error_handling>
def test_chained_transformer_error_propagation(sample_data):
    """
    Test ChainedTransformer propagates errors from transformers.

    :hierarchy: [Testing | Unit Tests | ChainedTransformer | ErrorHandling]
    :covers:
     - target: "ChainedTransformer.transform"
     - requirement: "Errors in transformers are propagated"

    :scenario: "Transformer raises error, chained propagates it"
    :priority: "P2"
    :complexity: 2
    """

    class ErrorTransformer(DataTransformer):
        def transform(self, data, **kwargs):
            raise ValueError("Test error")

    error_transformer = ErrorTransformer()
    agg_transformer = AggregateTransformer()
    chained = ChainedTransformer(error_transformer, agg_transformer)

    with pytest.raises(ValueError, match="Test error"):
        chained.transform(sample_data)


# </semantic_block: test_error_handling>


# <semantic_block: test_mutable_state_reset>
class MutableStateTransformer(DataTransformer):
    """Test transformer that accumulates state."""

    def __init__(self):
        super().__init__()
        self._rows = []

    def _reset_mutable_state(self):
        """Reset mutable state to prevent accumulation."""
        self._rows = []

    def _transform(self, data, **kwargs):
        """Transform that accumulates rows."""
        for _, row in data.iterrows():
            self._rows.append(row.to_dict())
        return pd.DataFrame(self._rows)


def test_mutable_state_reset():
    """
    Test that _reset_mutable_state prevents state accumulation.

    :hierarchy: [Testing | Unit Tests | DataTransformer | MutableStateReset]
    :covers:
     - target: "DataTransformer._reset_mutable_state"
     - requirement: "Prevents state accumulation across transform calls"

    :scenario: "Multiple transform calls don't accumulate state"
    :priority: "P1"
    :complexity: 3
    """
    transformer = MutableStateTransformer()

    # First transform
    data1 = pd.DataFrame({"x": [1, 2], "y": [10, 20]})
    result1 = transformer.transform(data1)

    assert len(result1) == 2
    assert transformer._rows == [{"x": 1, "y": 10}, {"x": 2, "y": 20}]

    # Second transform - should not accumulate
    data2 = pd.DataFrame({"x": [3], "y": [30]})
    result2 = transformer.transform(data2)

    # Should only have data2 rows, not accumulated
    assert len(result2) == 1
    assert transformer._rows == [{"x": 3, "y": 30}]


def test_chained_transformer_uses_transform():
    """
    Test that ChainedTransformer uses _transform method.

    :hierarchy: [Testing | Unit Tests | ChainedTransformer | TransformMethod]
    :covers:
     - target: "ChainedTransformer.transform"
     - requirement: "Uses _transform method for state reset"

    :scenario: "ChainedTransformer calls _transform on both transformers"
    :priority: "P1"
    :complexity: 2
    """
    transformer1 = MutableStateTransformer()
    transformer2 = MutableStateTransformer()
    chained = ChainedTransformer(transformer1, transformer2)

    data = pd.DataFrame({"x": [1], "y": [10]})
    result = chained.transform(data)

    # Both transformers should have reset state
    assert len(transformer1._rows) == 1
    assert len(transformer2._rows) == 1


# </semantic_block: test_mutable_state_reset>
