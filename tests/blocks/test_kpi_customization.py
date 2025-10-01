"""
Tests for KPIBlock customization parameters.

:hierarchy: [Tests | Blocks | KPIBlock | Customization]
:covers:
 - object: "class: KPIBlock"
 - requirement: "PRD: Need customizable styling for KPI blocks"

:scenario: "Verifies that KPIBlock correctly applies all style customization
 parameters to its components including individual KPI cards."
:strategy: "Uses pytest to create block instances and verify component
 attributes match expected styling parameters."
:contract:
 - pre: "KPIBlock is initialized with style parameters."
 - post: "All style parameters are correctly applied to rendered components."

"""

from unittest.mock import MagicMock, Mock

import dash_bootstrap_components as dbc
import pytest
from dash import html

from dashboard_lego.blocks.kpi import KPIBlock, _create_kpi_card
from dashboard_lego.core.datasource import BaseDataSource


class TestKPIBlockCustomization:
    """Test suite for KPIBlock style customization."""

    @pytest.fixture
    def mock_datasource(self):
        """Create a mock datasource for testing."""
        datasource = Mock(spec=BaseDataSource)
        datasource.get_kpis.return_value = {
            "total_sales": 100000,
            "total_orders": 500,
            "avg_order_value": 200,
        }
        return datasource

    @pytest.fixture
    def sample_kpi_definitions(self):
        """Create sample KPI definitions for testing."""
        return [
            {"key": "total_sales", "title": "Total Sales", "color": "primary"},
            {"key": "total_orders", "title": "Total Orders", "color": "success"},
            {"key": "avg_order_value", "title": "Avg Order Value", "color": "info"},
        ]

    def test_kpi_block_default_styling(self, mock_datasource, sample_kpi_definitions):
        """
        Test that KPIBlock uses default styling when no custom parameters
        are provided.

        :hierarchy: [Tests | Blocks | KPIBlock | Default Styling]
        :covers:
         - object: "method: KPIBlock.layout"
         - requirement: "Backward compatibility: default styling preserved"

        :scenario: "Verifies that default className and styling are applied
         when no customization parameters are provided."
        :strategy: "Creates block without style parameters and checks default
         component attributes."
        :contract:
         - pre: "KPIBlock is created without style parameters."
         - post: "Default styling is applied to all components."

        """
        block = KPIBlock(
            block_id="test_kpi",
            datasource=mock_datasource,
            kpi_definitions=sample_kpi_definitions,
            subscribes_to="test_state",
        )

        layout = block.layout()

        # Check that it's a Loading component
        assert layout.type == "default"

        # Check container div
        container = layout.children
        assert isinstance(container, html.Div)

        # Check initial content (should be a Row of KPI cards)
        initial_content = block._update_kpi_cards()
        assert isinstance(initial_content, dbc.Row)

    def test_kpi_block_custom_container_styling(
        self, mock_datasource, sample_kpi_definitions
    ):
        """
        Test that KPIBlock applies custom container styling.

        :hierarchy: [Tests | Blocks | KPIBlock | Container Styling]
        :covers:
         - object: "parameter: container_style, container_className, loading_type"
         - requirement: "PRD: Need customizable container styling"

        :scenario: "Verifies that custom container style and className are
         applied correctly."
        :strategy: "Creates block with custom container parameters and verifies
         component attributes."
        :contract:
         - pre: "KPIBlock is created with custom container styling."
         - post: "Custom container styling is applied to container component."

        """
        custom_style = {"backgroundColor": "#f8f9fa", "padding": "20px"}
        custom_class = "custom-kpi-container"
        custom_loading = "circle"

        block = KPIBlock(
            block_id="test_kpi",
            datasource=mock_datasource,
            kpi_definitions=sample_kpi_definitions,
            subscribes_to="test_state",
            container_style=custom_style,
            container_className=custom_class,
            loading_type=custom_loading,
        )

        layout = block.layout()

        # Check custom loading type
        assert layout.type == custom_loading

        # Check custom container styling
        container = layout.children
        assert container.className == custom_class
        assert container.style == custom_style

    def test_kpi_card_custom_styling(self):
        """
        Test that _create_kpi_card applies custom styling parameters.

        :hierarchy: [Tests | Blocks | KPIBlock | Card Styling]
        :covers:
         - object: "function: _create_kpi_card"
         - requirement: "PRD: Need customizable KPI card styling"

        :scenario: "Verifies that custom KPI card styling is applied correctly."
        :strategy: "Creates KPI card with custom parameters and verifies
         component attributes."
        :contract:
         - pre: "_create_kpi_card is called with custom styling parameters."
         - post: "Custom styling is applied to KPI card components."

        """
        custom_card_style = {"backgroundColor": "#007bff", "borderRadius": "10px"}
        custom_card_class = "custom-kpi-card"
        custom_value_style = {"fontSize": "2rem", "fontWeight": "bold"}
        custom_value_class = "custom-value"
        custom_title_style = {"color": "#ffffff"}
        custom_title_class = "custom-title"

        card = _create_kpi_card(
            title="Test KPI",
            value="1000",
            icon="",
            color="primary",
            kpi_card_style=custom_card_style,
            kpi_card_className=custom_card_class,
            value_style=custom_value_style,
            value_className=custom_value_class,
            title_style=custom_title_style,
            title_className=custom_title_class,
        )

        # Check that it's a Col component
        assert isinstance(card, dbc.Col)

        # Check Card component
        card_component = card.children
        assert isinstance(card_component, dbc.Card)
        assert card_component.className == custom_card_class
        assert card_component.style == custom_card_style

        # Check CardBody
        card_body = card_component.children
        assert isinstance(card_body, dbc.CardBody)

        # Check value styling
        value = card_body.children[0]
        assert isinstance(value, html.H4)
        assert value.className == custom_value_class
        assert value.style == custom_value_style

        # Check title styling
        title = card_body.children[1]
        assert isinstance(title, html.P)
        assert title.className == custom_title_class
        assert title.style == custom_title_style

    def test_kpi_block_custom_card_styling(
        self, mock_datasource, sample_kpi_definitions
    ):
        """
        Test that KPIBlock applies custom styling to individual KPI cards.

        :hierarchy: [Tests | Blocks | KPIBlock | Card Styling Integration]
        :covers:
         - object: "parameter: kpi_card_style, kpi_card_className, value_style, title_style"
         - requirement: "PRD: Need customizable individual KPI card styling"

        :scenario: "Verifies that custom styling is applied to all KPI cards
         in the block."
        :strategy: "Creates block with custom card parameters and verifies
         styling is applied to generated cards."
        :contract:
         - pre: "KPIBlock is created with custom card styling parameters."
         - post: "Custom styling is applied to all generated KPI cards."

        """
        custom_card_style = {"backgroundColor": "#007bff", "borderRadius": "10px"}
        custom_card_class = "custom-kpi-card"
        custom_value_style = {"fontSize": "2rem"}
        custom_value_class = "custom-value"
        custom_title_style = {"color": "#ffffff"}
        custom_title_class = "custom-title"

        block = KPIBlock(
            block_id="test_kpi",
            datasource=mock_datasource,
            kpi_definitions=sample_kpi_definitions,
            subscribes_to="test_state",
            kpi_card_style=custom_card_style,
            kpi_card_className=custom_card_class,
            value_style=custom_value_style,
            value_className=custom_value_class,
            title_style=custom_title_style,
            title_className=custom_title_class,
        )

        # Get the generated KPI cards
        kpi_cards = block._update_kpi_cards()
        assert isinstance(kpi_cards, dbc.Row)

        # Check that all cards have custom styling
        for card in kpi_cards.children:
            assert isinstance(card, dbc.Col)
            card_component = card.children
            assert isinstance(card_component, dbc.Card)
            assert card_component.className == custom_card_class
            assert card_component.style == custom_card_style

            # Check CardBody children
            card_body = card_component.children
            value = card_body.children[0]
            title = card_body.children[1]

            assert value.className == custom_value_class
            assert value.style == custom_value_style
            assert title.className == custom_title_class
            assert title.style == custom_title_style

    def test_kpi_block_all_custom_parameters(
        self, mock_datasource, sample_kpi_definitions
    ):
        """
        Test that KPIBlock applies all custom parameters together.

        :hierarchy: [Tests | Blocks | KPIBlock | Complete Customization]
        :covers:
         - object: "all customization parameters"
         - requirement: "PRD: Complete style customization support"

        :scenario: "Verifies that all customization parameters work together
         without conflicts."
        :strategy: "Creates block with all custom parameters and verifies
         all are applied correctly."
        :contract:
         - pre: "KPIBlock is created with all customization parameters."
         - post: "All custom styling is applied without conflicts."

        """
        block = KPIBlock(
            block_id="test_kpi",
            datasource=mock_datasource,
            kpi_definitions=sample_kpi_definitions,
            subscribes_to="test_state",
            container_style={"backgroundColor": "#f8f9fa"},
            container_className="custom-container",
            loading_type="circle",
            kpi_card_style={"backgroundColor": "#007bff"},
            kpi_card_className="custom-kpi-card",
            value_style={"fontSize": "2rem"},
            value_className="custom-value",
            title_style={"color": "#ffffff"},
            title_className="custom-title",
        )

        layout = block.layout()

        # Verify container customizations
        assert layout.type == "circle"
        container = layout.children
        assert container.className == "custom-container"
        assert container.style == {"backgroundColor": "#f8f9fa"}

        # Verify card customizations
        kpi_cards = block._update_kpi_cards()
        for card in kpi_cards.children:
            card_component = card.children
            assert card_component.className == "custom-kpi-card"
            assert card_component.style == {"backgroundColor": "#007bff"}

            card_body = card_component.children
            value = card_body.children[0]
            title = card_body.children[1]

            assert value.className == "custom-value"
            assert value.style == {"fontSize": "2rem"}
            assert title.className == "custom-title"
            assert title.style == {"color": "#ffffff"}
