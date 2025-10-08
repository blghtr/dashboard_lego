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
            "dropdown": Control(
                component=dcc.Dropdown, props={"options": ["a", "b"], "value": "a"}
            ),
            "slider": Control(
                component=dcc.Slider, props={"min": 0, "max": 10, "value": 5}
            ),
        }

    def test_layout(self, datasource_factory, controls):
        mock_ds = datasource_factory()
        block = InteractiveChartBlock(
            "interactive",
            mock_ds,
            "Interactive Chart",
            lambda df, ctx: go.Figure(),
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

        # Simulate callback context with control values from layout()
        figure = block._update_chart(**{"dropdown": "a", "slider": 5})

        # Check that the function was called with ChartContext
        mock_plot_fn.assert_called_once()
        call_args = mock_plot_fn.call_args
        assert call_args[0][0].equals(df)
        assert hasattr(call_args[0][1], "datasource")
        assert call_args[0][1].controls == {"dropdown": "a", "slider": 5}

    def test_state_registration(self, datasource_factory, controls):
        mock_ds = datasource_factory()
        block = InteractiveChartBlock(
            "interactive", mock_ds, "My Chart", lambda df, ctx: go.Figure(), controls
        )
        state_manager = StateManager()
        block._register_state_interactions(state_manager)

        # Check publishers
        assert "interactive-dropdown" in state_manager.dependency_graph
        # In non-navigation mode, ID should be a simple string
        assert (
            state_manager.dependency_graph["interactive-dropdown"]["publisher"][
                "component_id"
            ]
            == "interactive-dropdown"
        )
        assert "interactive-slider" in state_manager.dependency_graph

        # Check subscribers
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

    @pytest.mark.parametrize(
        "call_type, call_args, call_kwargs",
        [
            (
                "callback_args",
                ["ext_val", "a", 5],  # Simulates *args from StateManager
                {},
            ),
            (
                "layout_kwargs",
                [],
                {"dropdown": "a", "slider": 5},  # Simulates **kwargs from layout()
            ),
        ],
    )
    def test_update_chart_handles_both_arg_and_kwarg_calls(
        self,
        datasource_factory,
        controls,
        mock_plot_fn,
        call_type,
        call_args,
        call_kwargs,
    ):
        """Verify _update_chart works correctly with both *args and **kwargs."""
        # Provide a non-empty dataframe to the mock datasource
        mock_ds = datasource_factory(get_processed_data=pd.DataFrame({"a": [1]}))
        block = InteractiveChartBlock(
            "interactive",
            mock_ds,
            "My Chart",
            mock_plot_fn,
            controls,
            subscribes_to=["external-state"],
        )
        # This step is crucial to populate the self.subscribes dict for the *args mapping
        block._register_state_interactions(StateManager())

        # Simulate the call
        block._update_chart(*call_args, **call_kwargs)

        # Verify datasource was refreshed with all available state values
        mock_ds.init_data.assert_called_once()
        params_sent_to_datasource = mock_ds.init_data.call_args[0][0]

        if call_type == "callback_args":
            # For *args, params should include all subscribed states
            assert params_sent_to_datasource == {
                "external-state": "ext_val",
                "interactive-dropdown": "a",
                "interactive-slider": 5,
            }
        else:  # layout_kwargs
            # For **kwargs, params are the block's own controls with full state IDs
            assert params_sent_to_datasource == {
                "interactive-dropdown": "a",
                "interactive-slider": 5,
            }

        # Verify the chart generator was called with the correct context
        mock_plot_fn.assert_called_once()
        call_args_to_generator = mock_plot_fn.call_args
        chart_context = call_args_to_generator[0][1]

        # The ChartContext should only contain the block's own control values
        assert chart_context.controls == {"dropdown": "a", "slider": 5}


class TestMultiStateSubscription:
    """
    Tests for multi-state subscription feature.

    :hierarchy: [Testing | Unit Tests | Blocks | Multi-State Subscription]
    :covers:
     - object: "BaseBlock._normalize_subscribes_to"
     - object: "StaticChartBlock with list subscription"
     - object: "InteractiveChartBlock with list subscription"
     - requirement: "Bug Fix: Support subscribing to multiple states"

    :scenario: "Verifies that blocks can subscribe to multiple states using
     a list parameter without causing TypeError."
    :strategy: "Create blocks with list subscription parameters and verify
     state registration occurs correctly for all states."
    :contract:
     - pre: "subscribes_to accepts both str and List[str] types."
     - post: "Block subscribes to all specified states successfully."

    """

    def test_static_chart_list_subscription(self, datasource_factory):
        """Test StaticChartBlock with list of state IDs."""
        mock_ds = datasource_factory()
        state_ids = ["filter-state-1", "filter-state-2"]

        # This should not raise TypeError
        block = StaticChartBlock(
            "test_chart",
            mock_ds,
            "My Chart",
            lambda df, ctx: go.Figure(),
            subscribes_to=state_ids,
        )

        # Verify subscribes dict was created correctly
        assert block.subscribes is not None
        assert len(block.subscribes) == 2
        assert "filter-state-1" in block.subscribes
        assert "filter-state-2" in block.subscribes
        assert block.subscribes["filter-state-1"] == block._update_chart
        assert block.subscribes["filter-state-2"] == block._update_chart

    def test_static_chart_single_string_subscription(self, datasource_factory):
        """Test StaticChartBlock still works with single string (regression)."""
        mock_ds = datasource_factory()

        block = StaticChartBlock(
            "test_chart",
            mock_ds,
            "My Chart",
            lambda df, ctx: go.Figure(),
            subscribes_to="single-state",
        )

        # Verify subscribes dict was created correctly
        assert block.subscribes is not None
        assert len(block.subscribes) == 1
        assert "single-state" in block.subscribes

    def test_interactive_chart_list_subscription(self, datasource_factory, mocker):
        """Test InteractiveChartBlock with list of external state IDs."""
        mock_ds = datasource_factory()
        controls = {
            "my_control": Control(
                component=dcc.Dropdown, props={"options": ["a", "b"]}
            ),
        }
        external_states = ["external-state-1", "external-state-2"]

        # This should not raise TypeError: can only concatenate str (not "list")
        block = InteractiveChartBlock(
            "interactive",
            mock_ds,
            "Interactive Chart",
            lambda df, ctx: go.Figure(),
            controls=controls,
            subscribes_to=external_states,
        )

        # Manually register state to populate subscribes list
        mock_state_manager = mocker.MagicMock(spec=StateManager)
        block._register_state_interactions(mock_state_manager)

        # Verify subscribes includes both external states and own control
        assert block.subscribes is not None
        assert len(block.subscribes) == 3  # 2 external + 1 own control

    def test_interactive_chart_string_subscription(self, datasource_factory, mocker):
        """Test InteractiveChartBlock with single string (regression)."""
        mock_ds = datasource_factory()
        controls = {
            "my_control": Control(
                component=dcc.Dropdown, props={"options": ["a", "b"]}
            ),
        }

        # This should work without errors
        block = InteractiveChartBlock(
            "interactive",
            mock_ds,
            "Interactive Chart",
            lambda df, ctx: go.Figure(),
            controls=controls,
            subscribes_to="external-state",
        )

        # Manually register state to populate subscribes list
        mock_state_manager = mocker.MagicMock(spec=StateManager)
        block._register_state_interactions(mock_state_manager)

        # Verify subscribes includes both external state and own control
        assert block.subscribes is not None
        assert len(block.subscribes) == 2  # 1 external + 1 own control

    def test_interactive_chart_none_subscription(self, datasource_factory, mocker):
        """Test InteractiveChartBlock with None (only own controls)."""
        mock_ds = datasource_factory()
        controls = {
            "my_control": Control(
                component=dcc.Dropdown, props={"options": ["a", "b"]}
            ),
        }

        block = InteractiveChartBlock(
            "interactive",
            mock_ds,
            "Interactive Chart",
            lambda df, ctx: go.Figure(),
            controls=controls,
            subscribes_to=None,
        )

        # Manually register state to populate subscribes list
        mock_state_manager = mocker.MagicMock(spec=StateManager)
        block._register_state_interactions(mock_state_manager)

        # Verify subscribes includes only own control
        assert block.subscribes is not None
        assert len(block.subscribes) == 1

    def test_multi_state_registration(self, datasource_factory):
        """Test that multiple states register correctly with StateManager."""
        mock_ds = datasource_factory()
        state_ids = ["state-a", "state-b", "state-c"]

        block = StaticChartBlock(
            "test_chart",
            mock_ds,
            "My Chart",
            lambda df, ctx: go.Figure(),
            subscribes_to=state_ids,
        )

        state_manager = StateManager()
        block._register_state_interactions(state_manager)

        # Verify all states are registered
        for state_id in state_ids:
            assert state_id in state_manager.dependency_graph
            subscribers = state_manager.dependency_graph[state_id]["subscribers"]
            assert len(subscribers) == 1
            assert subscribers[0]["callback_fn"] == block._update_chart
            assert subscribers[0]["component_id"] == "test_chart-container"
