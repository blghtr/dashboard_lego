"""
Tests for AsyncLambdaBuilder and AsyncLambdaTransformer.

:hierarchy: [Tests | Core | LambdaHandlers | Async]
"""

import asyncio

import pandas as pd
import pytest

from dashboard_lego.core.async_api import AsyncLambdaBuilder, AsyncLambdaTransformer


@pytest.mark.asyncio
async def test_async_lambda_builder_async_func():
    """Test AsyncLambdaBuilder with async function."""

    async def async_build(params):
        await asyncio.sleep(0.01)
        rows = params.get("rows", 3)
        return pd.DataFrame({"x": range(rows)})

    builder = AsyncLambdaBuilder(async_build)
    result = await builder.build_async(rows=5)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 5
    assert "x" in result.columns


@pytest.mark.asyncio
async def test_async_lambda_builder_sync_func():
    """Test AsyncLambdaBuilder with sync function runs in executor."""

    def sync_build(params):
        rows = params.get("rows", 3)
        return pd.DataFrame({"y": range(rows)})

    builder = AsyncLambdaBuilder(sync_build)
    result = await builder.build_async(rows=4)

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 4
    assert "y" in result.columns


@pytest.mark.asyncio
async def test_async_lambda_transformer_async_func():
    """Test AsyncLambdaTransformer with async function."""

    async def async_transform(df):
        await asyncio.sleep(0.01)
        return df[df["value"] > 2]

    df = pd.DataFrame({"value": [1, 2, 3, 4, 5]})
    transformer = AsyncLambdaTransformer(async_transform)
    result = await transformer.transform_async(df)

    assert len(result) == 3
    assert all(result["value"] > 2)


@pytest.mark.asyncio
async def test_async_lambda_transformer_sync_func():
    """Test AsyncLambdaTransformer with sync function runs in executor."""

    def sync_transform(df):
        return df[df["value"] <= 2]

    df = pd.DataFrame({"value": [1, 2, 3, 4, 5]})
    transformer = AsyncLambdaTransformer(sync_transform)
    result = await transformer.transform_async(df)

    assert len(result) == 2
    assert all(result["value"] <= 2)


@pytest.mark.asyncio
async def test_async_lambda_transformer_with_kwargs():
    """Test AsyncLambdaTransformer with function that accepts kwargs."""

    async def transform_with_kwargs(df, threshold=3):
        await asyncio.sleep(0.01)
        return df[df["value"] > threshold]

    df = pd.DataFrame({"value": [1, 2, 3, 4, 5]})
    transformer = AsyncLambdaTransformer(transform_with_kwargs)
    result = await transformer.transform_async(df, threshold=4)

    assert len(result) == 1
    assert result["value"].iloc[0] == 5


@pytest.mark.asyncio
async def test_async_lambda_builder_function_hash():
    """Test AsyncLambdaBuilder computes function hash for cache stability."""

    async def build_func(params):
        return pd.DataFrame({"x": [1, 2, 3]})

    builder = AsyncLambdaBuilder(build_func)
    hash1 = builder.get_function_hash()

    # Same function should produce same hash
    builder2 = AsyncLambdaBuilder(build_func)
    hash2 = builder2.get_function_hash()

    assert hash1 == hash2
    assert hash1 is not None


@pytest.mark.asyncio
async def test_async_lambda_transformer_function_hash():
    """Test AsyncLambdaTransformer computes function hash for cache stability."""

    async def transform_func(df):
        return df

    transformer = AsyncLambdaTransformer(transform_func)
    hash1 = transformer.get_function_hash()

    # Same function should produce same hash
    transformer2 = AsyncLambdaTransformer(transform_func)
    hash2 = transformer2.get_function_hash()

    assert hash1 == hash2
    assert hash1 is not None
