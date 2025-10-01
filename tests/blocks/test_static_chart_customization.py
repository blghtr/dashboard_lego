"""
Tests for StaticChartBlock customization parameters.

:hierarchy: [Tests | Blocks | StaticChartBlock | Customization]
:covers:
 - object: "class: StaticChartBlock"
 - requirement: "PRD: Need customizable styling for chart blocks"

:scenario: "Verifies that StaticChartBlock correctly applies all style
 customization parameters to its components."
:strategy: "Uses pytest to create block instances and verify component
 attributes match expected styling parameters."
:contract:
 - pre: "StaticChartBlock is initialized with style parameters."
 - post: "All style parameters are correctly applied to rendered components."

"""

from unittest.mock import MagicMock, Mock

import dash_bootstrap_components as dbc
import pytest
from dash import html

from dashboard_lego.blocks.chart import StaticChartBlock
from dashboard_lego.core.datasource import BaseDataSource


class TestStaticChartBlockCustomization:
    """Test suite for StaticChartBlock style customization."""

    @pytest.fixture
    def mock_datasource(self):
        """Create a mock datasource for testing."""
        datasource = Mock(spec=BaseDataSource)
        datasource.get_processed_data.return_value = Mock()
        return datasource

    @pytest.fixture
    def mock_chart_generator(self):
        """Create a mock chart generator for testing."""

        def generator(df, ctx):
            return Mock()

        return generator

    def test_static_chart_default_styling(self, mock_datasource, mock_chart_generator):
        """
        Test that StaticChartBlock uses default styling when no custom
        parameters are provided.

        :hierarchy: [Tests | Blocks | StaticChartBlock | Default Styling]
        :covers:
         - object: "method: StaticChartBlock.layout"
         - requirement: "Backward compatibility: default styling preserved"

        :scenario: "Verifies that default className and styling are applied
         when no customization parameters are provided."
        :strategy: "Creates block without style parameters and checks default
         component attributes."
        :contract:
         - pre: "StaticChartBlock is created without style parameters."
         - post: "Default styling is applied to all components."

        """
        block = StaticChartBlock(
            block_id="test_chart",
            datasource=mock_datasource,
            title="Test Chart",
            chart_generator=mock_chart_generator,
            subscribes_to="test_state",
        )

        layout = block.layout()

        # Check that it's a Card component
        assert isinstance(layout, dbc.Card)
        assert layout.className == "mb-4"

        # Check CardBody structure
        card_body = layout.children
        assert isinstance(card_body, dbc.CardBody)

        # Check title styling
        title = card_body.children[0]
        assert isinstance(title, html.H4)
        assert title.className == "card-title"

        # Check loading component
        loading = card_body.children[1]
        assert loading.type == "default"

        # Check graph component
        graph = loading.children
        assert graph.config == {}

    def test_static_chart_custom_card_styling(
        self, mock_datasource, mock_chart_generator
    ):
        """
        Test that StaticChartBlock applies custom card styling.

        :hierarchy: [Tests | Blocks | StaticChartBlock | Card Styling]
        :covers:
         - object: "parameter: card_style, card_className"
         - requirement: "PRD: Need customizable card styling"

        :scenario: "Verifies that custom card style and className are applied
         correctly."
        :strategy: "Creates block with custom card parameters and verifies
         component attributes."
        :contract:
         - pre: "StaticChartBlock is created with custom card styling."
         - post: "Custom card styling is applied to Card component."

        """
        custom_style = {"backgroundColor": "#f8f9fa", "border": "2px solid #007bff"}
        custom_class = "shadow-lg rounded-lg"

        block = StaticChartBlock(
            block_id="test_chart",
            datasource=mock_datasource,
            title="Test Chart",
            chart_generator=mock_chart_generator,
            subscribes_to="test_state",
            card_style=custom_style,
            card_className=custom_class,
        )

        layout = block.layout()

        # Check custom card styling
        assert isinstance(layout, dbc.Card)
        assert layout.className == custom_class
        assert layout.style == custom_style

    def test_static_chart_custom_title_styling(
        self, mock_datasource, mock_chart_generator
    ):
        """
        Test that StaticChartBlock applies custom title styling.

        :hierarchy: [Tests | Blocks | StaticChartBlock | Title Styling]
        :covers:
         - object: "parameter: title_style, title_className"
         - requirement: "PRD: Need customizable title styling"

        :scenario: "Verifies that custom title style and className are applied
         correctly."
        :strategy: "Creates block with custom title parameters and verifies
         component attributes."
        :contract:
         - pre: "StaticChartBlock is created with custom title styling."
         - post: "Custom title styling is applied to title component."

        """
        custom_style = {"color": "#007bff", "fontSize": "1.8rem"}
        custom_class = "custom-title"

        block = StaticChartBlock(
            block_id="test_chart",
            datasource=mock_datasource,
            title="Test Chart",
            chart_generator=mock_chart_generator,
            subscribes_to="test_state",
            title_style=custom_style,
            title_className=custom_class,
        )

        layout = block.layout()
        card_body = layout.children
        title = card_body.children[0]

        # Check custom title styling
        assert isinstance(title, html.H4)
        assert title.className == custom_class
        assert title.style == custom_style

    def test_static_chart_custom_graph_styling(
        self, mock_datasource, mock_chart_generator
    ):
        """
        Test that StaticChartBlock applies custom graph styling.

        :hierarchy: [Tests | Blocks | StaticChartBlock | Graph Styling]
        :covers:
         - object: "parameter: graph_config, graph_style, loading_type"
         - requirement: "PRD: Need customizable graph styling"

        :scenario: "Verifies that custom graph configuration and styling are
         applied correctly."
        :strategy: "Creates block with custom graph parameters and verifies
         component attributes."
        :contract:
         - pre: "StaticChartBlock is created with custom graph styling."
         - post: "Custom graph styling is applied to Graph component."

        """
        custom_config = {"displayModeBar": False, "scrollZoom": True}
        custom_style = {"height": "500px"}
        custom_loading = "circle"

        block = StaticChartBlock(
            block_id="test_chart",
            datasource=mock_datasource,
            title="Test Chart",
            chart_generator=mock_chart_generator,
            subscribes_to="test_state",
            graph_config=custom_config,
            graph_style=custom_style,
            loading_type=custom_loading,
        )

        layout = block.layout()
        card_body = layout.children
        loading = card_body.children[1]
        graph = loading.children

        # Check custom loading type
        assert loading.type == custom_loading

        # Check custom graph styling
        assert graph.config == custom_config
        assert graph.style == custom_style

    def test_static_chart_figure_layout_override(
        self, mock_datasource, mock_chart_generator
    ):
        """
        Test that StaticChartBlock applies figure layout overrides.

        :hierarchy: [Tests | Blocks | StaticChartBlock | Figure Layout]
        :covers:
         - object: "parameter: figure_layout"
         - requirement: "PRD: Need customizable Plotly figure layout"

        :scenario: "Verifies that figure layout overrides are applied to the
         generated figure."
        :strategy: "Creates block with figure layout and verifies it's stored
         correctly."
        :contract:
         - pre: "StaticChartBlock is created with figure layout overrides."
         - post: "Figure layout overrides are stored and available for use."

        """
        custom_layout = {"template": "plotly_dark", "height": 500}

        block = StaticChartBlock(
            block_id="test_chart",
            datasource=mock_datasource,
            title="Test Chart",
            chart_generator=mock_chart_generator,
            subscribes_to="test_state",
            figure_layout=custom_layout,
        )

        # Check that figure layout is stored
        assert block.figure_layout == custom_layout

    def test_static_chart_all_custom_parameters(
        self, mock_datasource, mock_chart_generator
    ):
        """
        Test that StaticChartBlock applies all custom parameters together.

        :hierarchy: [Tests | Blocks | StaticChartBlock | Complete Customization]
        :covers:
         - object: "all customization parameters"
         - requirement: "PRD: Complete style customization support"

        :scenario: "Verifies that all customization parameters work together
         without conflicts."
        :strategy: "Creates block with all custom parameters and verifies
         all are applied correctly."
        :contract:
         - pre: "StaticChartBlock is created with all customization parameters."
         - post: "All custom styling is applied without conflicts."

        """
        block = StaticChartBlock(
            block_id="test_chart",
            datasource=mock_datasource,
            title="Test Chart",
            chart_generator=mock_chart_generator,
            subscribes_to="test_state",
            card_style={"backgroundColor": "#f8f9fa"},
            card_className="shadow-lg",
            title_style={"color": "#007bff"},
            title_className="custom-title",
            loading_type="circle",
            graph_config={"displayModeBar": False},
            graph_style={"height": "500px"},
            figure_layout={"template": "plotly_dark"},
        )

        layout = block.layout()

        # Verify all customizations are applied
        assert layout.className == "shadow-lg"
        assert layout.style == {"backgroundColor": "#f8f9fa"}

        card_body = layout.children
        title = card_body.children[0]
        assert title.className == "custom-title"
        assert title.style == {"color": "#007bff"}

        loading = card_body.children[1]
        assert loading.type == "circle"

        graph = loading.children
        assert graph.config == {"displayModeBar": False}
        assert graph.style == {"height": "500px"}

        assert block.figure_layout == {"template": "plotly_dark"}
