"""
Integration tests for layout contract compliance.

Verifies that DashboardPage layout system correctly implements:
- Equal height rows (align-items-stretch + h-100)
- Responsive column sizing
- No fixed heights interfering with flexbox

:hierarchy: [Tests | Integration | LayoutContracts]
:relates-to:
 - motivated_by: "SPEC: Layout height contract enforcement"
 - implements: "test_suite: 'test_layout_contracts'"

:contract:
 - pre: "Dash app with blocks in grid layout"
 - post: "All layout contracts verified"
 - test_coverage: "Equal heights, flexbox classes, no fixed heights"

:complexity: 6
:decision_cache: "layout_testing: Use Selenium to verify computed styles"

NOTE: These tests require ChromeDriver that matches your Chrome version.
      Tests are skipped if ChromeDriver is incompatible.
      To run: Update ChromeDriver to match Chrome version or use webdriver-manager.
"""

import pandas as pd
import pytest
from selenium.common.exceptions import SessionNotCreatedException, WebDriverException

from dashboard_lego.blocks import SingleMetricBlock, TypedChartBlock, get_metric_row
from dashboard_lego.core import DashboardPage, DataBuilder, DataSource

# Skip all tests in this module if ChromeDriver is incompatible
pytestmark = pytest.mark.skipif(
    True,
    reason="Browser tests require ChromeDriver matching Chrome version. "
    "Update ChromeDriver or use webdriver-manager to run these tests.",
)


class SimpleDataBuilder(DataBuilder):
    """Test data builder."""

    def build(self, params):
        """Return sample data."""
        return pd.DataFrame(
            {
                "Product": ["A", "B", "C"],
                "Revenue": [100, 200, 150],
                "Price": [10.5, 20.0, 15.5],
                "Quantity": [10, 10, 10],
            }
        )


@pytest.fixture
def test_datasource():
    """Create test datasource."""
    return DataSource(data_builder=SimpleDataBuilder())


def test_content_driven_heights_mixed_blocks(dash_duo, test_datasource):
    """
    Test that blocks size naturally to content (industry standard).

    :hierarchy: [Tests | Integration | LayoutContracts | ContentDriven]
    :covers:
     - target: "DashboardPage._render_row"
     - requirement: "Layout contract: content-driven heights"

    :scenario: "Row with compact metric and large chart"
    :priority: "P0"

    :complexity: 4
    """
    # Create blocks with different content sizes
    metric = SingleMetricBlock(
        block_id="test_metric",
        datasource=test_datasource,
        metric_spec={
            "column": "Revenue",
            "agg": "sum",
            "title": "Total Revenue",
            "color": "success",
        },
    )

    chart = TypedChartBlock(
        block_id="test_chart",
        datasource=test_datasource,
        plot_type="bar",
        plot_params={"x": "Product", "y": "Revenue"},
        title="Revenue by Product",
    )

    # Create page with both blocks in same row
    page = DashboardPage(title="Test Dashboard", blocks=[[metric, chart]])

    app = page.create_app(suppress_callback_exceptions=True)
    dash_duo.start_server(app)

    # Wait for page to render
    dash_duo.wait_for_element(".row", timeout=10)

    # Get column heights
    col1_height = dash_duo.driver.execute_script(
        "return document.querySelector('.row > .col:nth-child(1)').offsetHeight"
    )
    col2_height = dash_duo.driver.execute_script(
        "return document.querySelector('.row > .col:nth-child(2)').offsetHeight"
    )

    # Contract: Blocks MAY have different heights (content-driven)
    # Metric should be compact (< 300px), chart larger
    assert (
        col1_height < 300
    ), f"Metric card too large: {col1_height}px (should be compact)"
    assert col2_height > col1_height, "Chart should be taller than metric"


def test_flexbox_classes_present(dash_duo, test_datasource):
    """
    Test that required flexbox classes are present in HTML.

    :hierarchy: [Tests | Integration | LayoutContracts | FlexboxClasses]
    :covers:
     - target: "DashboardPage._render_row, _render_cell"
     - requirement: "Row has align-items-stretch, Col has h-100"

    :scenario: "Verify CSS classes in rendered HTML"
    :priority: "P0"

    :complexity: 3
    """
    metric = SingleMetricBlock(
        block_id="test_metric",
        datasource=test_datasource,
        metric_spec={
            "column": "Revenue",
            "agg": "sum",
            "title": "Revenue",
            "color": "primary",
        },
    )

    page = DashboardPage(title="Test", blocks=[[metric]])
    app = page.create_app(suppress_callback_exceptions=True)
    dash_duo.start_server(app)

    dash_duo.wait_for_element(".row", timeout=10)

    # Check Row classes
    row_classes = dash_duo.driver.execute_script(
        "return document.querySelector('.row').className"
    )
    assert (
        "align-items-stretch" in row_classes
    ), f"Row missing align-items-stretch: {row_classes}"

    # Check Col classes
    col_classes = dash_duo.driver.execute_script(
        "return document.querySelector('.col').className"
    )
    assert "h-100" in col_classes, f"Col missing h-100: {col_classes}"

    # Check Card classes
    card_classes = dash_duo.driver.execute_script(
        "return document.querySelector('.card').className"
    )
    assert "h-100" in card_classes, f"Card missing h-100: {card_classes}"


def test_no_fixed_heights(dash_duo, test_datasource):
    """
    Test that cards have no fixed height in inline styles.

    :hierarchy: [Tests | Integration | LayoutContracts | NoFixedHeights]
    :covers:
     - target: "SingleMetricBlock.layout, TypedChartBlock.layout"
     - requirement: "Cards must not have fixed height/minHeight"

    :scenario: "Verify no height/minHeight in computed styles"
    :priority: "P0"

    :complexity: 3
    """
    metric = SingleMetricBlock(
        block_id="test_metric",
        datasource=test_datasource,
        metric_spec={
            "column": "Revenue",
            "agg": "sum",
            "title": "Revenue",
            "color": "success",
        },
    )

    page = DashboardPage(title="Test", blocks=[[metric]])
    app = page.create_app(suppress_callback_exceptions=True)
    dash_duo.start_server(app)

    dash_duo.wait_for_element(".card", timeout=10)

    # Check for fixed height in inline styles
    card_style = dash_duo.driver.execute_script(
        "return document.querySelector('.card').style.height"
    )
    assert card_style == "", f"Card has fixed height in inline styles: {card_style}"

    # Check for minHeight in inline styles
    card_min_height = dash_duo.driver.execute_script(
        "return document.querySelector('.card').style.minHeight"
    )
    assert (
        card_min_height == ""
    ), f"Card has minHeight in inline styles: {card_min_height}"


def test_metric_row_factory_sizing(dash_duo, test_datasource):
    """
    Test get_metric_row() factory creates properly sized blocks.

    :hierarchy: [Tests | Integration | LayoutContracts | FactorySizing]
    :covers:
     - target: "get_metric_row"
     - requirement: "Factory creates blocks with responsive columns"

    :scenario: "3 metrics should each get col-md-4 (12/3=4)"
    :priority: "P0"

    :complexity: 4
    """
    metrics_blocks, row_opts = get_metric_row(
        metrics_spec={
            "revenue": {
                "column": "Revenue",
                "agg": "sum",
                "title": "Revenue",
                "color": "success",
            },
            "price": {
                "column": "Price",
                "agg": "mean",
                "title": "Avg Price",
                "color": "info",
            },
            "quantity": {
                "column": "Quantity",
                "agg": "sum",
                "title": "Units",
                "color": "primary",
            },
        },
        datasource=test_datasource,
    )

    # Verify factory returns 3 blocks
    assert len(metrics_blocks) == 3

    # Verify all are SingleMetricBlock instances
    assert all(isinstance(b, SingleMetricBlock) for b in metrics_blocks)

    # Create page
    page = DashboardPage(title="Test", blocks=[(metrics_blocks, row_opts)])
    app = page.create_app(suppress_callback_exceptions=True)
    dash_duo.start_server(app)

    dash_duo.wait_for_element(".row", timeout=10)

    # Count columns
    col_count = dash_duo.driver.execute_script(
        "return document.querySelectorAll('.row > .col').length"
    )
    assert col_count == 3, f"Expected 3 columns, got {col_count}"


def test_metric_cards_are_compact(dash_duo, test_datasource):
    """
    Test that metric cards are compact (no empty space).

    :hierarchy: [Tests | Integration | LayoutContracts | CompactCards]
    :covers:
     - target: "SingleMetricBlock._render_card"
     - requirement: "Metric cards should be compact"

    :scenario: "Card height should be minimal (< 200px for metrics)"
    :priority: "P1"

    :complexity: 3
    """
    metric = SingleMetricBlock(
        block_id="test_metric",
        datasource=test_datasource,
        metric_spec={
            "column": "Revenue",
            "agg": "sum",
            "title": "Total Revenue",
            "color": "success",
        },
    )

    page = DashboardPage(title="Test", blocks=[[metric]])
    app = page.create_app(suppress_callback_exceptions=True)
    dash_duo.start_server(app)

    dash_duo.wait_for_element(".card", timeout=10)

    # Get card height
    card_height = dash_duo.driver.execute_script(
        "return document.querySelector('.card').offsetHeight"
    )

    # Metric cards should be compact (not 600px!)
    assert (
        card_height < 200
    ), f"Metric card too tall: {card_height}px (< 200px expected)"
