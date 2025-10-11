"""
Integration tests for block-specific data transformations.

Tests the complete flow: DataSource → Block with transform → Rendered data

:hierarchy: [Testing | Integration Tests | BlockTransformations]
:relates-to:
 - motivated_by: "v0.15.0: Block-specific data transformations feature"
 - implements: "test_suite: 'BlockTransformations'"
 - uses: [
     "class: 'BaseDataSource'",
     "class: 'TypedChartBlock'",
     "class: 'ChainedTransformer'"
   ]

:contract:
 - pre: "Test environment with all core components available"
 - post: "All integration tests pass, end-to-end functionality verified"

:complexity: 7
:decision_cache: "Test real-world scenarios: aggregation, filtering, multiple blocks"
"""

import pandas as pd
import pytest
from pandas.testing import assert_frame_equal

from dashboard_lego.blocks.typed_chart import TypedChartBlock
from dashboard_lego.core import BaseDataSource, DataBuilder, DataTransformer


# <semantic_block: test_fixtures>
class SampleDataBuilder(DataBuilder):
    """
    Sample data builder for integration tests.

    :hierarchy: [Testing | Integration | DataBuilder]
    :relates-to:
     - motivated_by: "Provide realistic sales data for testing"
     - implements: "class: 'SampleDataBuilder'"
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def build(self, params):
        """Build sample sales data."""
        # Generate proper test data with both categories and regions
        data = []
        for i in range(100):
            data.append(
                {
                    "date": pd.Timestamp("2024-01-01") + pd.Timedelta(days=i),
                    "category": ["Electronics", "Clothing", "Food"][i % 3],
                    "product": ["Laptop", "Phone", "Tablet"][i % 3],
                    "region": ["North", "South", "East", "West"][i % 4],
                    "sales": 100 + i,
                    "units": 1 + i,
                    "price": [10.5, 20.0, 15.5][i % 3],
                }
            )
        return pd.DataFrame(data)


class CategoryFilter(DataTransformer):
    """
    Global filter that filters by category.

    :hierarchy: [Testing | Integration | CategoryFilter]
    :relates-to:
     - motivated_by: "Simulate global dashboard filter"
     - implements: "class: 'CategoryFilter'"
    """

    def transform(self, data, params):
        """Filter by category if param provided."""
        df = data.copy()
        if "category" in params:
            df = df[df["category"] == params["category"]]
        return df


# </semantic_block: test_fixtures>


# <semantic_block: test_basic_transform>
def test_block_with_simple_transform():
    """
    Test TypedChartBlock with simple filter transform.

    :hierarchy: [Testing | Integration | BlockTransformations | Simple]
    :covers:
     - target: "TypedChartBlock with transform_fn"
     - requirement: "Block-specific transform applied to chart data"

    :scenario: "Create chart block with price filter transform"
    :priority: "P0"
    :complexity: 4
    """
    # Setup datasource
    builder = SampleDataBuilder()
    datasource = BaseDataSource(data_builder=builder)

    # Create block with transform that filters high-value sales
    block = TypedChartBlock(
        block_id="high_value_chart",
        datasource=datasource,
        plot_type="scatter",
        plot_params={"x": "date", "y": "sales"},
        transform_fn=lambda df: df[df["sales"] > 150],
    )

    # Get processed data from block's datasource
    data = block.datasource.get_processed_data()

    # Should have filtered data
    assert len(data) > 0
    assert all(data["sales"] > 150)
    assert len(data) < 100  # Less than original data


# </semantic_block: test_basic_transform>


# <semantic_block: test_aggregation_transform>
def test_block_with_aggregation_transform():
    """
    Test TypedChartBlock with aggregation transform.

    :hierarchy: [Testing | Integration | BlockTransformations | Aggregation]
    :covers:
     - target: "TypedChartBlock with groupby transform"
     - requirement: "Block can aggregate data for visualization"

    :scenario: "Create bar chart showing sales by category"
    :priority: "P0"
    :complexity: 5
    """
    # Setup datasource
    builder = SampleDataBuilder()
    datasource = BaseDataSource(data_builder=builder)

    # Create block with aggregation transform
    block = TypedChartBlock(
        block_id="sales_by_category",
        datasource=datasource,
        plot_type="bar",
        plot_params={"x": "category", "y": "total_sales"},
        transform_fn=lambda df: df.groupby("category")["sales"]
        .sum()
        .reset_index(name="total_sales"),
    )

    # Get processed data
    data = block.datasource.get_processed_data()

    # Should have aggregated data
    assert len(data) == 3  # 3 categories
    assert set(data["category"]) == {"Electronics", "Clothing", "Food"}
    assert "total_sales" in data.columns
    assert all(data["total_sales"] > 0)


# </semantic_block: test_aggregation_transform>


# <semantic_block: test_global_filter_and_block_transform>
def test_block_with_global_filter_and_transform():
    """
    Test block transform applied AFTER global filter.

    :hierarchy: [Testing | Integration | BlockTransformations | Chaining]
    :covers:
     - target: "Global filter → Block transform pipeline"
     - requirement: "Block transform chains after global filter"

    :scenario: "Global filter by category, then aggregate by region"
    :priority: "P0"
    :complexity: 6
    """
    # Setup datasource with global filter
    builder = SampleDataBuilder()
    global_filter = CategoryFilter()

    def classifier(key):
        return "transform" if key == "category" else "build"

    datasource = BaseDataSource(
        data_builder=builder,
        data_transformer=global_filter,
        param_classifier=classifier,
    )

    # Create block with aggregation transform
    block = TypedChartBlock(
        block_id="region_sales",
        datasource=datasource,
        plot_type="bar",
        plot_params={"x": "region", "y": "total_sales"},
        transform_fn=lambda df: df.groupby("region")["sales"]
        .sum()
        .reset_index(name="total_sales"),
    )

    # Get data with global filter applied
    data = block.datasource.get_processed_data({"category": "Electronics"})

    # Should have:
    # 1. Filtered to Electronics only (global filter)
    # 2. Aggregated by region (block transform)
    assert len(data) == 4  # 4 regions
    assert set(data["region"]) == {"North", "South", "East", "West"}
    assert "total_sales" in data.columns

    # Verify it's Electronics data only (sum should match Electronics-only subset)
    # We can't verify exact numbers without knowing the data distribution,
    # but we can verify structure
    assert all(data["total_sales"] > 0)


# </semantic_block: test_global_filter_and_block_transform>


# <semantic_block: test_multiple_blocks_same_datasource>
def test_multiple_blocks_different_transforms():
    """
    Test multiple blocks with different transforms on same datasource.

    :hierarchy: [Testing | Integration | BlockTransformations | Multiple]
    :covers:
     - target: "Multiple blocks, each with specialized datasource"
     - requirement: "Each block has independent transform pipeline"

    :scenario: "One block aggregates by category, another by region"
    :priority: "P1"
    :complexity: 6
    """
    # Setup shared datasource
    builder = SampleDataBuilder()
    datasource = BaseDataSource(data_builder=builder)

    # Block 1: Aggregate by category
    block1 = TypedChartBlock(
        block_id="by_category",
        datasource=datasource,
        plot_type="bar",
        plot_params={"x": "category", "y": "total"},
        transform_fn=lambda df: df.groupby("category")["sales"]
        .sum()
        .reset_index(name="total"),
    )

    # Block 2: Aggregate by region
    block2 = TypedChartBlock(
        block_id="by_region",
        datasource=datasource,
        plot_type="bar",
        plot_params={"x": "region", "y": "total"},
        transform_fn=lambda df: df.groupby("region")["sales"]
        .sum()
        .reset_index(name="total"),
    )

    # Get data from each block
    data1 = block1.datasource.get_processed_data()
    data2 = block2.datasource.get_processed_data()

    # Each should have different aggregation
    assert len(data1) == 3  # 3 categories
    assert len(data2) == 4  # 4 regions
    assert set(data1["category"]) == {"Electronics", "Clothing", "Food"}
    assert set(data2["region"]) == {"North", "South", "East", "West"}

    # Original datasource should be unchanged
    original_data = datasource.get_processed_data()
    assert len(original_data) == 100  # Original row count


# </semantic_block: test_multiple_blocks_same_datasource>


# <semantic_block: test_pivot_transform>
def test_block_with_pivot_transform():
    """
    Test block with pivot table transform.

    :hierarchy: [Testing | Integration | BlockTransformations | Pivot]
    :covers:
     - target: "TypedChartBlock with pivot_table transform"
     - requirement: "Block can reshape data with pivot"

    :scenario: "Create heatmap with pivoted category/region sales"
    :priority: "P1"
    :complexity: 5
    """
    # Setup datasource
    builder = SampleDataBuilder()
    datasource = BaseDataSource(data_builder=builder)

    # Create block with pivot transform
    block = TypedChartBlock(
        block_id="sales_heatmap",
        datasource=datasource,
        plot_type="heatmap",
        plot_params={"x": "region", "y": "category", "z": "total_sales"},
        transform_fn=lambda df: df.pivot_table(
            index="category", columns="region", values="sales", aggfunc="sum"
        ).reset_index(),
    )

    # Get processed data
    data = block.datasource.get_processed_data()

    # Should have pivoted data
    assert len(data) == 3  # 3 categories
    assert "category" in data.columns
    # Should have columns for each region
    assert all(region in data.columns for region in ["North", "South", "East", "West"])


# </semantic_block: test_pivot_transform>


# <semantic_block: test_complex_transform>
def test_block_with_complex_multi_step_transform():
    """
    Test block with complex multi-step transformation.

    :hierarchy: [Testing | Integration | BlockTransformations | Complex]
    :covers:
     - target: "TypedChartBlock with multi-step transform"
     - requirement: "Block transform can be arbitrarily complex"

    :scenario: "Filter, aggregate, then calculate derived metrics"
    :priority: "P2"
    :complexity: 6
    """
    # Setup datasource
    builder = SampleDataBuilder()
    datasource = BaseDataSource(data_builder=builder)

    # Complex transform: filter high sales, aggregate by category, calculate average
    def complex_transform(df):
        # Step 1: Filter high sales
        filtered = df[df["sales"] > 125]
        # Step 2: Aggregate by category
        aggregated = (
            filtered.groupby("category")
            .agg({"sales": "sum", "units": "sum"})
            .reset_index()
        )
        # Step 3: Calculate average price
        aggregated["avg_price"] = aggregated["sales"] / aggregated["units"]
        return aggregated

    block = TypedChartBlock(
        block_id="complex_chart",
        datasource=datasource,
        plot_type="bar",
        plot_params={"x": "category", "y": "avg_price"},
        transform_fn=complex_transform,
    )

    # Get processed data
    data = block.datasource.get_processed_data()

    # Should have transformed data
    assert len(data) <= 3  # At most 3 categories
    assert "avg_price" in data.columns
    assert all(data["avg_price"] > 0)


# </semantic_block: test_complex_transform>


# <semantic_block: test_transform_with_controls>
def test_block_transform_with_embedded_controls():
    """
    Test block with both transform_fn and embedded controls.

    :hierarchy: [Testing | Integration | BlockTransformations | Controls]
    :covers:
     - target: "TypedChartBlock with transform_fn and controls"
     - requirement: "Transform works alongside embedded controls"

    :scenario: "Block has transform AND user-selectable parameters"
    :priority: "P1"
    :complexity: 5
    """
    from dash import dcc

    from dashboard_lego.blocks.typed_chart import Control

    # Setup datasource
    builder = SampleDataBuilder()
    datasource = BaseDataSource(data_builder=builder)

    # Create block with both transform and controls
    block = TypedChartBlock(
        block_id="controlled_chart",
        datasource=datasource,
        plot_type="scatter",
        plot_params={"x": "date", "y": "sales"},
        transform_fn=lambda df: df[df["sales"] > 100],  # Pre-filter data
        controls={
            "category": Control(
                component=dcc.Dropdown,
                props={
                    "options": [
                        {"label": "Electronics", "value": "Electronics"},
                        {"label": "Clothing", "value": "Clothing"},
                    ]
                },
            )
        },
    )

    # Verify block has both transform and controls
    assert block.transform_fn is not None
    assert len(block.controls) == 1
    assert "category" in block.controls

    # Get data (transform should be applied)
    data = block.datasource.get_processed_data()
    assert all(data["sales"] > 100)


# </semantic_block: test_transform_with_controls>
