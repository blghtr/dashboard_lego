"""
Unit tests for the KPIBlock class.

"""
import pytest
import dash_bootstrap_components as dbc
from dash import html, dcc

from blocks.kpi import KPIBlock

@pytest.fixture
def kpi_definitions():
    return [
        {
            "key": "total_sales",
            "title": "Total Sales",
            "color": "success"
        },
        {
            "key": "avg_order_value",
            "title": "Average Order Value"
        },
        {
            "key": "status",
            "title": "Status"
        }
    ]

def test_kpi_block_layout(datasource_factory):
    """
    Tests that the initial layout of the KPIBlock is a Loading component.

    """
    mock_ds = datasource_factory()
    block = KPIBlock(block_id="test_kpi", datasource=mock_ds, kpi_definitions=[], subscribes_to="some_state")
    layout = block.layout()
    assert isinstance(layout, dcc.Loading)
    assert layout.children.id == "test_kpi-container"

def test_update_kpi_cards_success(datasource_factory, kpi_definitions):
    """
    Tests the successful generation of KPI cards with correct formatting.

    """
    mock_data = {
        "total_sales": 1234567,
        "avg_order_value": 123.456,
        "status": "Active"
    }
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
    assert "bg-primary" in row.children[1].children.className # Default color

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
    Tests the behavior when the datasource raises an exception.

    """
    mock_ds = datasource_factory()
    # Make the mock method raise an error
    mock_ds.get_kpis.side_effect = ValueError("DB connection failed")
    block = KPIBlock("sales_kpis", mock_ds, kpi_definitions, "filters_changed")

    alert = block._update_kpi_cards()
    assert isinstance(alert, dbc.Alert)
    assert alert.color == "danger"
    assert "Ошибка загрузки KPI: DB connection failed" in alert.children
