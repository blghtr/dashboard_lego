"""
Unit tests for the KPIBlock class.

"""

import dash_bootstrap_components as dbc
import pytest
from dash import dcc, html

from dashboard_lego.blocks.kpi import KPIBlock


@pytest.fixture
def kpi_definitions():
    return [
        {"key": "total_sales", "title": "Total Sales", "color": "success"},
        {"key": "avg_order_value", "title": "Average Order Value"},
        {"key": "status", "title": "Status"},
    ]


def test_kpi_block_layout(datasource_factory):
    """
    Tests that the initial layout of the KPIBlock is a Loading component.

    """
    mock_ds = datasource_factory()
    block = KPIBlock(
        block_id="test_kpi",
        datasource=mock_ds,
        kpi_definitions=[],
        subscribes_to="some_state",
    )
    layout = block.layout()
    assert isinstance(layout, dcc.Loading)
    assert layout.children.id == "test_kpi-container"


def test_update_kpi_cards_success(datasource_factory, kpi_definitions):
    """
    Tests the successful generation of KPI cards with correct formatting.

    """
    mock_data = {"total_sales": 1234567, "avg_order_value": 123.456, "status": "Active"}
    mock_ds = datasource_factory(get_kpis=mock_data)
    block = KPIBlock("sales_kpis", mock_ds, kpi_definitions, "filters_changed")

    # Call the internal update method
    row = block._update_kpi_cards()

    assert isinstance(row, dbc.Row)
    assert len(row.children) == 3

    # Test formatting and content
    card1_body = row.children[0].children.children
    assert card1_body.children[0].children == "1,234,567"  # Integer formatting
    assert card1_body.children[1].children == "Total Sales"
    assert "bg-success" in row.children[0].children.className

    card2_body = row.children[1].children.children
    assert card2_body.children[0].children == "123.46"  # Float formatting (default .2f)
    assert card2_body.children[1].children == "Average Order Value"
    assert "bg-primary" in row.children[1].children.className  # Default color

    card3_body = row.children[2].children.children
    assert card3_body.children[0].children == "Active"  # String formatting
    assert card3_body.children[1].children == "Status"


def test_update_kpi_cards_no_data(datasource_factory, kpi_definitions):
    """
    Tests the behavior when the datasource returns no KPI data.

    """
    mock_ds = datasource_factory(get_kpis={})
    block = KPIBlock("sales_kpis", mock_ds, kpi_definitions, "filters_changed")

    alert = block._update_kpi_cards()
    assert isinstance(alert, dbc.Alert)
    assert alert.children == "Нет данных для KPI."


def test_update_kpi_cards_error(datasource_factory, kpi_definitions):
    """
    Tests the behavior when the datasource raises an exception (v0.15.0).
    In v0.15.0, errors come from get_processed_data() not get_kpis().
    """
    mock_ds = datasource_factory()
    # Make get_processed_data raise an error
    mock_ds.get_processed_data.side_effect = ValueError("DB connection failed")
    block = KPIBlock("sales_kpis", mock_ds, kpi_definitions, "filters_changed")

    alert = block._update_kpi_cards()
    assert isinstance(alert, dbc.Alert)
    assert alert.color == "danger"
    # Error message should contain the exception
    assert "Error" in str(alert.children) or "Ошибка" in str(alert.children)


def test_kpi_block_list_subscription(datasource_factory, kpi_definitions):
    """
    Tests that KPIBlock can subscribe to multiple states.

    :hierarchy: [Testing | Unit Tests | Blocks | KPIBlock | Multi-State]
    :covers:
     - object: "KPIBlock with list subscription"
     - requirement: "Bug Fix: Support subscribing to multiple states"

    :scenario: "Verifies that KPIBlock can subscribe to multiple states
     using a list parameter without causing TypeError."
    :strategy: "Create KPIBlock with list subscription and verify
     subscribes dict is created correctly."
    :contract:
     - pre: "subscribes_to accepts both str and List[str] types."
     - post: "Block subscribes to all specified states successfully."

    """
    mock_ds = datasource_factory()
    state_ids = ["filter-state-1", "filter-state-2"]

    # This should not raise TypeError: unhashable type: 'list'
    block = KPIBlock(
        block_id="test_kpi",
        datasource=mock_ds,
        kpi_definitions=kpi_definitions,
        subscribes_to=state_ids,
    )

    # Verify subscribes dict was created correctly
    assert block.subscribes is not None
    assert len(block.subscribes) == 2
    for state_id in state_ids:
        assert state_id in block.subscribes
        assert block.subscribes[state_id] == block._update_kpi_cards


def test_kpi_block_single_string_subscription(datasource_factory, kpi_definitions):
    """
    Tests that KPIBlock still works with single string (regression).

    :hierarchy: [Testing | Unit Tests | Blocks | KPIBlock | Single State]
    :covers:
     - object: "KPIBlock with string subscription"
     - requirement: "Regression test: Single string subscription must still work"

    :scenario: "Verifies that KPIBlock continues to work with single string
     state ID."
    :strategy: "Create KPIBlock with string subscription and verify it works."
    :contract:
     - pre: "subscribes_to is a single string state ID."
     - post: "Block subscribes to the state successfully."

    """
    mock_ds = datasource_factory()

    block = KPIBlock(
        block_id="test_kpi",
        datasource=mock_ds,
        kpi_definitions=kpi_definitions,
        subscribes_to="single-state",
    )

    # Verify subscribes dict was created correctly
    assert block.subscribes is not None
    assert len(block.subscribes) == 1
    assert "single-state" in block.subscribes
