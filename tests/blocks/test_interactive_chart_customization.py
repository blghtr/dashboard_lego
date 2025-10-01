"""
Tests for InteractiveChartBlock customization parameters.

:hierarchy: [Tests | Blocks | InteractiveChartBlock | Customization]
:covers:
 - object: "class: InteractiveChartBlock"
 - requirement: "PRD: Need customizable styling for interactive chart blocks"

:scenario: "Verifies that InteractiveChartBlock correctly applies all style
 customization parameters to its components including controls."
:strategy: "Uses pytest to create block instances and verify component
 attributes match expected styling parameters."
:contract:
 - pre: "InteractiveChartBlock is initialized with style parameters."
 - post: "All style parameters are correctly applied to rendered components."

"""

from unittest.mock import MagicMock, Mock

import dash_bootstrap_components as dbc
import pytest
from dash import dcc, html

from dashboard_lego.blocks.chart import Control, InteractiveChartBlock
from dashboard_lego.core.datasource import BaseDataSource


class TestInteractiveChartBlockCustomization:
    """Test suite for InteractiveChartBlock style customization."""

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

    @pytest.fixture
    def sample_controls(self):
        """Create sample controls for testing."""
        return {
            "filter": Control(
                component=dcc.Dropdown,
                props={"options": [{"label": "A", "value": "a"}], "value": "a"},
            ),
            "slider": Control(
                component=dcc.Slider, props={"min": 0, "max": 100, "value": 50}
            ),
        }

    def test_interactive_chart_default_styling(
        self, mock_datasource, mock_chart_generator, sample_controls
    ):
        """
        Test that InteractiveChartBlock uses default styling when no custom
        parameters are provided.

        :hierarchy: [Tests | Blocks | InteractiveChartBlock | Default Styling]
        :covers:
         - object: "method: InteractiveChartBlock.layout"
         - requirement: "Backward compatibility: default styling preserved"

        :scenario: "Verifies that default className and styling are applied
         when no customization parameters are provided."
        :strategy: "Creates block without style parameters and checks default
         component attributes."
        :contract:
         - pre: "InteractiveChartBlock is created without style parameters."
         - post: "Default styling is applied to all components."

        """
        block = InteractiveChartBlock(
            block_id="test_chart",
            datasource=mock_datasource,
            title="Test Chart",
            chart_generator=mock_chart_generator,
            controls=sample_controls,
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

        # Check controls row styling
        controls_row = card_body.children[1]
        assert isinstance(controls_row, dbc.Row)
        assert controls_row.className == "mb-3 align-items-center"

        # Check loading component
        loading = card_body.children[2]
        assert loading.type == "default"

        # Check graph component
        graph = loading.children
        assert graph.config == {}

    def test_interactive_chart_custom_card_styling(
        self, mock_datasource, mock_chart_generator, sample_controls
    ):
        """
            Test that InteractiveChartBlock applies custom card styling.

            :hierarchy: [Tests | Blocks | InteractiveChartBlock | Card Styling]
        :covers:
             - object: "parameter: card_style, card_className"
             - requirement: "PRD: Need customizable card styling"

            :scenario: "Verifies that custom card style and className are applied
             correctly."
            :strategy: "Creates block with custom card parameters and verifies
             component attributes."
        :contract:
             - pre: "InteractiveChartBlock is created with custom card styling."
             - post: "Custom card styling is applied to Card component."

        """
        custom_style = {"backgroundColor": "#f8f9fa", "border": "2px solid #007bff"}
        custom_class = "shadow-lg rounded-lg"

        block = InteractiveChartBlock(
            block_id="test_chart",
            datasource=mock_datasource,
            title="Test Chart",
            chart_generator=mock_chart_generator,
            controls=sample_controls,
            card_style=custom_style,
            card_className=custom_class,
        )

        layout = block.layout()

        # Check custom card styling
        assert isinstance(layout, dbc.Card)
        assert layout.className == custom_class
        assert layout.style == custom_style

    def test_interactive_chart_custom_controls_styling(
        self, mock_datasource, mock_chart_generator, sample_controls
    ):
        """
            Test that InteractiveChartBlock applies custom controls row styling.

            :hierarchy: [Tests | Blocks | InteractiveChartBlock | Controls Styling]
        :covers:
             - object: "parameter: controls_row_style, controls_row_className"
             - requirement: "PRD: Need customizable controls styling"

            :scenario: "Verifies that custom controls row style and className are
             applied correctly."
            :strategy: "Creates block with custom controls parameters and verifies
             component attributes."
        :contract:
             - pre: "InteractiveChartBlock is created with custom controls styling."
             - post: "Custom controls styling is applied to controls row."

        """
        custom_style = {"backgroundColor": "#e9ecef", "padding": "10px"}
        custom_class = "custom-controls-row"

        block = InteractiveChartBlock(
            block_id="test_chart",
            datasource=mock_datasource,
            title="Test Chart",
            chart_generator=mock_chart_generator,
            controls=sample_controls,
            controls_row_style=custom_style,
            controls_row_className=custom_class,
        )

        layout = block.layout()
        card_body = layout.children
        controls_row = card_body.children[1]

        # Check custom controls row styling
        assert isinstance(controls_row, dbc.Row)
        assert controls_row.className == custom_class
        assert controls_row.style == custom_style

    def test_interactive_chart_custom_title_styling(
        self, mock_datasource, mock_chart_generator, sample_controls
    ):
        """
            Test that InteractiveChartBlock applies custom title styling.

            :hierarchy: [Tests | Blocks | InteractiveChartBlock | Title Styling]
        :covers:
             - object: "parameter: title_style, title_className"
             - requirement: "PRD: Need customizable title styling"

            :scenario: "Verifies that custom title style and className are applied
             correctly."
            :strategy: "Creates block with custom title parameters and verifies
             component attributes."
        :contract:
             - pre: "InteractiveChartBlock is created with custom title styling."
             - post: "Custom title styling is applied to title component."

        """
        custom_style = {"color": "#007bff", "fontSize": "1.8rem"}
        custom_class = "custom-title"

        block = InteractiveChartBlock(
            block_id="test_chart",
            datasource=mock_datasource,
            title="Test Chart",
            chart_generator=mock_chart_generator,
            controls=sample_controls,
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

    def test_interactive_chart_custom_graph_styling(
        self, mock_datasource, mock_chart_generator, sample_controls
    ):
        """
            Test that InteractiveChartBlock applies custom graph styling.

            :hierarchy: [Tests | Blocks | InteractiveChartBlock | Graph Styling]
        :covers:
             - object: "parameter: graph_config, graph_style, loading_type"
             - requirement: "PRD: Need customizable graph styling"

            :scenario: "Verifies that custom graph configuration and styling are
             applied correctly."
            :strategy: "Creates block with custom graph parameters and verifies
             component attributes."
        :contract:
             - pre: "InteractiveChartBlock is created with custom graph styling."
             - post: "Custom graph styling is applied to Graph component."

        """
        custom_config = {"displayModeBar": False, "scrollZoom": True}
        custom_style = {"height": "500px"}
        custom_loading = "circle"

        block = InteractiveChartBlock(
            block_id="test_chart",
            datasource=mock_datasource,
            title="Test Chart",
            chart_generator=mock_chart_generator,
            controls=sample_controls,
            graph_config=custom_config,
            graph_style=custom_style,
            loading_type=custom_loading,
        )

        layout = block.layout()
        card_body = layout.children
        loading = card_body.children[2]
        graph = loading.children

        # Check custom loading type
        assert loading.type == custom_loading

        # Check custom graph styling
        assert graph.config == custom_config
        assert graph.style == custom_style

    def test_interactive_chart_figure_layout_override(
        self, mock_datasource, mock_chart_generator, sample_controls
    ):
        """
            Test that InteractiveChartBlock applies figure layout overrides.

            :hierarchy: [Tests | Blocks | InteractiveChartBlock | Figure Layout]
        :covers:
             - object: "parameter: figure_layout"
             - requirement: "PRD: Need customizable Plotly figure layout"

            :scenario: "Verifies that figure layout overrides are applied to the
             generated figure."
            :strategy: "Creates block with figure layout and verifies it's stored
             correctly."
        :contract:
             - pre: "InteractiveChartBlock is created with figure layout overrides."
             - post: "Figure layout overrides are stored and available for use."

        """
        custom_layout = {"template": "plotly_dark", "height": 500}

        block = InteractiveChartBlock(
            block_id="test_chart",
            datasource=mock_datasource,
            title="Test Chart",
            chart_generator=mock_chart_generator,
            controls=sample_controls,
            figure_layout=custom_layout,
        )

        # Check that figure layout is stored
        assert block.figure_layout == custom_layout

    def test_interactive_chart_all_custom_parameters(
        self, mock_datasource, mock_chart_generator, sample_controls
    ):
        """
            Test that InteractiveChartBlock applies all custom parameters together.

            :hierarchy: [Tests | Blocks | InteractiveChartBlock | Complete Customization]
        :covers:
             - object: "all customization parameters"
             - requirement: "PRD: Complete style customization support"

            :scenario: "Verifies that all customization parameters work together
             without conflicts."
            :strategy: "Creates block with all custom parameters and verifies
             all are applied correctly."
        :contract:
             - pre: "InteractiveChartBlock is created with all customization parameters."
             - post: "All custom styling is applied without conflicts."

        """
        block = InteractiveChartBlock(
            block_id="test_chart",
            datasource=mock_datasource,
            title="Test Chart",
            chart_generator=mock_chart_generator,
            controls=sample_controls,
            card_style={"backgroundColor": "#f8f9fa"},
            card_className="shadow-lg",
            title_style={"color": "#007bff"},
            title_className="custom-title",
            controls_row_style={"backgroundColor": "#e9ecef"},
            controls_row_className="custom-controls",
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

        controls_row = card_body.children[1]
        assert controls_row.className == "custom-controls"
        assert controls_row.style == {"backgroundColor": "#e9ecef"}

        loading = card_body.children[2]
        assert loading.type == "circle"

        graph = loading.children
        assert graph.config == {"displayModeBar": False}
        assert graph.style == {"height": "500px"}

        assert block.figure_layout == {"template": "plotly_dark"}
