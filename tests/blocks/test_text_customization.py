"""
Tests for TextBlock customization parameters.

:hierarchy: [Tests | Blocks | TextBlock | Customization]
:covers:
 - object: "class: TextBlock"
 - requirement: "PRD: Need customizable styling for text blocks"

:scenario: "Verifies that TextBlock correctly applies all style customization
 parameters to its components including content and title."
:strategy: "Uses pytest to create block instances and verify component
 attributes match expected styling parameters."
:contract:
 - pre: "TextBlock is initialized with style parameters."
 - post: "All style parameters are correctly applied to rendered components."

"""

from unittest.mock import MagicMock, Mock

import dash_bootstrap_components as dbc
import pandas as pd
import pytest
from dash import dcc, html

from dashboard_lego.blocks.text import TextBlock
from dashboard_lego.core.datasource import BaseDataSource


class TestTextBlockCustomization:
    """Test suite for TextBlock style customization."""

    @pytest.fixture
    def mock_datasource(self):
        """Create a mock datasource for testing."""
        datasource = Mock(spec=BaseDataSource)
        datasource.get_processed_data.return_value = pd.DataFrame({"col1": [1, 2, 3]})
        return datasource

    @pytest.fixture
    def mock_content_generator(self):
        """Create a mock content generator for testing."""

        def generator(df):
            return "Generated content"

        return generator

    def test_text_block_default_styling(self, mock_datasource, mock_content_generator):
        """
        Test that TextBlock uses default styling when no custom parameters
        are provided.

        :hierarchy: [Tests | Blocks | TextBlock | Default Styling]
        :covers:
         - object: "method: TextBlock.layout"
         - requirement: "Backward compatibility: default styling preserved"

        :scenario: "Verifies that default className and styling are applied
         when no customization parameters are provided."
        :strategy: "Creates block without style parameters and checks default
         component attributes."
        :contract:
         - pre: "TextBlock is created without style parameters."
         - post: "Default styling is applied to all components."

        """
        block = TextBlock(
            block_id="test_text",
            datasource=mock_datasource,
            subscribes_to="test_state",
            content_generator=mock_content_generator,
            title="Test Title",
        )

        layout = block.layout()

        # Check that it's a Card component
        assert isinstance(layout, dbc.Card)
        assert layout.className == "mb-4"

        # Check Loading component
        loading = layout.children
        assert loading.type == "default"

        # Check container div
        container = loading.children
        assert isinstance(container, html.Div)

        # Check initial content
        initial_content = block._update_content()
        assert isinstance(initial_content, dbc.CardBody)

    def test_text_block_custom_card_styling(
        self, mock_datasource, mock_content_generator
    ):
        """
        Test that TextBlock applies custom card styling.

        :hierarchy: [Tests | Blocks | TextBlock | Card Styling]
        :covers:
         - object: "parameter: card_style, card_className, loading_type"
         - requirement: "PRD: Need customizable card styling"

        :scenario: "Verifies that custom card style and className are applied
         correctly."
        :strategy: "Creates block with custom card parameters and verifies
         component attributes."
        :contract:
         - pre: "TextBlock is created with custom card styling."
         - post: "Custom card styling is applied to Card component."

        """
        custom_style = {"backgroundColor": "#f8f9fa", "border": "2px solid #007bff"}
        custom_class = "shadow-lg rounded-lg"
        custom_loading = "circle"

        block = TextBlock(
            block_id="test_text",
            datasource=mock_datasource,
            subscribes_to="test_state",
            content_generator=mock_content_generator,
            title="Test Title",
            card_style=custom_style,
            card_className=custom_class,
            loading_type=custom_loading,
        )

        layout = block.layout()

        # Check custom card styling
        assert isinstance(layout, dbc.Card)
        assert layout.className == custom_class
        assert layout.style == custom_style

        # Check custom loading type
        loading = layout.children
        assert loading.type == custom_loading

    def test_text_block_custom_title_styling(
        self, mock_datasource, mock_content_generator
    ):
        """
        Test that TextBlock applies custom title styling.

        :hierarchy: [Tests | Blocks | TextBlock | Title Styling]
        :covers:
         - object: "parameter: title_style, title_className"
         - requirement: "PRD: Need customizable title styling"

        :scenario: "Verifies that custom title style and className are applied
         correctly."
        :strategy: "Creates block with custom title parameters and verifies
         component attributes."
        :contract:
         - pre: "TextBlock is created with custom title styling."
         - post: "Custom title styling is applied to title component."

        """
        custom_style = {"color": "#007bff", "fontSize": "1.8rem"}
        custom_class = "custom-title"

        block = TextBlock(
            block_id="test_text",
            datasource=mock_datasource,
            subscribes_to="test_state",
            content_generator=mock_content_generator,
            title="Test Title",
            title_style=custom_style,
            title_className=custom_class,
        )

        # Get the generated content
        content = block._update_content()
        assert isinstance(content, dbc.CardBody)

        # Check title styling (first child should be the title)
        title = content.children[0]
        assert isinstance(title, html.H4)
        assert title.className == custom_class
        assert title.style == custom_style

    def test_text_block_custom_content_styling(
        self, mock_datasource, mock_content_generator
    ):
        """
        Test that TextBlock applies custom content styling.

        :hierarchy: [Tests | Blocks | TextBlock | Content Styling]
        :covers:
         - object: "parameter: content_style, content_className"
         - requirement: "PRD: Need customizable content styling"

        :scenario: "Verifies that custom content style and className are applied
         correctly."
        :strategy: "Creates block with custom content parameters and verifies
         component attributes."
        :contract:
         - pre: "TextBlock is created with custom content styling."
         - post: "Custom content styling is applied to content component."

        """
        custom_style = {"backgroundColor": "#e9ecef", "padding": "15px"}
        custom_class = "custom-content"

        block = TextBlock(
            block_id="test_text",
            datasource=mock_datasource,
            subscribes_to="test_state",
            content_generator=mock_content_generator,
            title="Test Title",
            content_style=custom_style,
            content_className=custom_class,
        )

        # Get the generated content
        content = block._update_content()
        assert isinstance(content, dbc.CardBody)

        # Check content styling (last child should be the wrapped content)
        content_wrapper = content.children[-1]
        assert isinstance(content_wrapper, html.Div)
        assert content_wrapper.className == custom_class
        assert content_wrapper.style == custom_style

    def test_text_block_without_title(self, mock_datasource, mock_content_generator):
        """
        Test that TextBlock works correctly without a title.

        :hierarchy: [Tests | Blocks | TextBlock | No Title]
        :covers:
         - object: "parameter: title=None"
         - requirement: "PRD: Optional title support"

        :scenario: "Verifies that TextBlock works correctly when no title is
         provided."
        :strategy: "Creates block without title and verifies content structure."
        :contract:
         - pre: "TextBlock is created without title."
         - post: "Content is generated without title component."

        """
        block = TextBlock(
            block_id="test_text",
            datasource=mock_datasource,
            subscribes_to="test_state",
            content_generator=mock_content_generator,
        )

        # Get the generated content
        content = block._update_content()
        assert isinstance(content, dbc.CardBody)

        # Should only have one child (the content)
        assert len(content.children) == 1
        content_component = content.children[0]
        assert isinstance(content_component, dcc.Markdown)

    def test_text_block_all_custom_parameters(
        self, mock_datasource, mock_content_generator
    ):
        """
        Test that TextBlock applies all custom parameters together.

        :hierarchy: [Tests | Blocks | TextBlock | Complete Customization]
        :covers:
         - object: "all customization parameters"
         - requirement: "PRD: Complete style customization support"

        :scenario: "Verifies that all customization parameters work together
         without conflicts."
        :strategy: "Creates block with all custom parameters and verifies
         all are applied correctly."
        :contract:
         - pre: "TextBlock is created with all customization parameters."
         - post: "All custom styling is applied without conflicts."

        """
        block = TextBlock(
            block_id="test_text",
            datasource=mock_datasource,
            subscribes_to="test_state",
            content_generator=mock_content_generator,
            title="Test Title",
            card_style={"backgroundColor": "#f8f9fa"},
            card_className="shadow-lg",
            title_style={"color": "#007bff"},
            title_className="custom-title",
            content_style={"backgroundColor": "#e9ecef"},
            content_className="custom-content",
            loading_type="circle",
        )

        layout = block.layout()

        # Verify card customizations
        assert layout.className == "shadow-lg"
        assert layout.style == {"backgroundColor": "#f8f9fa"}

        # Verify loading type
        loading = layout.children
        assert loading.type == "circle"

        # Verify content customizations
        content = block._update_content()
        title = content.children[0]
        assert title.className == "custom-title"
        assert title.style == {"color": "#007bff"}

        content_wrapper = content.children[1]
        assert content_wrapper.className == "custom-content"
        assert content_wrapper.style == {"backgroundColor": "#e9ecef"}
