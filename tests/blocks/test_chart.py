"""
Unit tests for Chart blocks.

"""

from unittest.mock import MagicMock, call

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import pytest
from dash import dcc, html

from dashboard_lego.blocks.chart import Control, InteractiveChartBlock, StaticChartBlock
from dashboard_lego.core.state import StateManager


@pytest.fixture
def mock_plot_fn(mocker):
    """Fixture to create a mock plotting function."""
    return mocker.MagicMock(return_value=go.Figure(data=[go.Bar(y=[1, 2, 3])]))


class TestStaticChartBlock:
    def test_layout(self, datasource_factory):
        mock_ds = datasource_factory()
        block = StaticChartBlock(
            "test_chart", mock_ds, "My Chart", lambda df: go.Figure(), "state_id"
        )
        layout = block.layout()
        assert isinstance(layout, dbc.Card)
        card_body = layout.children
        assert isinstance(card_body, dbc.CardBody)
        assert card_body.children[0].children == "My Chart"
        assert isinstance(card_body.children[1], dcc.Loading)

    def test_update_chart_with_data(self, datasource_factory, mock_plot_fn):
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        mock_ds = datasource_factory(get_processed_data=df)
        block = StaticChartBlock(
            "test_chart", mock_ds, "My Chart", mock_plot_fn, "state_id"
        )

        figure = block._update_chart()

        # Check that the function was called with ChartContext
        mock_plot_fn.assert_called_once()
        call_args = mock_plot_fn.call_args
        assert call_args[0][0].equals(df)  # First argument should be DataFrame
        assert hasattr(
            call_args[0][1], "datasource"
        )  # Second argument should be ChartContext
        assert isinstance(figure, go.Figure)
        assert len(figure.data) == 1  # From mock_plot_fn

    def test_update_chart_empty_df(self, datasource_factory, mock_plot_fn):
        mock_ds = datasource_factory(get_processed_data=pd.DataFrame())
        block = StaticChartBlock(
            "test_chart", mock_ds, "My Chart", mock_plot_fn, "state_id"
        )

        figure = block._update_chart()

        mock_plot_fn.assert_not_called()
        assert isinstance(figure, go.Figure)
        assert len(figure.data) == 0


class TestInteractiveChartBlock:
    @pytest.fixture
    def controls(self):
        return {
            "dropdown": Control(component=dcc.Dropdown, props={"options": ["a", "b"]}),
            "slider": Control(component=dcc.Slider, props={"min": 0, "max": 10}),
        }

    def test_layout(self, datasource_factory, controls):
        mock_ds = datasource_factory()
        block = InteractiveChartBlock(
            "interactive",
            mock_ds,
            "Interactive Chart",
            lambda df: go.Figure(),
            controls,
        )
        layout = block.layout()

        # Check title
        assert layout.children.children[0].children == "Interactive Chart"
        # Check controls row
        controls_row = layout.children.children[1]
        assert len(controls_row.children) == 2
        assert isinstance(controls_row.children[0].children, dcc.Dropdown)
        assert controls_row.children[0].children.id == "interactive-dropdown"
        assert isinstance(controls_row.children[1].children, dcc.Slider)
        assert controls_row.children[1].children.id == "interactive-slider"
        # Check graph
        assert isinstance(layout.children.children[2].children, dcc.Graph)

    def test_update_chart(self, datasource_factory, controls, mock_plot_fn):
        df = pd.DataFrame({"a": [1, 2]})
        mock_ds = datasource_factory(get_processed_data=df)
        block = InteractiveChartBlock(
            "interactive", mock_ds, "My Chart", mock_plot_fn, controls
        )

        # Simulate callback context with control values
        figure = block._update_chart(
            **{"interactive-dropdown": "a", "interactive-slider": 5}
        )

        # Check that the function was called with ChartContext
        mock_plot_fn.assert_called_once()
        call_args = mock_plot_fn.call_args
        assert call_args[0][0].equals(df)  # First argument should be DataFrame
        assert hasattr(
            call_args[0][1], "datasource"
        )  # Second argument should be ChartContext
        assert call_args[0][1].controls == {"dropdown": "a", "slider": 5}
        assert isinstance(figure, go.Figure)

    def test_state_registration(self, datasource_factory, controls):
        mock_ds = datasource_factory()
        block = InteractiveChartBlock(
            "interactive", mock_ds, "My Chart", lambda df: go.Figure(), controls
        )
        state_manager = StateManager()
        block._register_state_interactions(state_manager)

        # Check publishers
        assert "interactive-dropdown" in state_manager.dependency_graph
        assert (
            state_manager.dependency_graph["interactive-dropdown"]["publisher"][
                "component_id"
            ]
            == "interactive-dropdown"
        )
        assert "interactive-slider" in state_manager.dependency_graph

        # Check subscribers
        # The block subscribes to its own publishers
        assert (
            len(state_manager.dependency_graph["interactive-dropdown"]["subscribers"])
            == 1
        )
        assert (
            state_manager.dependency_graph["interactive-dropdown"]["subscribers"][0][
                "callback_fn"
            ]
            == block._update_chart
        )
