"""
Unit tests for BaseDataSource (v0.15.0 - 2-stage pipeline).

:hierarchy: [Testing | Unit Tests | Core | BaseDataSource]
:complexity: 4
"""

import time

import numpy as np
import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from dashboard_lego.core import BaseDataSource, DataBuilder, DataTransformer
from dashboard_lego.utils.exceptions import DataLoadError


# Simple test data builder
class SampleDataBuilder(DataBuilder):
    """Sample data builder that returns test data."""

    def __init__(self, data=None, **kwargs):
        super().__init__(**kwargs)
        self.data = (
            data if data is not None else pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        )

    def build(self, params):
        return self.data.copy()


# Simple test filter
class SampleDataTransformer(DataTransformer):
    """Sample filter that filters by min value."""

    def transform(self, data, params):
        df = data.copy()
        if "min_a" in params:
            df = df[df["a"] >= params["min_a"]]
        return df


def test_datasource_in_memory_caching_hit():
    """Test that in-memory cache works correctly."""
    builder = SampleDataBuilder()
    datasource = BaseDataSource(data_builder=builder)

    # First call - cache miss
    data1 = datasource.get_processed_data()

    # Second call - cache hit
    data2 = datasource.get_processed_data()

    # Assert data is same and cached
    assert_frame_equal(data1, data2)


def test_datasource_disk_caching_hit(tmp_path):
    """Test that disk cache works correctly."""
    cache_dir = str(tmp_path / "cache")
    builder = SampleDataBuilder()
    datasource = BaseDataSource(data_builder=builder, cache_dir=cache_dir)

    # First call
    data1 = datasource.get_processed_data()

    # Second call (should hit disk cache)
    data2 = datasource.get_processed_data()

    assert_frame_equal(data1, data2)


def test_datasource_caching_miss():
    """Test cache miss with different parameters."""
    builder = SampleDataBuilder()
    filter_obj = SampleDataTransformer()

    def classifier(key):
        return "transform" if key == "min_a" else "build"

    datasource = BaseDataSource(
        data_builder=builder, data_transformer=filter_obj, param_classifier=classifier
    )

    # Different params = different cache keys
    data1 = datasource.get_processed_data({"min_a": 2})
    data2 = datasource.get_processed_data({"min_a": 3})

    assert len(data1) == 2  # a >= 2
    assert len(data2) == 1  # a >= 3


def test_datasource_cache_ttl_configuration(tmp_path):
    """Test cache TTL expiration."""
    cache_dir = str(tmp_path / "cache")
    builder = SampleDataBuilder()

    datasource = BaseDataSource(
        data_builder=builder, cache_dir=cache_dir, cache_ttl=1  # 1 second TTL
    )

    # First call
    data1 = datasource.get_processed_data()

    # Wait for TTL expiration
    time.sleep(1.5)

    # Should reload (not from cache)
    data2 = datasource.get_processed_data()

    # Data should still be equal
    assert_frame_equal(data1, data2)


def test_datasource_load_error_handling():
    """Test error handling when data building fails.

    In v0.15.0, BaseDataSource catches exceptions and returns empty DataFrame
    instead of propagating them to maintain dashboard stability.
    """

    class ErrorBuilder(DataBuilder):
        def build(self, params):
            raise ValueError("Build error")

    datasource = BaseDataSource(data_builder=ErrorBuilder())

    # Should return empty DataFrame, not raise
    result = datasource.get_processed_data()
    assert isinstance(result, pd.DataFrame)
    assert result.empty


def test_datasource_numpy_serialization(tmp_path):
    """Test that DataFrames with numpy types are cached correctly."""
    cache_dir = str(tmp_path / "cache")

    df = pd.DataFrame(
        {
            "int_col": np.array([1, 2, 3], dtype=np.int64),
            "float_col": np.array([1.1, 2.2, 3.3], dtype=np.float64),
        }
    )

    builder = SampleDataBuilder(data=df)
    datasource = BaseDataSource(data_builder=builder, cache_dir=cache_dir)

    # First call
    data1 = datasource.get_processed_data()

    # Second call (from cache)
    data2 = datasource.get_processed_data()

    assert_frame_equal(data1, data2)
    assert data2["int_col"].dtype == np.int64
    assert data2["float_col"].dtype == np.float64


# <semantic_block: test_with_transform_fn>
def test_datasource_with_transform_fn_basic():
    """
    Test with_transform_fn() creates specialized datasource with block transform.

    :hierarchy: [Testing | Unit Tests | BaseDataSource | WithTransform]
    :covers:
     - target: "BaseDataSource.with_transform_fn"
     - requirement: "Creates new datasource with additional transform"

    :scenario: "Basic transform function applied after global filter"
    :priority: "P0"
    :complexity: 3
    """
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    builder = SampleDataBuilder(data=df)
    datasource = BaseDataSource(data_builder=builder)

    # Create specialized datasource with transform
    transform_fn = lambda df: df[df["a"] >= 2]
    specialized_ds = datasource.with_transform_fn(transform_fn)

    # Get data from specialized datasource
    result = specialized_ds.get_processed_data()

    # Should have applied transform (filter a >= 2)
    assert len(result) == 2
    assert result["a"].tolist() == [2, 3]


def test_datasource_with_transform_fn_preserves_original():
    """
    Test with_transform_fn() does not modify original datasource.

    :hierarchy: [Testing | Unit Tests | BaseDataSource | Immutability]
    :covers:
     - target: "BaseDataSource.with_transform_fn"
     - requirement: "Immutable pattern - original unchanged"

    :scenario: "Original datasource returns unchanged data"
    :priority: "P0"
    :complexity: 2
    """
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    builder = SampleDataBuilder(data=df)
    original_ds = BaseDataSource(data_builder=builder)

    # Create specialized datasource
    transform_fn = lambda df: df[df["a"] >= 2]
    specialized_ds = original_ds.with_transform_fn(transform_fn)

    # Original should return all data
    original_result = original_ds.get_processed_data()
    assert len(original_result) == 3

    # Specialized should return filtered data
    specialized_result = specialized_ds.get_processed_data()
    assert len(specialized_result) == 2


def test_datasource_with_transform_fn_and_global_filter():
    """
    Test with_transform_fn() chains with global filter correctly.

    :hierarchy: [Testing | Unit Tests | BaseDataSource | Chaining]
    :covers:
     - target: "BaseDataSource.with_transform_fn"
     - requirement: "Block transform applied AFTER global filter"

    :scenario: "Global filter → Block transform pipeline"
    :priority: "P0"
    :complexity: 4
    """
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [10, 20, 30, 40, 50]})
    builder = SampleDataBuilder(data=df)

    # Global filter: keep a >= min_a
    global_filter = SampleDataTransformer()

    def classifier(key):
        return "transform" if key == "min_a" else "build"

    datasource = BaseDataSource(
        data_builder=builder,
        data_transformer=global_filter,
        param_classifier=classifier,
    )

    # Block transform: keep only rows where b > 25
    block_transform = lambda df: df[df["b"] > 25]
    specialized_ds = datasource.with_transform_fn(block_transform)

    # Get data with global filter param
    result = specialized_ds.get_processed_data({"min_a": 2})

    # Should apply: Build → GlobalFilter(a >= 2) → BlockTransform(b > 25)
    # After global filter: a in [2,3,4,5], b in [20,30,40,50]
    # After block transform: b in [30,40,50] (b > 25)
    assert len(result) == 3
    assert result["a"].tolist() == [3, 4, 5]
    assert result["b"].tolist() == [30, 40, 50]


def test_datasource_with_transform_fn_aggregation():
    """
    Test with_transform_fn() with aggregation function.

    :hierarchy: [Testing | Unit Tests | BaseDataSource | Aggregation]
    :covers:
     - target: "BaseDataSource.with_transform_fn"
     - requirement: "Supports aggregation transforms"

    :scenario: "Transform aggregates data by grouping"
    :priority: "P1"
    :complexity: 3
    """
    df = pd.DataFrame(
        {"category": ["A", "B", "A", "B", "C"], "value": [10, 20, 30, 40, 50]}
    )
    builder = SampleDataBuilder(data=df)
    datasource = BaseDataSource(data_builder=builder)

    # Block transform: aggregate by category
    agg_transform = lambda df: df.groupby("category")["value"].sum().reset_index()
    specialized_ds = datasource.with_transform_fn(agg_transform)

    result = specialized_ds.get_processed_data()

    # Should have 3 rows (A, B, C) with summed values
    assert len(result) == 3
    assert set(result["category"]) == {"A", "B", "C"}
    assert result[result["category"] == "A"]["value"].iloc[0] == 40  # 10 + 30


def test_datasource_with_transform_fn_caching():
    """
    Test with_transform_fn() caching works independently.

    :hierarchy: [Testing | Unit Tests | BaseDataSource | Caching]
    :covers:
     - target: "BaseDataSource.with_transform_fn"
     - requirement: "Specialized datasource has independent cache"

    :scenario: "Cache keys differ between original and specialized"
    :priority: "P1"
    :complexity: 3
    """
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    builder = SampleDataBuilder(data=df)
    datasource = BaseDataSource(data_builder=builder)

    # Create specialized datasource
    transform_fn = lambda df: df[df["a"] >= 2]
    specialized_ds = datasource.with_transform_fn(transform_fn)

    # First call - should cache
    result1 = specialized_ds.get_processed_data()

    # Second call - should hit cache
    result2 = specialized_ds.get_processed_data()

    assert_frame_equal(result1, result2)
    assert len(result2) == 2


def test_datasource_with_transform_fn_empty_result():
    """
    Test with_transform_fn() handles empty results gracefully.

    :hierarchy: [Testing | Unit Tests | BaseDataSource | EmptyResult]
    :covers:
     - target: "BaseDataSource.with_transform_fn"
     - requirement: "Handles empty DataFrame from transform"

    :scenario: "Transform filters out all rows"
    :priority: "P2"
    :complexity: 2
    """
    df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
    builder = SampleDataBuilder(data=df)
    datasource = BaseDataSource(data_builder=builder)

    # Transform that filters everything
    transform_fn = lambda df: df[df["a"] > 100]
    specialized_ds = datasource.with_transform_fn(transform_fn)

    result = specialized_ds.get_processed_data()

    assert len(result) == 0
    assert isinstance(result, pd.DataFrame)


# </semantic_block: test_with_transform_fn>
