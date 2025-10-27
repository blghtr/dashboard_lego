"""
Unit tests for DataBuilder.

:hierarchy: [Testing | Unit Tests | Core | DataBuilder]
:relates-to:
 - motivated_by: "v0.15.0: State reset wrapper for DataBuilder"
 - implements: "test_suite: 'DataBuilder'"
 - uses: ["class: 'DataBuilder'"]

:contract:
 - pre: "Test environment set up with pytest and pandas"
 - post: "All tests pass, code coverage comprehensive"

:complexity: 4
:decision_cache: "Test state reset, _build method, and error handling"
"""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from dashboard_lego.core.data_builder import DataBuilder


# <semantic_block: test_fixtures>
@pytest.fixture
def sample_data():
    """
    Sample DataFrame for testing building.

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


# <semantic_block: test_builders>
class MutableStateBuilder(DataBuilder):
    """Test builder that accumulates state."""

    def __init__(self):
        super().__init__()
        self._rows = []

    def _reset_mutable_state(self):
        """Reset mutable state to prevent accumulation."""
        self._rows = []

    def _build(self, **kwargs):
        """Build that accumulates rows."""
        for i in range(kwargs.get("count", 1)):
            self._rows.append({"id": i, "value": i * 10})
        return pd.DataFrame(self._rows)


class SimpleBuilder(DataBuilder):
    """Simple builder for basic testing."""

    def _build(self, **kwargs):
        """Simple build that returns sample data."""
        return pd.DataFrame({"x": [1, 2, 3], "y": [10, 20, 30]})


# </semantic_block: test_builders>


# <semantic_block: test_mutable_state_reset>
def test_mutable_state_reset():
    """
    Test that _reset_mutable_state prevents state accumulation.

    :hierarchy: [Testing | Unit Tests | DataBuilder | MutableStateReset]
    :covers:
     - target: "DataBuilder._reset_mutable_state"
     - requirement: "Prevents state accumulation across build calls"

    :scenario: "Multiple build calls don't accumulate state"
    :priority: "P1"
    :complexity: 3
    """
    builder = MutableStateBuilder()

    # First build
    result1 = builder.build(count=2)

    assert len(result1) == 2
    assert builder._rows == [{"id": 0, "value": 0}, {"id": 1, "value": 10}]

    # Second build - should not accumulate
    result2 = builder.build(count=1)

    # Should only have new data, not accumulated
    assert len(result2) == 1
    assert builder._rows == [{"id": 0, "value": 0}]


def test_build_calls_reset_mutable_state():
    """
    Test that build() calls _reset_mutable_state before _build.

    :hierarchy: [Testing | Unit Tests | DataBuilder | BuildReset]
    :covers:
     - target: "DataBuilder.build"
     - requirement: "Calls _reset_mutable_state before _build"

    :scenario: "build() resets state then calls _build"
    :priority: "P1"
    :complexity: 2
    """
    builder = MutableStateBuilder()

    # First build to populate state
    builder.build(count=2)
    assert len(builder._rows) == 2

    # Second build should reset state first
    result = builder.build(count=1)
    assert len(result) == 1
    assert len(builder._rows) == 1


def test_simple_builder_works():
    """
    Test that simple builders work without state issues.

    :hierarchy: [Testing | Unit Tests | DataBuilder | SimpleBuilder]
    :covers:
     - target: "DataBuilder.build"
     - requirement: "Works for builders without mutable state"

    :scenario: "Simple builder returns consistent results"
    :priority: "P1"
    :complexity: 1
    """
    builder = SimpleBuilder()

    result1 = builder.build()
    result2 = builder.build()

    # Should return same result each time
    assert_frame_equal(result1, result2)
    assert len(result1) == 3


def test_build_with_params():
    """
    Test that build() passes params to _build.

    :hierarchy: [Testing | Unit Tests | DataBuilder | BuildParams]
    :covers:
     - target: "DataBuilder.build"
     - requirement: "Passes params to _build method"

    :scenario: "Params are passed through to _build"
    :priority: "P1"
    :complexity: 2
    """
    builder = MutableStateBuilder()

    result = builder.build(count=3, extra_param="test")

    assert len(result) == 3
    assert builder._rows == [
        {"id": 0, "value": 0},
        {"id": 1, "value": 10},
        {"id": 2, "value": 20},
    ]


def test_build_error_handling():
    """
    Test that build() handles errors from _build.

    :hierarchy: [Testing | Unit Tests | DataBuilder | ErrorHandling]
    :covers:
     - target: "DataBuilder.build"
     - requirement: "Handles errors from _build method"

    :scenario: "Errors in _build are propagated"
    :priority: "P2"
    :complexity: 2
    """

    class ErrorBuilder(DataBuilder):
        def _build(self, **kwargs):
            raise ValueError("Test error")

    builder = ErrorBuilder()

    with pytest.raises(ValueError, match="Test error"):
        builder.build()


# </semantic_block: test_mutable_state_reset>
