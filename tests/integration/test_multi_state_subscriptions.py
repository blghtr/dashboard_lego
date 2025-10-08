"""
Integration tests for multi-state subscription feature.

:hierarchy: [Testing | Integration Tests | Multi-State Subscription]
:relates-to:
 - motivated_by: "Bug Fix: Support subscribing to multiple states to enable
   complex dashboard patterns with multi-filter dependencies"
 - implements: "integration_tests: 'multi_state_subscription'"
 - uses: ["class: 'InteractiveChartBlock'", "class: 'StaticChartBlock'",
          "class: 'KPIBlock'", "class: 'StateManager'", "class: 'DashboardPage'"]

:rationale: "Comprehensive integration tests ensure multi-state subscription
 works correctly across the entire dashboard pipeline."
:contract:
 - pre: "Multiple publisher blocks exist with different controls."
 - post: "Subscriber blocks correctly respond to changes from multiple states."

"""

import pandas as pd
import plotly.graph_objects as go
import pytest
from dash import dcc

from dashboard_lego.blocks.chart import Control, InteractiveChartBlock, StaticChartBlock
from dashboard_lego.blocks.kpi import KPIBlock
from dashboard_lego.blocks.text import TextBlock
from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.core.page import DashboardPage
from dashboard_lego.core.state import StateManager


class SimpleDataSource(BaseDataSource):
    """Simple datasource for testing."""

    def __init__(self):
        super().__init__()

    def _load_data(self, params: dict) -> pd.DataFrame:
        """Return test data."""
        return pd.DataFrame({"value": [1, 2, 3], "category": ["A", "B", "C"]})

    def get_kpis(self) -> dict:
        """Return test KPIs."""
        if self._data is None:
            return {}
        return {"total": self._data["value"].sum()}

    def get_summary(self) -> str:
        """Return test summary."""
        return "Test summary"

    def get_filter_options(self, filter_name: str) -> list:
        """Return empty list for filter options."""
        return []


def test_multi_state_subscription_integration(datasource_factory):
    """
    Integration test for multi-state subscription across multiple blocks.

    :hierarchy: [Testing | Integration Tests | Multi-State | Full Workflow]
    :covers:
     - object: "Full multi-state subscription workflow"
     - requirement: "Bug Fix: Blocks should subscribe to multiple states"

    :scenario: "Creates a dashboard with multiple publishers and a subscriber
     that listens to all of them, verifying state registration works correctly."
    :strategy: "Use StateManager to verify all subscriptions are registered."
    :contract:
     - pre: "Multiple InteractiveChartBlocks publish different states."
     - post: "StaticChartBlock subscribes to all publisher states."

    """
    datasource = SimpleDataSource()

    # Create two publisher blocks
    filter_block_1 = InteractiveChartBlock(
        block_id="filter1",
        datasource=datasource,
        title="Filter 1",
        chart_generator=lambda df, ctx: go.Figure(),
        controls={
            "control_a": Control(
                component=dcc.Dropdown, props={"options": ["A", "B"], "value": "A"}
            ),
        },
    )

    filter_block_2 = InteractiveChartBlock(
        block_id="filter2",
        datasource=datasource,
        title="Filter 2",
        chart_generator=lambda df, ctx: go.Figure(),
        controls={
            "control_b": Control(
                component=dcc.Slider, props={"min": 0, "max": 10, "value": 5}
            ),
        },
    )

    # Create a subscriber block that listens to BOTH filters
    chart_block = StaticChartBlock(
        block_id="my_chart",
        datasource=datasource,
        title="Dependent Chart",
        chart_generator=lambda df, ctx: go.Figure(),
        subscribes_to=["filter1-control_a", "filter2-control_b"],
    )

    # Register with StateManager
    state_manager = StateManager()
    filter_block_1._register_state_interactions(state_manager)
    filter_block_2._register_state_interactions(state_manager)
    chart_block._register_state_interactions(state_manager)

    # Verify publishers were registered
    assert "filter1-control_a" in state_manager.dependency_graph
    assert "filter2-control_b" in state_manager.dependency_graph

    # Verify chart subscribes to both states
    subscribers_1 = state_manager.dependency_graph["filter1-control_a"]["subscribers"]
    subscribers_2 = state_manager.dependency_graph["filter2-control_b"]["subscribers"]

    # Both states should have the chart as a subscriber
    chart_ids = [sub["component_id"] for sub in subscribers_1]
    assert "my_chart-container" in chart_ids

    chart_ids = [sub["component_id"] for sub in subscribers_2]
    assert "my_chart-container" in chart_ids


def test_kpi_subscribes_to_multiple_filters(datasource_factory):
    """
    Test KPIBlock subscribing to multiple filter states.

    :hierarchy: [Testing | Integration Tests | Multi-State | KPI]
    :covers:
     - object: "KPIBlock multi-state subscription"
     - requirement: "Bug Fix: KPIBlock should react to multiple filters"

    :scenario: "KPIBlock subscribes to multiple interactive chart controls."
    :strategy: "Verify KPI updates when any of the subscribed states change."
    :contract:
     - pre: "Multiple control states exist."
     - post: "KPIBlock subscribes to all specified controls."

    """
    datasource = SimpleDataSource()

    filter_block = InteractiveChartBlock(
        block_id="filters",
        datasource=datasource,
        title="Filters",
        chart_generator=lambda df, ctx: go.Figure(),
        controls={
            "region": Control(
                component=dcc.Dropdown,
                props={"options": ["North", "South"], "value": "North"},
            ),
            "date_range": Control(
                component=dcc.Slider, props={"min": 1, "max": 12, "value": 6}
            ),
        },
    )

    # KPI block subscribes to both controls
    kpi_block = KPIBlock(
        block_id="kpis",
        datasource=datasource,
        kpi_definitions=[{"key": "total", "title": "Total"}],
        subscribes_to=["filters-region", "filters-date_range"],
    )

    # Register with StateManager
    state_manager = StateManager()
    filter_block._register_state_interactions(state_manager)
    kpi_block._register_state_interactions(state_manager)

    # Verify KPI subscribes to both controls
    region_subscribers = state_manager.dependency_graph["filters-region"]["subscribers"]
    date_subscribers = state_manager.dependency_graph["filters-date_range"][
        "subscribers"
    ]

    kpi_component_ids = [sub["component_id"] for sub in region_subscribers]
    assert "kpis-container" in kpi_component_ids

    kpi_component_ids = [sub["component_id"] for sub in date_subscribers]
    assert "kpis-container" in kpi_component_ids


def test_text_block_subscribes_to_multiple_states(datasource_factory):
    """
    Test TextBlock subscribing to multiple states.

    :hierarchy: [Testing | Integration Tests | Multi-State | TextBlock]
    :covers:
     - object: "TextBlock multi-state subscription"
     - requirement: "Bug Fix: TextBlock should react to multiple filters"

    :scenario: "TextBlock subscribes to multiple control states."
    :strategy: "Verify TextBlock subscription registration works correctly."
    :contract:
     - pre: "Multiple control states exist."
     - post: "TextBlock subscribes to all specified controls."

    """
    datasource = SimpleDataSource()

    filter_block = InteractiveChartBlock(
        block_id="controls",
        datasource=datasource,
        title="Controls",
        chart_generator=lambda df, ctx: go.Figure(),
        controls={
            "filter_a": Control(
                component=dcc.Dropdown, props={"options": ["X", "Y"], "value": "X"}
            ),
            "filter_b": Control(
                component=dcc.Dropdown, props={"options": ["1", "2"], "value": "1"}
            ),
        },
    )

    # TextBlock subscribes to both controls
    text_block = TextBlock(
        block_id="summary",
        datasource=datasource,
        subscribes_to=["controls-filter_a", "controls-filter_b"],
        content_generator=lambda df: "Summary text",
    )

    # Register with StateManager
    state_manager = StateManager()
    filter_block._register_state_interactions(state_manager)
    text_block._register_state_interactions(state_manager)

    # Verify TextBlock subscribes to both controls
    filter_a_subscribers = state_manager.dependency_graph["controls-filter_a"][
        "subscribers"
    ]
    filter_b_subscribers = state_manager.dependency_graph["controls-filter_b"][
        "subscribers"
    ]

    text_component_ids = [sub["component_id"] for sub in filter_a_subscribers]
    assert "summary-container" in text_component_ids

    text_component_ids = [sub["component_id"] for sub in filter_b_subscribers]
    assert "summary-container" in text_component_ids


def test_interactive_chart_with_external_and_own_states(datasource_factory, mocker):
    """
    Test InteractiveChartBlock subscribing to external states AND its own controls.

    :hierarchy: [Testing | Integration Tests | Multi-State | Interactive]
    :covers:
     - object: "InteractiveChartBlock with external and own subscriptions"
     - requirement: "Bug Fix: Interactive chart should handle both external
       and internal state subscriptions"

    :scenario: "InteractiveChartBlock has its own controls AND subscribes to
     external filter states."
    :strategy: "Verify block subscribes to both external states and own controls."
    :contract:
     - pre: "External states and own controls exist."
     - post: "Block subscribes to all states (external + own)."

    """
    datasource = SimpleDataSource()

    # External filter block
    external_filter = InteractiveChartBlock(
        block_id="external",
        datasource=datasource,
        title="External Filter",
        chart_generator=lambda df, ctx: go.Figure(),
        controls={
            "category": Control(
                component=dcc.Dropdown, props={"options": ["A", "B"], "value": "A"}
            ),
        },
    )

    # Interactive chart with its own controls AND subscribing to external filter
    interactive_chart = InteractiveChartBlock(
        block_id="chart",
        datasource=datasource,
        title="Chart with Controls",
        chart_generator=lambda df, ctx: go.Figure(),
        controls={
            "metric": Control(
                component=dcc.Dropdown,
                props={"options": ["sales", "profit"], "value": "sales"},
            ),
        },
        subscribes_to="external-category",  # Subscribe to external state
    )

    # Register with StateManager
    state_manager = StateManager()
    external_filter._register_state_interactions(state_manager)
    interactive_chart._register_state_interactions(state_manager)

    # Verify subscriptions are set up correctly
    assert len(interactive_chart.subscribes) == 2  # 1 external + 1 own
    assert "external-category" in interactive_chart.subscribes
    assert "chart-metric" in interactive_chart.subscribes

    # Verify external state has the chart as subscriber
    external_subscribers = state_manager.dependency_graph["external-category"][
        "subscribers"
    ]
    chart_ids = [sub["component_id"] for sub in external_subscribers]
    assert "chart-container" in chart_ids

    # Verify chart's own control is also registered
    assert "chart-metric" in state_manager.dependency_graph
    own_subscribers = state_manager.dependency_graph["chart-metric"]["subscribers"]
    chart_ids = [sub["component_id"] for sub in own_subscribers]
    assert "chart-container" in chart_ids


def test_interactive_chart_refreshes_datasource_with_all_states(mocker):
    """
    Verify InteractiveChartBlock calls datasource.init_data with all states.

    :hierarchy: [Testing | Integration Tests | Multi-State | DataSource Refresh]
    :covers:
     - object: "InteractiveChartBlock._update_chart"
     - requirement: "Bug Fix: InteractiveChartBlock must propagate external state to DataSource"

    :scenario: "An InteractiveChartBlock subscribes to an external filter. When the
     external filter's value is passed to _update_chart, the block should call
     datasource.init_data with both the external and its own internal control values."
    :strategy: "Mocker is used to spy on datasource.init_data and assert it was
     called with the expected combined parameters."
    :contract:
     - pre: "Block subscribes to 'external-state' and has its own 'internal-state'."
     - post: "datasource.init_data is called with {'external-state': 'ext_val', 'chart-internal-state': 'int_val'}."
    """
    # 1. Setup
    datasource = SimpleDataSource()
    mock_init_data = mocker.spy(datasource, "init_data")

    chart = InteractiveChartBlock(
        block_id="chart",
        datasource=datasource,
        title="Test Chart",
        chart_generator=lambda df, ctx: go.Figure(),
        controls={
            "internal-state": Control(component=dcc.Input, props={"value": "int_val"})
        },
        subscribes_to="external-state",
    )

    # Manually register state to populate `chart.subscribes`
    state_manager = StateManager()
    chart._register_state_interactions(state_manager)

    # The order of inputs is external, then internal
    # Dash will call the callback with positional args in this order
    callback_args = ("ext_val", "int_val")

    # 2. Action
    chart._update_chart(*callback_args)

    # 3. Verification
    expected_params = {
        "external-state": "ext_val",
        "chart-internal-state": "int_val",
    }
    mock_init_data.assert_called_once_with(expected_params)

    def test_interactive_chart_with_external_and_own_states(datasource_factory, mocker):
        """
        Test InteractiveChartBlock subscribing to external states AND its own controls.

        :hierarchy: [Testing | Integration Tests | Multi-State | Interactive]
        :covers:
         - object: "InteractiveChartBlock with external and own subscriptions"
         - requirement: "Bug Fix: Interactive chart should handle both external
           and internal state subscriptions"

        :scenario: "InteractiveChartBlock has its own controls AND subscribes to
         external filter states."
        :strategy: "Verify block subscribes to both external states and own controls."
        :contract:
         - pre: "External states and own controls exist."
         - post: "Block subscribes to all states (external + own)."

        """
        datasource = SimpleDataSource()

        # External filter block
        external_filter = InteractiveChartBlock(
            block_id="external",
            datasource=datasource,
            title="External Filter",
            chart_generator=lambda df, ctx: go.Figure(),
            controls={
                "category": Control(
                    component=dcc.Dropdown, props={"options": ["A", "B"], "value": "A"}
                ),
            },
        )

        # Interactive chart with its own controls AND subscribing to external filter
        interactive_chart = InteractiveChartBlock(
            block_id="chart",
            datasource=datasource,
            title="Chart with Controls",
            chart_generator=lambda df, ctx: go.Figure(),
            controls={
                "metric": Control(
                    component=dcc.Dropdown,
                    props={"options": ["sales", "profit"], "value": "sales"},
                ),
            },
            subscribes_to="external-category",  # Subscribe to external state
        )

        # Register with StateManager
        state_manager = StateManager()
        external_filter._register_state_interactions(state_manager)
        interactive_chart._register_state_interactions(state_manager)

        # Verify subscriptions are set up correctly
        assert len(interactive_chart.subscribes) == 2  # 1 external + 1 own
        assert "external-category" in interactive_chart.subscribes
        assert "chart-metric" in interactive_chart.subscribes

        # Verify external state has the chart as subscriber
        external_subscribers = state_manager.dependency_graph["external-category"][
            "subscribers"
        ]
        chart_ids = [sub["component_id"] for sub in external_subscribers]
        assert "chart-container" in chart_ids

        # Verify chart's own control is also registered
        assert "chart-metric" in state_manager.dependency_graph
        own_subscribers = state_manager.dependency_graph["chart-metric"]["subscribers"]
        chart_ids = [sub["component_id"] for sub in own_subscribers]
        assert "chart-container" in chart_ids
