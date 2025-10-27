"""
Unit tests for Chart blocks.

Updated for v0.15.0: Using TypedChartBlock instead of StaticChartBlock/InteractiveChartBlock
"""

from unittest.mock import MagicMock, call

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
import pytest
from dash import dcc, html

from dashboard_lego.blocks.control_panel import Control
from dashboard_lego.blocks.typed_chart import TypedChartBlock
from dashboard_lego.core.state import StateManager
from dashboard_lego.utils.plot_registry import register_plot_type


@pytest.fixture
def mock_plot_fn(mocker):
    """Fixture to create a mock plotting function for TypedChartBlock."""
    return mocker.MagicMock(return_value=go.Figure(data=[go.Bar(y=[1, 2, 3])]))


@pytest.fixture(autouse=True)
def register_test_plot_types(mock_plot_fn):
    """Register test plot types for testing."""
    # Register a simple test plot type
    register_plot_type("test_plot", lambda df, **kwargs: go.Figure())
    register_plot_type("test_mock_plot", mock_plot_fn)
    yield
    # Cleanup not needed - registry persists but that's okay for tests


class TestTypedChartBlock:
    """Tests for TypedChartBlock with custom plot functions."""

    def test_layout(self, datasource_factory):
        mock_ds = datasource_factory()
        block = TypedChartBlock(
            block_id="test_chart",
            datasource=mock_ds,
            title="My Chart",
            plot_type="test_plot",
            plot_params={},
            subscribes_to="state_id",
        )
        layout = block.layout()
        assert isinstance(layout, dbc.Card)
        card_body = layout.children
        assert isinstance(card_body, dbc.CardBody)
        assert card_body.children[0].children == "My Chart"
        assert isinstance(card_body.children[1], dcc.Loading)

    def test_update_chart_with_data(self, datasource_factory, mock_plot_fn):
        """Test that TypedChartBlock correctly uses registered plot function."""
        df = pd.DataFrame({"a": [1, 2], "b": [3, 4]})
        mock_ds = datasource_factory(get_processed_data=df)
        block = TypedChartBlock(
            block_id="test_chart",
            datasource=mock_ds,
            title="My Chart",
            plot_type="test_mock_plot",
            plot_params={},
            subscribes_to="state_id",
        )

        # Verify block was created with correct plot function
        assert block.block_id == "test_chart"
        assert block._plot_type == "test_mock_plot"
        assert block.plot_func == mock_plot_fn
        assert block.datasource == mock_ds

    def test_update_chart_empty_df(self, datasource_factory, mock_plot_fn):
        """Test that TypedChartBlock handles empty DataFrame correctly."""
        mock_ds = datasource_factory(get_processed_data=pd.DataFrame())
        block = TypedChartBlock(
            block_id="test_chart",
            datasource=mock_ds,
            title="My Chart",
            plot_type="test_mock_plot",
            plot_params={},
            subscribes_to="state_id",
        )

        # Verify block was created successfully even with empty data
        assert block.block_id == "test_chart"
        assert block.datasource == mock_ds
        assert block.plot_func == mock_plot_fn


class TestTypedChartBlockWithControls:
    """Tests for TypedChartBlock with built-in controls."""

    @pytest.fixture
    def controls(self):
        return {
            "dropdown": Control(
                component=dcc.Dropdown, props={"options": ["a", "b"], "value": "a"}
            ),
            "slider": Control(
                component=dcc.Slider, props={"min": 0, "max": 10, "value": 5}
            ),
        }

    def test_layout_with_controls(self, datasource_factory, controls):
        mock_ds = datasource_factory()
        block = TypedChartBlock(
            block_id="interactive",
            datasource=mock_ds,
            title="Interactive Chart",
            plot_type="test_plot",
            plot_params={},
            controls=controls,
        )
        layout = block.layout()

        # Check it's a card
        assert isinstance(layout, dbc.Card)
        card_body = layout.children
        assert isinstance(card_body, dbc.CardBody)

        # Check title
        assert card_body.children[0].children == "Interactive Chart"

        # Check controls row exists
        controls_row = card_body.children[1]
        assert len(controls_row.children) == 2

        # Check graph
        assert isinstance(card_body.children[2].children, dcc.Graph)

    def test_update_chart_with_controls(
        self, datasource_factory, controls, mock_plot_fn
    ):
        """Test that TypedChartBlock correctly registers controls."""
        df = pd.DataFrame({"a": [1, 2]})
        mock_ds = datasource_factory(get_processed_data=df)
        block = TypedChartBlock(
            block_id="interactive",
            datasource=mock_ds,
            title="My Chart",
            plot_type="test_mock_plot",
            plot_params={},
            controls=controls,
        )

        # Verify block was created with controls
        assert block.block_id == "interactive"
        assert block.controls == controls
        assert len(block.controls) == 2
        assert "dropdown" in block.controls
        assert "slider" in block.controls

    def test_state_registration_with_controls(self, datasource_factory, controls):
        mock_ds = datasource_factory()
        block = TypedChartBlock(
            block_id="interactive",
            datasource=mock_ds,
            title="My Chart",
            plot_type="test_plot",
            plot_params={},
            controls=controls,
        )
        state_manager = StateManager()
        block._register_state_interactions(state_manager)

        # Check publishers for controls are registered
        assert "interactive-dropdown" in state_manager.dependency_graph
        assert "interactive-slider" in state_manager.dependency_graph

        # v0.15: Block-centric callbacks pattern - controls DO NOT have subscribers
        # in dependency_graph. Instead, block subscribes to ALL its controls via
        # list_control_inputs(). Check that method returns correct control IDs:
        control_inputs = block.list_control_inputs()
        assert len(control_inputs) == 2
        control_ids = [ctrl_id for ctrl_id, _ in control_inputs]
        assert "interactive-dropdown" in control_ids
        assert "interactive-slider" in control_ids


class TestMultiStateSubscription:
    """
    Tests for multi-state subscription feature with TypedChartBlock.

    :hierarchy: [Testing | Unit Tests | Blocks | Multi-State Subscription]
    :covers:
     - object: "BaseBlock._normalize_subscribes_to"
     - object: "TypedChartBlock with list subscription"
     - requirement: "Support subscribing to multiple states"

    :scenario: "Verifies that blocks can subscribe to multiple states using
     a list parameter without causing TypeError."
    :strategy: "Create blocks with list subscription parameters and verify
     state registration occurs correctly for all states."
    :contract:
     - pre: "subscribes_to accepts both str and List[str] types."
     - post: "Block subscribes to all specified states successfully."

    """

    def test_typed_chart_list_subscription(self, datasource_factory):
        """Test TypedChartBlock with list of state IDs."""
        mock_ds = datasource_factory()
        state_ids = ["filter-state-1", "filter-state-2"]

        # This should not raise TypeError
        block = TypedChartBlock(
            block_id="test_chart",
            datasource=mock_ds,
            title="My Chart",
            plot_type="test_plot",
            plot_params={},
            subscribes_to=state_ids,
        )

        # Verify subscribes dict was created correctly
        assert block.subscribes is not None
        assert len(block.subscribes) == 2
        assert "filter-state-1" in block.subscribes
        assert "filter-state-2" in block.subscribes

    def test_typed_chart_single_string_subscription(self, datasource_factory):
        """Test TypedChartBlock still works with single string (regression)."""
        mock_ds = datasource_factory()

        block = TypedChartBlock(
            block_id="test_chart",
            datasource=mock_ds,
            title="My Chart",
            plot_type="test_plot",
            plot_params={},
            subscribes_to="single-state",
        )

        # Verify subscribes dict was created correctly
        assert block.subscribes is not None
        assert len(block.subscribes) == 1
        assert "single-state" in block.subscribes

    def test_typed_chart_with_controls_and_external_subscriptions(
        self, datasource_factory, mocker
    ):
        """Test TypedChartBlock with controls and external state IDs."""
        mock_ds = datasource_factory()
        controls = {
            "my_control": Control(
                component=dcc.Dropdown, props={"options": ["a", "b"]}
            ),
        }
        external_states = ["external-state-1", "external-state-2"]

        # This should not raise TypeError
        block = TypedChartBlock(
            block_id="interactive",
            datasource=mock_ds,
            title="Interactive Chart",
            plot_type="test_plot",
            plot_params={},
            controls=controls,
            subscribes_to=external_states,
        )

        # Manually register state to populate subscribes list
        mock_state_manager = mocker.MagicMock(spec=StateManager)
        block._register_state_interactions(mock_state_manager)

        # v0.15: Block-centric pattern - subscribes contains ONLY external states
        # Own controls are handled via list_control_inputs()
        assert block.subscribes is not None
        assert len(block.subscribes) == 2  # Only 2 external states
        assert "external-state-1" in block.subscribes
        assert "external-state-2" in block.subscribes

        # Verify controls handled via list_control_inputs
        control_inputs = block.list_control_inputs()
        assert len(control_inputs) == 1

    def test_typed_chart_with_controls_no_external(self, datasource_factory, mocker):
        """Test TypedChartBlock with controls but no external subscriptions."""
        mock_ds = datasource_factory()
        controls = {
            "my_control": Control(
                component=dcc.Dropdown, props={"options": ["a", "b"]}
            ),
        }

        block = TypedChartBlock(
            block_id="interactive",
            datasource=mock_ds,
            title="Interactive Chart",
            plot_type="test_plot",
            plot_params={},
            controls=controls,
            subscribes_to=None,
        )

        # Manually register state to populate subscribes list
        mock_state_manager = mocker.MagicMock(spec=StateManager)
        block._register_state_interactions(mock_state_manager)

        # v0.15: Block-centric pattern - subscribes is EMPTY (no external states)
        # Own controls are handled via list_control_inputs()
        assert len(block.subscribes) == 0

        # Verify controls handled via list_control_inputs
        control_inputs = block.list_control_inputs()
        assert len(control_inputs) == 1
        assert "interactive-my_control" in [ctrl_id for ctrl_id, _ in control_inputs]

    def test_multi_state_registration(self, datasource_factory):
        """Test that multiple states register correctly with StateManager."""
        mock_ds = datasource_factory()
        state_ids = ["state-a", "state-b", "state-c"]

        block = TypedChartBlock(
            block_id="test_chart",
            datasource=mock_ds,
            title="My Chart",
            plot_type="test_plot",
            plot_params={},
            subscribes_to=state_ids,
        )

        state_manager = StateManager()
        block._register_state_interactions(state_manager)

        # Verify all states are registered
        for state_id in state_ids:
            assert state_id in state_manager.dependency_graph
            subscribers = state_manager.dependency_graph[state_id]["subscribers"]
            assert len(subscribers) == 1
            assert subscribers[0]["component_id"] == "test_chart-container"


class TestFigureExport:
    def test_get_figure_returns_plotly_figure(self, datasource_factory):
        """Test get_figure returns valid Plotly Figure."""
        chart = TypedChartBlock(
            block_id="test",
            datasource=datasource_factory(
                get_processed_data=pd.DataFrame({"x": [1, 2], "y": [3, 4]})
            ),
            plot_type="scatter",
            plot_params={"x": "x", "y": "y"},
        )

        fig = chart.get_figure()

        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0

    def test_get_figure_with_params(self, datasource_factory):
        """Test get_figure accepts parameters."""
        chart = TypedChartBlock(
            block_id="test",
            datasource=datasource_factory(
                get_processed_data=pd.DataFrame({"x": [1, 2], "y": [3, 4]})
            ),
            plot_type="scatter",
            plot_params={"x": "{{x_col}}", "y": "y"},
            controls={"x_col": Control(component=dbc.Select, props={"options": []})},
        )

        fig = chart.get_figure(params={"x_col": "x"})

        assert isinstance(fig, go.Figure)

    def test_color_passthrough_to_plot_function(self, datasource_factory, mock_plot_fn):
        """Test that color parameter is passed to plot function."""
        df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6], "color": ["A", "B", "C"]})
        mock_ds = datasource_factory(get_processed_data=df)

        chart = TypedChartBlock(
            block_id="test_color",
            datasource=mock_ds,
            plot_type="test_mock_plot",
            plot_params={"x": "x", "y": "y", "color": "color"},
            plot_kwargs={"title": "Color Test"},
        )

        # Call _update_chart to trigger plot function
        chart._update_chart()

        # Verify plot function was called with color parameter
        mock_plot_fn.assert_called_once()
        call_args = mock_plot_fn.call_args
        assert "color" in call_args.kwargs
        assert call_args.kwargs["color"] == "color"
        assert "title" in call_args.kwargs
        assert call_args.kwargs["title"] == "Color Test"

    def test_initial_render_with_control_defaults(
        self, datasource_factory, mock_plot_fn
    ):
        """Test that initial render uses control default values."""
        df = pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})
        mock_ds = datasource_factory(get_processed_data=df)

        controls = {
            "x_col": Control(
                component=dcc.Dropdown, props={"options": ["x", "y"], "value": "x"}
            ),
            "y_col": Control(
                component=dcc.Dropdown, props={"options": ["x", "y"], "value": "y"}
            ),
        }

        chart = TypedChartBlock(
            block_id="test_defaults",
            datasource=mock_ds,
            plot_type="test_mock_plot",
            plot_params={"x": "{{x_col}}", "y": "{{y_col}}"},
            controls=controls,
        )

        # Call layout() which should use control defaults
        layout = chart.layout()

        # Verify plot function was called with resolved defaults
        mock_plot_fn.assert_called_once()
        call_args = mock_plot_fn.call_args
        assert call_args.kwargs["x"] == "x"  # Resolved from control default
        assert call_args.kwargs["y"] == "y"  # Resolved from control default
