"""
Tests for AsyncDataTransformer.

:hierarchy: [Tests | Core | DataTransformer | Async]
"""

import asyncio

import pandas as pd
import pytest

from dashboard_lego.core.async_api import (
    AsyncChainedTransformer,
    AsyncDataFilter,
    AsyncDataTransformer,
)
from dashboard_lego.core.data_transformer import DataTransformer
from dashboard_lego.core.exceptions import DataTransformError


@pytest.mark.asyncio
async def test_async_transformer_with_async_transform():
    """Test AsyncDataTransformer with async _transform_async method."""

    class AsyncCustomTransformer(AsyncDataTransformer):
        async def _transform_async(self, data, **kwargs):
            await asyncio.sleep(0.01)
            return data[data["value"] > 2]

    df = pd.DataFrame({"value": [1, 2, 3, 4, 5]})
    transformer = AsyncCustomTransformer()
    result = await transformer.transform_async(df)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 3
    assert all(result["value"] > 2)


@pytest.mark.asyncio
async def test_async_transformer_with_sync_transform():
    """Test AsyncDataTransformer wrapping sync transformer runs in executor."""

    class SyncCustomTransformer(DataTransformer):
        def _transform(self, data, **kwargs):
            return data[data["value"] <= 2]

    df = pd.DataFrame({"value": [1, 2, 3, 4, 5]})
    sync_transformer = SyncCustomTransformer()
    transformer = AsyncDataTransformer.wrap_sync_transformer(sync_transformer)
    result = await transformer.transform_async(df)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert all(result["value"] <= 2)


@pytest.mark.asyncio
async def test_async_transformer_with_params():
    """Test AsyncDataTransformer passes params correctly."""

    class ParamTransformer(AsyncDataTransformer):
        async def _transform_async(self, data, **kwargs):
            threshold = kwargs.get("threshold", 3)
            await asyncio.sleep(0.01)
            return data[data["value"] > threshold]

    df = pd.DataFrame({"value": [1, 2, 3, 4, 5]})
    transformer = ParamTransformer()
    result = await transformer.transform_async(df, threshold=4)

    assert len(result) == 1
    assert result["value"].iloc[0] == 5


@pytest.mark.asyncio
async def test_async_transformer_error_handling():
    """Test AsyncDataTransformer error handling."""

    class FailingTransformer(AsyncDataTransformer):
        async def _transform_async(self, data, **kwargs):
            await asyncio.sleep(0.01)
            raise ValueError("Transform failed")

    df = pd.DataFrame({"value": [1, 2, 3]})
    transformer = FailingTransformer()

    with pytest.raises(ValueError, match="Transform failed"):
        await transformer.transform_async(df)


@pytest.mark.asyncio
async def test_async_transformer_returns_non_dataframe():
    """Test AsyncDataTransformer accepts non-DataFrame return (no validation)."""

    class BadTransformer(AsyncDataTransformer):
        async def _transform_async(self, data, **kwargs):
            await asyncio.sleep(0.01)
            return {"not": "a dataframe"}

    df = pd.DataFrame({"value": [1, 2, 3]})
    transformer = BadTransformer()

    # Note: Currently no validation, returns whatever _transform_async returns
    result = await transformer.transform_async(df)
    assert isinstance(result, dict)
    assert result == {"not": "a dataframe"}


@pytest.mark.asyncio
async def test_async_data_filter():
    """Test AsyncDataFilter filters DataFrame correctly."""

    df = pd.DataFrame({"category": ["A", "B", "A", "C"], "value": [1, 2, 3, 4]})
    filter_transformer = AsyncDataFilter()

    result = await filter_transformer.transform_async(df, category="A")

    assert len(result) == 2
    assert all(result["category"] == "A")
    assert list(result["value"]) == [1, 3]


@pytest.mark.asyncio
async def test_async_chained_transformer():
    """Test AsyncChainedTransformer applies transformers sequentially."""

    class FilterTransformer(AsyncDataTransformer):
        async def _transform_async(self, data, **kwargs):
            await asyncio.sleep(0.01)
            return data[data["value"] > 2]

    class MultiplyTransformer(AsyncDataTransformer):
        async def _transform_async(self, data, **kwargs):
            await asyncio.sleep(0.01)
            data = data.copy()
            data["value"] = data["value"] * 2
            return data

    df = pd.DataFrame({"value": [1, 2, 3, 4, 5]})
    chain = AsyncChainedTransformer(
        transformer_1=FilterTransformer(),
        transformer_2=MultiplyTransformer(),
    )

    result = await chain.transform_async(df)

    assert len(result) == 3
    assert list(result["value"]) == [6, 8, 10]  # [3, 4, 5] * 2


@pytest.mark.asyncio
async def test_async_transformer_state_reset():
    """Test AsyncDataTransformer resets mutable state before transform."""

    call_count = 0

    class StatefulTransformer(AsyncDataTransformer):
        def __init__(self):
            super().__init__()
            self._state = 0

        async def _transform_async(self, data, **kwargs):
            nonlocal call_count
            call_count += 1
            self._state += 1
            await asyncio.sleep(0.01)
            data = data.copy()
            data["call"] = call_count
            data["state"] = self._state
            return data

    df = pd.DataFrame({"value": [1, 2, 3]})
    transformer = StatefulTransformer()

    result1 = await transformer.transform_async(df)
    result2 = await transformer.transform_async(df)

    # State should be reset between calls
    assert call_count == 2
    assert result1["call"].iloc[0] == 1
    assert result2["call"].iloc[0] == 2
