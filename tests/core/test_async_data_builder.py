"""
Tests for AsyncDataBuilder.

:hierarchy: [Tests | Core | DataBuilder | Async]
"""

import asyncio

import pandas as pd
import pytest

from dashboard_lego.core.async_api import AsyncDataBuilder, AsyncDfHandler
from dashboard_lego.core.data_builder import DataBuilder
from dashboard_lego.core.exceptions import DataLoadError


@pytest.mark.asyncio
async def test_async_builder_with_async_build():
    """Test AsyncDataBuilder with async _build_async method."""

    class AsyncCustomBuilder(AsyncDataBuilder):
        async def _build_async(self, **kwargs):
            await asyncio.sleep(0.01)
            return pd.DataFrame({"x": [1, 2, 3]})

    builder = AsyncCustomBuilder()
    result = await builder.build_async()

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert "x" in result.columns


@pytest.mark.asyncio
async def test_async_builder_with_sync_build():
    """Test AsyncDataBuilder wrapping sync builder runs in executor."""

    class SyncCustomBuilder(DataBuilder):
        def _build(self, **kwargs):
            return pd.DataFrame({"y": [4, 5, 6]})

    sync_builder = SyncCustomBuilder()
    builder = AsyncDataBuilder.wrap_sync_builder(sync_builder)
    result = await builder.build_async()

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert "y" in result.columns


@pytest.mark.asyncio
async def test_async_builder_with_params():
    """Test AsyncDataBuilder passes params correctly."""

    class ParamBuilder(AsyncDataBuilder):
        async def _build_async(self, **kwargs):
            rows = kwargs.get("rows", 5)
            await asyncio.sleep(0.01)
            return pd.DataFrame({"val": range(rows)})

    builder = ParamBuilder()
    result = await builder.build_async(rows=10)

    assert len(result) == 10
    assert "val" in result.columns


@pytest.mark.asyncio
async def test_async_builder_error_handling():
    """Test AsyncDataBuilder error handling."""

    class FailingBuilder(AsyncDataBuilder):
        async def _build_async(self, **kwargs):
            await asyncio.sleep(0.01)
            raise ValueError("Build failed")

    builder = FailingBuilder()

    with pytest.raises(ValueError, match="Build failed"):
        await builder.build_async()


@pytest.mark.asyncio
async def test_async_builder_returns_non_dataframe():
    """Test AsyncDataBuilder accepts non-DataFrame return (no validation)."""

    class BadBuilder(AsyncDataBuilder):
        async def _build_async(self, **kwargs):
            await asyncio.sleep(0.01)
            return {"not": "a dataframe"}

    builder = BadBuilder()

    # Note: Currently no validation, returns whatever _build_async returns
    result = await builder.build_async()
    assert isinstance(result, dict)
    assert result == {"not": "a dataframe"}


@pytest.mark.asyncio
async def test_async_df_handler():
    """Test AsyncDfHandler filters DataFrame correctly."""

    df = pd.DataFrame({"category": ["A", "B", "A", "C"], "value": [1, 2, 3, 4]})
    handler = AsyncDfHandler(df)

    # Filter by category
    result = await handler.build_async(category="A")

    assert len(result) == 2
    assert all(result["category"] == "A")
    assert list(result["value"]) == [1, 3]


@pytest.mark.asyncio
async def test_async_df_handler_empty_df():
    """Test AsyncDfHandler handles empty DataFrame."""

    df = pd.DataFrame()
    handler = AsyncDfHandler(df)
    result = await handler.build_async()

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 0


@pytest.mark.asyncio
async def test_async_builder_state_reset():
    """Test AsyncDataBuilder resets mutable state before build."""

    call_count = 0

    class StatefulBuilder(AsyncDataBuilder):
        def __init__(self):
            super().__init__()
            self._state = 0

        async def _build_async(self, **kwargs):
            nonlocal call_count
            call_count += 1
            self._state += 1
            await asyncio.sleep(0.01)
            return pd.DataFrame({"count": [call_count, self._state]})

    builder = StatefulBuilder()

    result1 = await builder.build_async()
    result2 = await builder.build_async()

    # State should be reset between calls
    assert call_count == 2
    assert result1["count"].iloc[0] == 1
    assert result2["count"].iloc[0] == 2
