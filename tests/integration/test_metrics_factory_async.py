"""
Tests for metrics_factory with AsyncDataSource.

:hierarchy: [Tests | Integration | MetricsFactory | Async]
"""

import asyncio

import pandas as pd
import pytest

from dashboard_lego.blocks import get_metric_row
from dashboard_lego.core.async_api import AsyncDataSource


@pytest.mark.asyncio
async def test_get_metric_row_with_async_datasource():
    """Test get_metric_row works with AsyncDataSource."""

    async def async_build(params):
        await asyncio.sleep(0.01)
        return pd.DataFrame(
            {
                "Revenue": [100, 200, 300],
                "Price": [10, 20, 30],
                "Quantity": [5, 10, 15],
            }
        )

    async_datasource = AsyncDataSource(build_fn=async_build)

    # Create metric blocks with async datasource
    metric_blocks, row_opts = get_metric_row(
        metrics_spec={
            "revenue": {
                "column": "Revenue",
                "agg": "sum",
                "title": "Total Revenue",
                "color": "success",
            },
            "price": {
                "column": "Price",
                "agg": "mean",
                "title": "Avg Price",
                "color": "info",
            },
        },
        datasource=async_datasource,
        block_id_prefix="async_metric",
    )

    # Verify blocks were created
    assert len(metric_blocks) == 2
    assert all(block.datasource == async_datasource for block in metric_blocks)
    assert row_opts["className"] == "mb-4"

    # Verify block IDs
    assert metric_blocks[0].block_id == "async_metric-revenue"
    assert metric_blocks[1].block_id == "async_metric-price"


@pytest.mark.asyncio
async def test_get_metric_row_mixed_blocks_with_async_datasource():
    """Test get_metric_row creates both numeric and text blocks with AsyncDataSource."""

    async def async_build(params):
        await asyncio.sleep(0.01)
        return pd.DataFrame(
            {
                "Sales": [100, 200, 300],
                "Status": ["Active", "Pending", "Active"],
            }
        )

    async_datasource = AsyncDataSource(build_fn=async_build)

    # Create mixed blocks (numeric + text) with async datasource
    metric_blocks, row_opts = get_metric_row(
        metrics_spec={
            "total_sales": {
                "column": "Sales",
                "agg": "sum",
                "title": "Total Sales",
                "color": "success",
            },
            "status": {
                "content_generator": lambda df: f"Status: {df['Status'].iloc[0]}",
                "title": "System Status",
                "color": "info",
            },
        },
        datasource=async_datasource,
    )

    # Verify blocks were created
    assert len(metric_blocks) == 2
    assert all(block.datasource == async_datasource for block in metric_blocks)

    # Verify block types (first is SingleMetricBlock, second is TextBlock)
    from dashboard_lego.blocks.single_metric import SingleMetricBlock
    from dashboard_lego.blocks.text import TextBlock

    assert isinstance(metric_blocks[0], SingleMetricBlock)
    assert isinstance(metric_blocks[1], TextBlock)
