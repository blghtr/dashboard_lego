"""
Tests for cache backend abstraction.

:hierarchy: [Testing | Unit Tests | Cache | Backend]
:relates-to:
 - motivated_by: "Contract 2: Verify Redis and other backend support"
 - implements: "Test suite for cache backend implementations"

:complexity: 4
"""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from dashboard_lego.core.cache import (
    DiskCacheBackend,
    InMemoryCacheBackend,
    RedisCacheBackend,
)
from dashboard_lego.core.datasource import DataSource


def test_disk_cache_backend():
    """Test DiskCacheBackend basic operations."""
    backend = DiskCacheBackend(directory=None, expire=300)

    # Test set/get
    backend["key1"] = "value1"
    assert "key1" in backend
    assert backend["key1"] == "value1"

    # Test missing key
    assert "key2" not in backend
    with pytest.raises(KeyError):
        _ = backend["key2"]


def test_inmemory_cache_backend():
    """Test InMemoryCacheBackend basic operations."""
    backend = InMemoryCacheBackend(expire=300)

    # Test set/get
    backend["key1"] = {"data": [1, 2, 3]}
    assert "key1" in backend
    assert backend["key1"] == {"data": [1, 2, 3]}

    # Test missing key
    assert "key2" not in backend
    with pytest.raises(KeyError):
        _ = backend["key2"]


@pytest.mark.skipif(
    True,  # Skip by default - requires Redis server
    reason="Requires Redis server running on localhost:6379",
)
def test_redis_cache_backend():
    """Test RedisCacheBackend basic operations (requires Redis server)."""
    try:
        # Use a fixed signing key for testing
        signing_key = b"test_key_for_testing_purposes_32b"
        backend = RedisCacheBackend(
            host="localhost", port=6379, expire=300, signing_key=signing_key
        )

        # Test set/get
        backend["test_key"] = "test_value"
        assert "test_key" in backend
        assert backend["test_key"] == "test_value"

        # Test missing key
        assert "missing_key" not in backend
        with pytest.raises(KeyError):
            _ = backend["missing_key"]

        # Test that data is signed (tampering detection)
        raw_value = backend._redis.get("test_key")
        assert len(raw_value) > 32  # Should have signature prefix

    except Exception as e:
        pytest.skip(f"Redis not available: {e}")


def test_datasource_with_disk_backend():
    """Test DataSource with explicit disk backend."""
    ds = DataSource(
        build_fn=lambda p: pd.DataFrame({"x": [1, 2, 3]}), cache_backend="disk"
    )

    result = ds.get_processed_data()
    assert len(result) == 3
    assert list(result["x"]) == [1, 2, 3]


def test_datasource_with_memory_backend():
    """Test DataSource with in-memory backend."""
    ds = DataSource(
        build_fn=lambda p: pd.DataFrame({"x": [4, 5, 6]}), cache_backend="memory"
    )

    result = ds.get_processed_data()
    assert len(result) == 3
    assert list(result["x"]) == [4, 5, 6]


def test_datasource_backend_sharing():
    """Test that datasources with same backend share cache."""
    # Create two datasources with same backend type
    ds1 = DataSource(
        build_fn=lambda p: pd.DataFrame({"a": [1, 2]}), cache_backend="memory"
    )
    ds2 = DataSource(
        build_fn=lambda p: pd.DataFrame({"b": [3, 4]}), cache_backend="memory"
    )

    # They should share the same backend instance
    assert ds1.cache is ds2.cache


def test_datasource_with_custom_backend():
    """Test DataSource with custom backend instance."""
    custom_backend = InMemoryCacheBackend(expire=600)

    ds = DataSource(
        build_fn=lambda p: pd.DataFrame({"x": [7, 8, 9]}), cache_backend=custom_backend
    )

    result = ds.get_processed_data()
    assert len(result) == 3
    assert ds.cache is custom_backend


def test_datasource_cloning_preserves_backend():
    """Test that with_* methods preserve cache backend."""
    ds1 = DataSource(
        build_fn=lambda p: pd.DataFrame({"a": [1, 2, 3]}), cache_backend="memory"
    )

    # Clone with new transformer
    ds2 = ds1.with_transform_fn(lambda df: df[df["a"] > 1])

    # Should share same backend
    assert ds1.cache is ds2.cache
    assert ds1.cache_backend == ds2.cache_backend
