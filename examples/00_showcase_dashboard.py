"""
v0.15 Showcase Dashboard - Comprehensive Feature Demonstration

Demonstrates:
- Navigation with multiple sections
- Theme selection via CLI (--theme light|dark|lux|cyborg)
- v0.15 composition pattern (DataBuilder + DataTransformer)
- **NEW v0.15: Collapsible Sidebar with global transforms**
- **NEW v0.15: Adaptive layout - sidebar pushes content (desktop/mobile)**
- **NEW v0.15: Block-level data transformations (transform_fn)**
- **NEW v0.15: MetricsBlock with dynamic responsive sizing**
- EDA and ML presets
- Various layouts and blocks
- Interactive controls with state management
- Cross-section State() subscriptions via sidebar

Usage:
    python examples/00_showcase_dashboard.py --theme lux
    python examples/00_showcase_dashboard.py --theme dark
    uv run python examples/00_showcase_dashboard.py --theme cyborg
"""

import argparse
import os

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc

from dashboard_lego.blocks import get_metric_row
from dashboard_lego.blocks.control_panel import ControlPanelBlock
from dashboard_lego.blocks.typed_chart import Control, TypedChartBlock
from dashboard_lego.core import (
    DashboardPage,
    DataBuilder,
    DataSource,
    DataTransformer,
    NavigationConfig,
    NavigationSection,
    ThemeConfig,
)
from dashboard_lego.core.sidebar import SidebarConfig
from dashboard_lego.presets.eda_presets import (
    BoxPlotPreset,
    CorrelationHeatmapPreset,
    GroupedHistogramPreset,
    KneePlotPreset,
    MissingValuesPreset,
)
from dashboard_lego.presets.layouts import kpi_row_top
from dashboard_lego.utils.logger import setup_logging
from dashboard_lego.utils.plot_registry import register_plot_type

# Setup debug logging
setup_logging(level="DEBUG")


# ============================================================================
# Custom Plot Functions
# ============================================================================


def plot_revenue_by_date(df, x="Date", y="Revenue", **kwargs):
    """Plot revenue grouped by date."""
    if df.empty or y not in df.columns:
        return go.Figure().add_annotation(
            text=f"Column {y} not found",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )
    grouped = df.groupby(x)[y].sum().reset_index()
    return px.line(grouped, x=x, y=y, **kwargs)


def plot_grouped_bar(df, x="Category", y="Revenue", **kwargs):
    """Plot grouped bar chart."""
    if df.empty or x not in df.columns or y not in df.columns:
        return go.Figure().add_annotation(
            text="Required columns not found",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )
    grouped = df.groupby(x)[y].sum().reset_index()
    return px.bar(grouped, x=x, y=y, **kwargs)


# Register custom plot types
register_plot_type("revenue_by_date", plot_revenue_by_date)
register_plot_type("grouped_bar", plot_grouped_bar)


# ============================================================================
# Utility: Sample Data Generation
# ============================================================================


def create_sample_data():
    """Generate sample sales data for demonstration."""
    import numpy as np

    np.random.seed(42)
    n = 200

    df = pd.DataFrame(
        {
            "Date": pd.date_range("2024-01-01", periods=n, freq="D"),
            "Product": np.random.choice(["Widget", "Gadget", "Tool", "Device"], n),
            "Category": np.random.choice(["Electronics", "Clothing", "Tools"], n),
            "Price": np.random.uniform(10, 500, n),
            "Quantity": np.random.randint(1, 20, n),
            "Cost": np.random.uniform(5, 250, n),
        }
    )

    # Add missing values (7% of data) for Data Quality Check demo
    missing_indices = np.random.choice(n, size=int(n * 0.07), replace=False)
    df.loc[missing_indices[:5], "Price"] = np.nan
    df.loc[missing_indices[5:10], "Quantity"] = np.nan
    df.loc[missing_indices[10:14], "Category"] = None

    file_path = "examples/sample_data.csv"
    df.to_csv(file_path, index=False)
    print(f"✓ Created sample data with missing values: {file_path}")
    return df


def ensure_sample_data():
    """Ensure sample data exists."""
    file_path = "examples/sample_data.csv"
    if not os.path.exists(file_path):
        print(f"Sample data not found at {file_path}, creating...")
        create_sample_data()
    return file_path


# ============================================================================
# Section 1: Data Pipeline (v0.15 Pattern)
# ============================================================================


class SalesDataBuilder(DataBuilder):
    """Build sales dataset with calculated fields."""

    def __init__(self, file_path, **kwargs):
        super().__init__(**kwargs)
        self.file_path = file_path

    def build(self, **params):
        """Load CSV and add Revenue, Profit, date fields."""
        df = pd.read_csv(self.file_path)

        # Add calculated fields
        if "Price" in df.columns and "Quantity" in df.columns:
            df["Revenue"] = df["Price"] * df["Quantity"]

        if "Revenue" in df.columns and "Cost" in df.columns:
            df["Profit"] = df["Revenue"] - df["Cost"]

        # Parse dates
        if "Date" in df.columns:
            df["Date"] = pd.to_datetime(df["Date"])
            df["Year"] = df["Date"].dt.year
            df["Month"] = df["Date"].dt.month

        return df


class SalesDataTransformer(DataTransformer):
    """Transform sales data by filtering category and price range."""

    def transform(self, data, **params):
        """
        Transform data by applying filters.

        Note: Parameters are already stripped of transform__ prefix by classifier.
        Use simple names: category, min_price (not transform__category, transform__min_price).
        """
        df = data.copy()

        # Category filter (parameter name is already stripped by classifier)
        if "category" in params:
            cat = params["category"]
            if cat and cat != "All":
                df = df[df["Category"] == cat]

        # Price filter (parameter name is already stripped by classifier)
        if "min_price" in params:
            min_p = params["min_price"]
            # Convert to float (dcc.Input returns string)
            try:
                min_p = float(min_p) if min_p not in (None, "", " ") else None
            except (ValueError, TypeError):
                min_p = None

            if min_p is not None and min_p > 0:
                df = df[df["Price"] >= min_p]

        return df


# ============================================================================
# Section 2: Navigation Sections
# ============================================================================


def create_overview_section():
    """Overview page with KPIs and summary charts."""

    # NEW v0.15: get_metric_row() factory pattern
    metrics_blocks, metrics_row_opts = get_metric_row(
        metrics_spec={
            "total_revenue": {
                "column": "Revenue",
                "agg": "sum",
                "title": "Total Revenue",
                "dtype": "float64",
                "color": "success",
            },
            "avg_price": {
                "column": "Price",
                "agg": "mean",
                "title": "Average Price",
                "color": "info",
            },
            "total_units": {
                "column": "Quantity",
                "agg": "sum",
                "title": "Units Sold",
                "color": "primary",
            },
        },
        datasource=datasource,
        subscribes_to=[
            "transforms-transform__category",
            "transforms-transform__min_price",
        ],
        block_id_prefix="overview_metric",
    )

    # Revenue trend chart (using custom plot function)
    trend_chart = TypedChartBlock(
        block_id="revenue_trend",
        datasource=datasource,
        plot_type="revenue_by_date",
        plot_params={"x": "Date", "y": "Revenue"},
        plot_kwargs={"title": "Revenue Trend Over Time"},
        title="Revenue Over Time",
        subscribes_to=[
            "transforms-transform__category",
            "transforms-transform__min_price",
        ],
    )

    # Category breakdown chart (using custom grouped plot)
    category_chart = TypedChartBlock(
        block_id="category_chart",
        datasource=datasource,
        plot_type="grouped_bar",
        plot_params={"x": "Category", "y": "Revenue"},
        plot_kwargs={"title": "Revenue by Category"},
        title="Category Breakdown",
        subscribes_to=[
            "transforms-transform__category",
            "transforms-transform__min_price",
        ],
    )

    # NEW v0.15: Block-specific transformation demo
    # This block aggregates sales by product (block-level transform)
    top_products = TypedChartBlock(
        block_id="top_products_agg",
        datasource=datasource,
        plot_type="bar",
        plot_params={"x": "Product", "y": "total_revenue"},
        plot_kwargs={"title": "Top Products (Aggregated)"},
        title="Top Products (Transform Demo)",
        subscribes_to=[
            "transforms-transform__category",
            "transforms-transform__min_price",
        ],
        # NEW: Block-level aggregation via transform_fn
        transform_fn=lambda df: df.groupby("Product")["Revenue"]
        .sum()
        .reset_index(name="total_revenue")
        .sort_values("total_revenue", ascending=False)
        .head(10),
    )

    return kpi_row_top(
        kpi_blocks=metrics_blocks,
        content_rows=[
            [trend_chart],
            [(category_chart, {"md": 6}), (top_products, {"md": 6})],
        ],
        kpi_row_options=metrics_row_opts,
    )


def create_eda_section():
    """EDA page showcasing preset blocks."""

    corr_heatmap = CorrelationHeatmapPreset(
        block_id="correlation",
        datasource=datasource,
        subscribes_to=[
            "transforms-transform__category",
            "transforms-transform__min_price",
        ],
        title="Feature Correlations",
    )

    histogram = GroupedHistogramPreset(
        block_id="distribution",
        datasource=datasource,
        subscribes_to=[
            "transforms-transform__category",
            "transforms-transform__min_price",
        ],
        title="Distribution Analysis",
    )

    missing_vals = MissingValuesPreset(
        block_id="missing",
        datasource=datasource,
        subscribes_to=[
            "transforms-transform__category",
            "transforms-transform__min_price",
        ],
        title="Data Quality Check",
    )

    boxplot = BoxPlotPreset(
        block_id="boxplot",
        datasource=datasource,
        subscribes_to=[
            "transforms-transform__category",
            "transforms-transform__min_price",
        ],
        title="Distribution Comparison",
    )

    # Create sample data for knee plot (k-means inertia)
    knee_data = pd.DataFrame(
        {"k": range(1, 11), "inertia": [100, 80, 60, 45, 35, 30, 28, 27, 26.5, 26]}
    )

    from dashboard_lego.core.data_transformer import DataTransformer
    from dashboard_lego.utils.quick_dashboard import InMemoryDataBuilder

    knee_datasource = DataSource(InMemoryDataBuilder(knee_data), DataTransformer())

    knee_plot = KneePlotPreset(
        block_id="knee_plot",
        datasource=knee_datasource,
        title="K-Means Elbow Analysis",
        controls=True,  # Show controls for demonstration
        x_col="k",  # Explicitly specify x column
        y_col="inertia",  # Explicitly specify y column
    )

    return [[corr_heatmap, histogram], [missing_vals, boxplot], [knee_plot]]


def create_analysis_section():
    """Analysis page with detailed views subscribing to sidebar transforms."""

    # Charts subscribe to sidebar transforms (using TypedChartBlock)
    scatter = TypedChartBlock(
        block_id="scatter",
        datasource=datasource,
        plot_type="scatter",
        plot_params={
            "x": "Price",
            "y": "Quantity",
            "color": "Category",
            "size": "Revenue",
        },
        plot_kwargs={"title": "Price vs Quantity Analysis", "hover_data": ["Product"]},
        title="Scatter Analysis",
        subscribes_to=[
            "transforms-transform__category",
            "transforms-transform__min_price",
        ],  # Subscribe to sidebar transforms
    )

    top_products = TypedChartBlock(
        block_id="top_products",
        datasource=datasource,
        plot_type="grouped_bar",
        plot_params={"x": "Product", "y": "Revenue"},
        plot_kwargs={"title": "Top Products by Revenue"},
        title="Top Products",
        subscribes_to=[
            "transforms-transform__category",
            "transforms-transform__min_price",
        ],  # Subscribe to sidebar transforms
    )

    # Return layout without control panel (now in sidebar)
    return [[scatter], [top_products]]


# ============================================================================
# Section 3: Dashboard Setup with Theme Selection
# ============================================================================


def get_theme_config(theme_name):
    """Get theme configuration based on CLI argument."""
    themes = {
        "light": (dbc.themes.BOOTSTRAP, ThemeConfig.light_theme()),
        "dark": (dbc.themes.DARKLY, ThemeConfig.dark_theme()),
        "lux": (dbc.themes.LUX, ThemeConfig.from_dbc_theme(dbc.themes.LUX)),
        "cyborg": (dbc.themes.CYBORG, ThemeConfig.from_dbc_theme(dbc.themes.CYBORG)),
    }
    return themes.get(theme_name, themes["lux"])


def main():
    # Parse CLI arguments
    parser = argparse.ArgumentParser(description="v0.15 Showcase Dashboard")
    parser.add_argument(
        "--theme",
        choices=["light", "dark", "lux", "cyborg"],
        default="lux",
        help="Dashboard theme",
    )
    args = parser.parse_args()

    # Ensure sample data exists
    data_file = ensure_sample_data()

    # Initialize datasource with v0.15 pattern (composition)
    # Uses default param_classifier which routes params with transform__ prefix to transform stage
    global datasource
    datasource = DataSource(
        data_builder=SalesDataBuilder(data_file),
        data_transformer=SalesDataTransformer(),  # v0.15+ API (was: data_filter)
        cache_ttl=600,
    )

    # Get theme
    theme_url, theme_config = get_theme_config(args.theme)

    # Create global control panel for sidebar
    # Control names use transform__ prefix so default classifier routes them to transform stage
    control_panel = ControlPanelBlock(
        block_id="transforms",
        datasource=datasource,
        title="Global Transforms",
        controls={
            "transform__category": Control(
                component=dbc.Select,
                props={
                    "options": [
                        {"label": "All", "value": "All"},
                        {"label": "Electronics", "value": "Electronics"},
                        {"label": "Clothing", "value": "Clothing"},
                        {"label": "Tools", "value": "Tools"},
                    ],
                    "value": "All",
                },
            ),
            "transform__min_price": Control(
                component=dbc.Input,
                props={
                    "type": "number",
                    "placeholder": "Min price",
                    "value": "",  # Empty string instead of None
                    "min": 0,
                    "step": 10,
                    "debounce": True,  # Update only on Enter or blur
                },
            ),
        },
    )

    # Configure collapsible sidebar (NEW in v0.15+)
    sidebar = SidebarConfig(
        blocks=[control_panel],
        collapsible=True,
        width="320px",
        title="Global Transforms",
        position="start",
        default_collapsed=False,
        push_content=True,  # NEW: Adaptive layout (push vs overlay)
    )

    # Create navigation
    navigation = NavigationConfig(
        sections=[
            NavigationSection(title="Overview", block_factory=create_overview_section),
            NavigationSection(
                title="EDA & Data Quality", block_factory=create_eda_section
            ),
            NavigationSection(
                title="Detailed Analysis", block_factory=create_analysis_section
            ),
        ],
        position="left",
    )

    # Create page with sidebar (NEW in v0.15+)
    page = DashboardPage(
        title=f"v0.15 Showcase Dashboard ({args.theme.capitalize()} Theme)",
        sidebar=sidebar,  # NEW: Collapsible sidebar with global transforms
        navigation=navigation,
        theme=theme_url,
        theme_config=theme_config,
    )

    # Create app with theme automatically applied
    app = page.create_app(
        suppress_callback_exceptions=True,  # Required for pre-registered callbacks
    )

    print("=" * 70)
    print(f"v0.15 Showcase Dashboard - {args.theme.capitalize()} Theme")
    print("=" * 70)
    print("\nFeatures Demonstrated:")
    print("  ✓ Navigation with 3 sections (Overview, EDA, Analysis)")
    print("  ✓ Theme selection via CLI (--theme)")
    print("  ✓ v0.15 composition pattern (DataBuilder + DataTransformer)")
    print("  ✓ NEW v0.15: Collapsible Sidebar with global transforms (☰ button)")
    print("  ✓ NEW v0.15: Adaptive layout (content pushes aside on desktop)")
    print("  ✓ NEW v0.15: Cross-section State() (all charts use sidebar)")
    print("  ✓ NEW v0.15: Block-level transforms (transform_fn)")
    print("  ✓ MetricsBlock with dynamic sizing (auto-scales)")
    print("  ✓ EDA presets (Correlation, Histogram, Missing Values, BoxPlot, KneePlot)")
    print("  ✓ Interactive and static charts")
    print("  ✓ Control panels with state management")
    print("  ✓ Various layout presets (kpi_row_top, two_column_8_4)")
    print("\nInteraction Guide:")
    print("  1. Click ☰ button (top-left) to toggle sidebar")
    print("  2. Watch content slide aside (desktop) or overlay (mobile)")
    print("  3. Change transforms in sidebar → all sections update")
    print("  4. Navigate between sections → transforms persist")
    print("\nStarting server at http://127.0.0.1:8050/")
    print("Press Ctrl+C to stop")
    print("=" * 70)

    app.run(debug=True)


if __name__ == "__main__":
    main()
