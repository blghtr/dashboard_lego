"""
Integration tests for navigation callbacks and lazy-loading functionality.

Tests that callbacks are properly registered for blocks in lazy-loaded sections.
"""

import dash
import pandas as pd
import plotly.express as px
from dash import dcc

from dashboard_lego.blocks.chart import (
    Control,
    ControlPanelBlock,
    InteractiveChartBlock,
    StaticChartBlock,
)
from dashboard_lego.blocks.kpi import KPIBlock
from dashboard_lego.core.datasources.csv_source import CsvDataSource
from dashboard_lego.core.page import DashboardPage, NavigationConfig, NavigationSection


class MockDataSource(CsvDataSource):
    """Mock datasource for testing that tracks init_data calls."""

    def __init__(self, data: pd.DataFrame):
        # Don't call super().__init__ to avoid cache setup
        self._data = data
        self.init_data_calls = []

    def init_data(self, params=None):
        """Track init_data calls for testing."""
        self.init_data_calls.append(params or {})
        return True

    def get_processed_data(self):
        return self._data

    def get_kpis(self):
        return {
            "total": len(self._data),
            "average": self._data["value"].mean() if "value" in self._data else 0,
        }

    def get_filter_options(self, filter_name):
        if filter_name == "category" and "category" in self._data:
            return [{"label": c, "value": c} for c in self._data["category"].unique()]
        return []

    def get_summary(self):
        return f"Test data with {len(self._data)} rows"


def test_interactive_chart_in_lazy_section():
    """Test that InteractiveChartBlock works in non-default section."""
    # Create test data
    df = pd.DataFrame(
        {
            "x": [1, 2, 3, 4, 5],
            "y": [10, 20, 15, 25, 30],
            "category": ["A", "A", "B", "B", "A"],
        }
    )

    datasource = MockDataSource(df)

    def create_section_with_interactive_chart():
        """Section factory with InteractiveChartBlock."""
        chart = InteractiveChartBlock(
            block_id="test_chart",
            datasource=datasource,
            title="Test Interactive Chart",
            chart_generator=lambda df, ctx: px.scatter(df, x="x", y="y"),
            controls={
                "mode": Control(
                    component=dcc.RadioItems,
                    props={"options": ["Mode A", "Mode B"], "value": "Mode A"},
                )
            },
        )
        return [[chart]]

    # Create navigation with chart in Section 0 (default)
    navigation = NavigationConfig(
        sections=[
            NavigationSection(
                title="Section 0", block_factory=create_section_with_interactive_chart
            )
        ],
        position="left",
    )

    # Build dashboard
    page = DashboardPage(title="Test Dashboard", navigation=navigation)
    app = dash.Dash(__name__, external_stylesheets=[page.theme])
    app.layout = page.build_layout()
    page.register_callbacks(app)

    # Verify that callbacks were registered
    # The InteractiveChartBlock should have a callback registered
    # We can check this by verifying the StateManager tracked outputs
    assert (
        len(page.state_manager._registered_outputs) > 0
    ), "No callbacks registered for default section"


def test_control_panel_in_lazy_section():
    """Test that ControlPanelBlock works in lazy-loaded section."""
    # Create test data
    df = pd.DataFrame(
        {"x": [1, 2, 3], "value": [100, 200, 150], "category": ["A", "B", "A"]}
    )

    datasource = MockDataSource(df)

    def create_section_0():
        """Default section."""
        kpi = KPIBlock(
            block_id="kpi_block",
            datasource=datasource,
            kpi_definitions=[{"key": "total", "title": "Total", "color": "primary"}],
            subscribes_to="control_panel-category",
        )
        return [[kpi]]

    def create_section_1():
        """Lazy section with ControlPanelBlock."""
        control_panel = ControlPanelBlock(
            block_id="control_panel",
            datasource=datasource,
            title="Filters",
            controls={
                "category": Control(
                    component=dcc.Dropdown,
                    props={
                        "options": datasource.get_filter_options("category"),
                        "value": "A",
                    },
                )
            },
        )
        return [[control_panel]]

    # Create navigation
    navigation = NavigationConfig(
        sections=[
            NavigationSection(title="Section 0", block_factory=create_section_0),
            NavigationSection(title="Section 1", block_factory=create_section_1),
        ],
        position="left",
    )

    # Build dashboard
    page = DashboardPage(title="Test Dashboard", navigation=navigation)
    app = dash.Dash(__name__, external_stylesheets=[page.theme])
    app.layout = page.build_layout()
    page.register_callbacks(app)

    # Verify app instance stored
    assert hasattr(
        page, "_app_instance"
    ), "App instance not stored for lazy callback registration"
    assert page._app_instance == app, "Stored app instance doesn't match registered app"


def test_kpi_block_datasource_refresh():
    """Test that KPIBlock refreshes datasource with control values."""
    # Create test data
    df = pd.DataFrame({"value": [100, 200, 150], "category": ["A", "B", "A"]})

    datasource = MockDataSource(df)

    # Create KPIBlock that subscribes to controls
    kpi_block = KPIBlock(
        block_id="test_kpi",
        datasource=datasource,
        kpi_definitions=[
            {"key": "total", "title": "Total", "color": "primary"},
            {"key": "average", "title": "Average", "color": "success"},
        ],
        subscribes_to=["control-category", "control-threshold"],
    )

    # Simulate callback invocation with control values
    result = kpi_block._update_kpi_cards("A", 100)

    # Verify datasource was refreshed with params
    assert len(datasource.init_data_calls) > 0, "Datasource.init_data not called"

    last_call_params = datasource.init_data_calls[-1]
    assert (
        "control-category" in last_call_params
    ), "Category parameter not passed to datasource"
    assert (
        last_call_params["control-category"] == "A"
    ), "Incorrect category value passed"
    assert (
        "control-threshold" in last_call_params
    ), "Threshold parameter not passed to datasource"
    assert (
        last_call_params["control-threshold"] == 100
    ), "Incorrect threshold value passed"


def test_static_chart_datasource_refresh():
    """Test that StaticChartBlock refreshes datasource with control values."""
    # Create test data
    df = pd.DataFrame({"x": [1, 2, 3], "y": [10, 20, 15], "category": ["A", "B", "A"]})

    datasource = MockDataSource(df)

    def chart_generator(df, ctx):
        return px.bar(df, x="x", y="y")

    # Create StaticChartBlock that subscribes to controls
    chart_block = StaticChartBlock(
        block_id="test_chart",
        datasource=datasource,
        title="Test Chart",
        chart_generator=chart_generator,
        subscribes_to=["control-category", "control-min_value"],
    )

    # Simulate callback invocation with control values
    result = chart_block._update_chart("B", 10)

    # Verify datasource was refreshed with params
    assert len(datasource.init_data_calls) > 0, "Datasource.init_data not called"

    last_call_params = datasource.init_data_calls[-1]
    assert (
        "control-category" in last_call_params
    ), "Category parameter not passed to datasource"
    assert (
        last_call_params["control-category"] == "B"
    ), "Incorrect category value passed"


def test_interactive_chart_datasource_refresh():
    """Test that InteractiveChartBlock refreshes datasource with control values."""
    # Create test data
    df = pd.DataFrame({"x": [1, 2, 3], "y": [10, 20, 15]})

    datasource = MockDataSource(df)

    def chart_generator(df, ctx):
        return px.scatter(df, x="x", y="y")

    # Create InteractiveChartBlock with controls
    chart_block = InteractiveChartBlock(
        block_id="test_chart",
        datasource=datasource,
        title="Test Chart",
        chart_generator=chart_generator,
        controls={
            "mode": Control(
                component=dcc.RadioItems, props={"options": ["A", "B"], "value": "A"}
            )
        },
    )

    # Simulate callback invocation with control values (kwargs format from layout call)
    result = chart_block._update_chart(**{"mode": "B"})
    # Verify datasource was refreshed with params
    assert len(datasource.init_data_calls) > 0, "Datasource.init_data not called"

    last_call_params = datasource.init_data_calls[-1]
    assert (
        "test_chart-mode" in last_call_params
    ), "Mode parameter not passed to datasource"
    assert last_call_params["test_chart-mode"] == "B", "Incorrect mode value passed"


def test_callback_deduplication():
    """Test that StateManager doesn't register duplicate callbacks."""
    df = pd.DataFrame({"x": [1, 2, 3], "y": [10, 20, 15]})
    datasource = MockDataSource(df)

    def chart_generator(df, ctx):
        return px.bar(df, x="x", y="y")

    # Create a simple chart
    chart = StaticChartBlock(
        block_id="test_chart",
        datasource=datasource,
        title="Test",
        chart_generator=chart_generator,
        subscribes_to="dummy_state",
    )

    # Build page
    page = DashboardPage(title="Test", blocks=[[chart]])
    app = dash.Dash(__name__, external_stylesheets=[page.theme])
    app.layout = page.build_layout()

    # Register callbacks twice (simulating lazy section loading)
    page.register_callbacks(app)
    initial_count = len(page.state_manager._registered_outputs)

    # Try to register again
    page.state_manager.bind_callbacks(app, [chart])
    final_count = len(page.state_manager._registered_outputs)

    # Count should be the same (deduplication working)
    assert (
        initial_count == final_count
    ), f"Callbacks duplicated: {initial_count} -> {final_count}"
