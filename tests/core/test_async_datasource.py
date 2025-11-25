"""
Tests for async DataSource support.

:hierarchy: [Tests | Core | DataSource | Async]
"""

import asyncio

import pandas as pd
import pytest

from dashboard_lego.core.async_datasource import AsyncDataSource
from dashboard_lego.core.exceptions import DataLoadError


@pytest.mark.asyncio
async def test_async_build_fn():
    """Test async build_fn is awaited properly."""

    async def async_fetch(params):
        await asyncio.sleep(0.01)  # Simulate async I/O
        return pd.DataFrame({"x": [1, 2, 3]})

    ds = AsyncDataSource(build_fn=async_fetch)
    result = await ds.get_processed_data_async()

    assert len(result) == 3
    assert "x" in result.columns
    assert list(result["x"]) == [1, 2, 3]


@pytest.mark.asyncio
async def test_sync_build_fn_in_async_context():
    """Test sync build_fn works in async context via executor."""

    def sync_fetch(params):
        return pd.DataFrame({"y": [4, 5, 6]})

    ds = AsyncDataSource(build_fn=sync_fetch)
    result = await ds.get_processed_data_async()

    assert len(result) == 3
    assert "y" in result.columns
    assert list(result["y"]) == [4, 5, 6]


@pytest.mark.asyncio
async def test_async_with_params():
    """Test params passed to async build_fn."""

    async def build_with_params(params):
        rows = params.get("rows", 5)
        await asyncio.sleep(0.01)
        return pd.DataFrame({"val": range(rows)})

    ds = AsyncDataSource(build_fn=build_with_params)
    result = await ds.get_processed_data_async({"rows": 10})

    assert len(result) == 10
    assert "val" in result.columns


@pytest.mark.asyncio
async def test_async_with_transform_fn():
    """Test async build_fn with sync transform_fn."""

    async def async_build(params):
        await asyncio.sleep(0.01)
        return pd.DataFrame({"value": [1, 2, 3, 4, 5]})

    def sync_transform(df):
        return df[df["value"] > 2]

    ds = AsyncDataSource(build_fn=async_build, transform_fn=sync_transform)
    result = await ds.get_processed_data_async()

    assert len(result) == 3
    assert list(result["value"]) == [3, 4, 5]


@pytest.mark.asyncio
async def test_async_caching():
    """Test that async operations use cache correctly."""
    call_count = 0

    async def async_build(params):
        nonlocal call_count
        call_count += 1
        await asyncio.sleep(0.01)
        return pd.DataFrame({"x": [1, 2, 3]})

    ds = AsyncDataSource(build_fn=async_build, cache_ttl=60)

    # First call - cache miss
    result1 = await ds.get_processed_data_async()
    assert call_count == 1

    # Second call - cache hit
    result2 = await ds.get_processed_data_async()
    assert call_count == 1  # Should not increment

    # Results should be identical
    pd.testing.assert_frame_equal(result1, result2)


@pytest.mark.asyncio
async def test_async_error_handling():
    """Test error handling in async context."""

    async def failing_build(params):
        await asyncio.sleep(0.01)
        raise ValueError("Simulated async error")

    ds = AsyncDataSource(build_fn=failing_build)

    with pytest.raises(DataLoadError, match="Async data processing failed"):
        await ds.get_processed_data_async()


@pytest.mark.asyncio
async def test_async_concurrent_calls():
    """Test multiple concurrent async calls work correctly."""

    async def async_build(params):
        await asyncio.sleep(0.01)
        multiplier = params.get("multiplier", 1)
        return pd.DataFrame({"value": [i * multiplier for i in range(5)]})

    ds = AsyncDataSource(build_fn=async_build)

    # Make concurrent calls with different params
    results = await asyncio.gather(
        ds.get_processed_data_async({"multiplier": 1}),
        ds.get_processed_data_async({"multiplier": 2}),
        ds.get_processed_data_async({"multiplier": 3}),
    )

    assert len(results) == 3
    assert list(results[0]["value"]) == [0, 1, 2, 3, 4]
    assert list(results[1]["value"]) == [0, 2, 4, 6, 8]
    assert list(results[2]["value"]) == [0, 3, 6, 9, 12]


@pytest.mark.asyncio
async def test_async_with_empty_params():
    """Test async call with no params."""

    async def async_build(params):
        await asyncio.sleep(0.01)
        return pd.DataFrame({"default": [1, 2, 3]})

    ds = AsyncDataSource(build_fn=async_build)
    result = await ds.get_processed_data_async()

    assert len(result) == 3
    assert "default" in result.columns
