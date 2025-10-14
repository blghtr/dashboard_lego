"""
Test cache sharing behavior across datasource instances.

:hierarchy: [Testing | Unit Tests | BaseDataSource | CacheSharing]
:relates-to:
 - motivated_by: "Verify cache registry contract: same cache_dir → shared Cache, cache_dir=None → shared in-memory cache [Contract-CacheSharing]"
 - implements: "Test suite for cache sharing across BaseDataSource instances"

:contract:
 - coverage: "Tests cache sharing for matching cache_dir, in-memory, and independent caches"
 - priority: "P0"

:complexity: 4
"""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from dashboard_lego.core.data_builder import DataBuilder
from dashboard_lego.core.datasource import BaseDataSource


@pytest.fixture(autouse=True)
def clear_cache_registry():
    """
    Clear cache registry before each test.

    :hierarchy: [Testing | Fixtures | CacheRegistry]
    :relates-to:
     - motivated_by: "Cache registry persists across tests, must be cleared for test isolation [Test-Isolation]"
    :contract:
     - pre: "Called automatically before each test"
     - post: "BaseDataSource._cache_registry is empty dict"
    :complexity: 1
    """
    BaseDataSource._cache_registry.clear()
    yield
    # Cleanup after test as well
    BaseDataSource._cache_registry.clear()


class SampleDataBuilder(DataBuilder):
    """
    Simple data builder for testing.

    :hierarchy: [Testing | Fixtures | SampleDataBuilder]
    """

    def __init__(self, data: pd.DataFrame, **kwargs):
        super().__init__(**kwargs)
        self.data = data

    def build(self, params):
        """Return sample data."""
        return self.data.copy()


# LLM:METADATA
# :hierarchy: [Testing | Unit Tests | BaseDataSource | CacheSharing | SameCacheDir]
# :relates-to:
#  - motivated_by: "Verify cache sharing contract: datasources with identical cache_dir paths share same Cache object [Contract-CacheSharing]"
# :contract:
#  - pre: "Two datasources created with same cache_dir string"
#  - post: "Both datasources have identical cache object (ds1.cache is ds2.cache)"
# :complexity: 2
# LLM:END
def test_cache_sharing_with_same_cache_dir():
    """
    Verify cache shared when cache_dir matches.

    :hierarchy: [Testing | Unit Tests | BaseDataSource | CacheSharing]
    :covers:
     - target: "BaseDataSource._cache_registry"
     - requirement: "Same cache_dir → shared Cache object"

    :scenario: "Two datasources with same cache_dir share cache"
    :priority: "P0"
    :complexity: 2
    """
    df1 = pd.DataFrame({"x": [1, 2, 3]})
    df2 = pd.DataFrame({"y": [4, 5, 6]})

    builder1 = SampleDataBuilder(data=df1)
    builder2 = SampleDataBuilder(data=df2)

    # Create datasources with same cache_dir
    ds1 = BaseDataSource(data_builder=builder1, cache_dir="/tmp/test_cache_shared")
    ds2 = BaseDataSource(data_builder=builder2, cache_dir="/tmp/test_cache_shared")

    # Should share same cache object
    assert ds1.cache is ds2.cache, "Expected same Cache object for matching cache_dir"


# LLM:METADATA
# :hierarchy: [Testing | Unit Tests | BaseDataSource | CacheSharing | InMemory]
# :relates-to:
#  - motivated_by: "Verify cache sharing contract: all datasources with cache_dir=None share single global in-memory Cache object [Contract-CacheSharing]"
# :contract:
#  - pre: "Two datasources created with cache_dir=None"
#  - post: "Both datasources have identical cache object (ds1.cache is ds2.cache)"
# :complexity: 2
# LLM:END
def test_cache_sharing_in_memory():
    """
    Verify all in-memory datasources share single cache.

    :hierarchy: [Testing | Unit Tests | BaseDataSource | CacheSharing]
    :covers:
     - target: "BaseDataSource._cache_registry"
     - requirement: "All cache_dir=None → shared in-memory Cache"

    :scenario: "Multiple datasources with cache_dir=None share cache"
    :priority: "P0"
    :complexity: 2
    """
    df1 = pd.DataFrame({"x": [1, 2, 3]})
    df2 = pd.DataFrame({"y": [4, 5, 6]})

    builder1 = SampleDataBuilder(data=df1)
    builder2 = SampleDataBuilder(data=df2)

    # Create datasources with cache_dir=None (in-memory)
    ds1 = BaseDataSource(data_builder=builder1, cache_dir=None)
    ds2 = BaseDataSource(data_builder=builder2, cache_dir=None)

    # Should share same in-memory cache
    assert ds1.cache is ds2.cache, "Expected same Cache object for in-memory caches"


# LLM:METADATA
# :hierarchy: [Testing | Unit Tests | BaseDataSource | CacheSharing | DifferentDirs]
# :relates-to:
#  - motivated_by: "Verify cache independence: datasources with different cache_dir paths have independent Cache objects [Contract-CacheSharing]"
# :contract:
#  - pre: "Two datasources created with different cache_dir strings"
#  - post: "Both datasources have different cache objects (ds1.cache is not ds2.cache)"
# :complexity: 2
# LLM:END
def test_cache_independent_different_dirs():
    """
    Verify caches independent when cache_dir differs.

    :hierarchy: [Testing | Unit Tests | BaseDataSource | CacheSharing]
    :covers:
     - target: "BaseDataSource._cache_registry"
     - requirement: "Different cache_dir → independent Cache objects"

    :scenario: "Datasources with different cache_dir have separate caches"
    :priority: "P0"
    :complexity: 2
    """
    df = pd.DataFrame({"x": [1, 2, 3]})
    builder = SampleDataBuilder(data=df)

    # Create datasources with different cache_dir
    ds1 = BaseDataSource(data_builder=builder, cache_dir="/tmp/cache1")
    ds2 = BaseDataSource(data_builder=builder, cache_dir="/tmp/cache2")

    # Should have different cache objects
    assert (
        ds1.cache is not ds2.cache
    ), "Expected different Cache objects for different cache_dir"


# LLM:METADATA
# :hierarchy: [Testing | Unit Tests | BaseDataSource | CacheSharing | WithTransformFnIntegration]
# :relates-to:
#  - motivated_by: "Verify with_transform_fn() correctly inherits cache from parent datasource, preventing duplicate Stage1 builds [Contract-CacheSharing]"
# :contract:
#  - pre: "Datasource created, with_transform_fn() called to create derived datasource"
#  - post: "Both datasources share same cache object, builder.build() called only once"
# :complexity: 3
# LLM:END
def test_cache_sharing_with_transform_fn_integration():
    """
    Verify with_transform_fn() shares cache with parent datasource.

    :hierarchy: [Testing | Unit Tests | BaseDataSource | CacheSharing]
    :covers:
     - target: "BaseDataSource.with_transform_fn"
     - requirement: "Derived datasource shares cache → prevents duplicate builds"

    :scenario: "with_transform_fn() reuses parent cache via registry"
    :priority: "P0"
    :complexity: 3
    """
    df = pd.DataFrame({"a": [1, 2, 3, 4, 5], "b": [10, 20, 30, 40, 50]})
    builder = SampleDataBuilder(data=df)

    # Track build calls
    build_count = 0
    original_build = builder.build

    def tracked_build(params):
        nonlocal build_count
        build_count += 1
        return original_build(params)

    builder.build = tracked_build

    # Create original datasource
    original_ds = BaseDataSource(data_builder=builder, cache_dir=None)

    # Create derived datasource via with_transform_fn
    derived_ds = original_ds.with_transform_fn(lambda df: df[df["a"] > 2])

    # Verify cache sharing
    assert (
        original_ds.cache is derived_ds.cache
    ), "Expected shared cache between parent and derived datasource"

    # Execute both datasources
    result_original = original_ds.get_processed_data()
    result_derived = derived_ds.get_processed_data()

    # Build should be called only ONCE (cache shared)
    assert build_count == 1, f"Expected 1 build call, got {build_count}"

    # Verify data correctness
    assert len(result_original) == 5  # All rows
    assert len(result_derived) == 3  # Filtered: a > 2 → [3, 4, 5]
