"""
Unit tests for the DashboardPage class.

"""

from unittest.mock import MagicMock, call

import pytest
from dash import html

from dashboard_lego.blocks.base import BaseBlock
from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.core.page import DashboardPage
from dashboard_lego.utils.exceptions import ConfigurationError


# Mock BaseBlock for testing purposes
class MockBlock(BaseBlock):
    def __init__(self, block_id, datasource=None, **kwargs):
        if datasource is None:
            # Create a mock that passes the isinstance(datasource, BaseDataSource) check
            datasource = MagicMock(spec=BaseDataSource)
        super().__init__(block_id, datasource, **kwargs)
        # Mock the layout to be a simple Div with the block_id
        self._layout = html.Div(self.block_id, id=self._generate_id("container"))

    def layout(self):
        return self._layout


@pytest.fixture
def mock_app():
    """Fixture to create a mock Dash app with a callback decorator."""
    app = MagicMock()
    app.callback = MagicMock(return_value=lambda f: f)  # Decorator returns the function
    return app


@pytest.fixture
def mock_datasource():
    """Fixture to create a mock datasource that passes type checks."""
    return MagicMock(spec=BaseDataSource)


def test_page_init_registers_blocks(mocker, mock_datasource):
    """
    Tests that DashboardPage.__init__ correctly finds all blocks and calls
    their _register_state_interactions method.

    """
    # Spy on the registration method of MockBlock
    spy_register = mocker.spy(MockBlock, "_register_state_interactions")

    block1 = MockBlock(block_id="b1", datasource=mock_datasource)
    block2 = MockBlock(block_id="b2", datasource=mock_datasource)
    block3 = MockBlock(block_id="b3", datasource=mock_datasource)

    page = DashboardPage(
        title="Test Page", blocks=[[block1], [(block2, {"width": 8}), block3]]
    )

    # Assert that the registration method was called for each block
    assert spy_register.call_count == 3
    # Check that it was called with the page's state_manager instance
    spy_register.assert_has_calls(
        [
            call(block1, page.state_manager),
            call(block2, page.state_manager),
            call(block3, page.state_manager),
        ],
        any_order=True,
    )


def test_page_build_layout_structure(mock_datasource):
    """
    Tests that build_layout creates the correct dbc grid structure.

    """
    block1 = MockBlock(block_id="b1", datasource=mock_datasource)
    block2 = MockBlock(block_id="b2", datasource=mock_datasource)
    block3 = MockBlock(block_id="b3", datasource=mock_datasource)

    page = DashboardPage(
        title="My Dashboard",
        blocks=[
            [block1],  # First row
            [(block2, {"lg": 8}), (block3, {"lg": 4})],  # Second row
        ],
    )

    layout = page.build_layout()

    # Basic assertions
    assert layout.fluid is True
    assert layout.children[0].children == "My Dashboard"

    # Check rows
    rows = layout.children[1:]
    assert len(rows) == 2

    # Check first row
    row1_cols = rows[0].children
    assert len(row1_cols) == 1
    assert row1_cols[0].children.children == "b1"
    # Back-compat auto assignment uses 'width'
    assert getattr(row1_cols[0], "width", None) == 12

    # Check second row
    row2_cols = rows[1].children
    assert len(row2_cols) == 2
    assert row2_cols[0].children.children == "b2"
    assert row2_cols[0].lg == 8
    assert row2_cols[1].children.children == "b3"
    assert row2_cols[1].lg == 4


def test_page_register_callbacks_delegates_to_state_manager(mocker, mock_app):
    """
    Tests that register_callbacks correctly delegates the call to the state manager.

    """
    # We don't need real blocks for this test
    page = DashboardPage(title="Test", blocks=[])

    # Spy on the state manager's method
    spy_generate = mocker.spy(page.state_manager, "generate_callbacks")

    # Call the method to be tested
    page.register_callbacks(mock_app)

    # Assert that the state manager's method was called exactly once with the app
    spy_generate.assert_called_once_with(mock_app)


def test_page_init_raises_error_for_invalid_block_type(mock_datasource):
    """
    Tests that DashboardPage raises a TypeError if a non-BaseBlock object
    is passed in the layout structure.

    """
    block1 = MockBlock(block_id="b1", datasource=mock_datasource)
    invalid_object = html.Div("I am not a block")

    with pytest.raises(
        ConfigurationError, match="All layout items must be of type BaseBlock"
    ):
        DashboardPage(title="Test", blocks=[[block1, invalid_object]])
