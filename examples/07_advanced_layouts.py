# 07_advanced_layouts.py

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import html

from dashboard_lego.blocks.chart import StaticChartBlock
from dashboard_lego.blocks.kpi import KPIBlock
from dashboard_lego.blocks.text import TextBlock
from dashboard_lego.core.datasources.csv_source import CsvDataSource
from dashboard_lego.core.page import DashboardPage
from dashboard_lego.utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

# 1. Use the library's CsvDataSource
datasource = CsvDataSource(file_path="examples/sample_data.csv")
datasource.init_data()

# 2. Create blocks for demonstration
dummy_state = "dummy_state_for_init"

# KPI blocks
total_sales_kpi = KPIBlock(
    block_id="total_sales",
    datasource=datasource,
    kpi_definitions=[
        {"key": "total_sales", "title": "Total Sales", "color": "success"}
    ],
    subscribes_to=dummy_state,
)

total_units_kpi = KPIBlock(
    block_id="total_units",
    datasource=datasource,
    kpi_definitions=[{"key": "total_units", "title": "Total Units", "color": "info"}],
    subscribes_to=dummy_state,
)

avg_price_kpi = KPIBlock(
    block_id="avg_price",
    datasource=datasource,
    kpi_definitions=[{"key": "avg_price", "title": "Avg Price", "color": "warning"}],
    subscribes_to=dummy_state,
)


# Chart blocks
def plot_sales_by_fruit(df, ctx):
    """Creates a bar chart of sales by fruit."""
    sales_by_fruit = df.groupby("Fruit")["Sales"].sum().reset_index()
    fig = px.bar(sales_by_fruit, x="Fruit", y="Sales", title="Sales by Fruit")
    return fig


def plot_units_by_category(df, ctx):
    """Creates a pie chart of units by category."""
    units_by_category = df.groupby("Category")["UnitsSold"].sum().reset_index()
    fig = px.pie(
        units_by_category,
        values="UnitsSold",
        names="Category",
        title="Units by Category",
    )
    return fig


sales_chart = StaticChartBlock(
    block_id="sales_chart",
    datasource=datasource,
    title="Sales Analysis",
    chart_generator=plot_sales_by_fruit,
    subscribes_to=dummy_state,
)

units_chart = StaticChartBlock(
    block_id="units_chart",
    datasource=datasource,
    title="Units Analysis",
    chart_generator=plot_units_by_category,
    subscribes_to=dummy_state,
)

# Additional chart for row 4
units_chart2 = StaticChartBlock(
    block_id="units_chart_2",
    datasource=datasource,
    title="Units Analysis",
    chart_generator=plot_units_by_category,
    subscribes_to=dummy_state,
)


# Text blocks
def header_content_generator(df):
    return html.Div(
        [
            html.H2("Advanced Layout Features Demo"),
            html.P("This example shows custom row and column options."),
        ]
    )


header_text = TextBlock(
    block_id="header",
    datasource=datasource,
    content_generator=header_content_generator,
    subscribes_to=dummy_state,
)

# 3. Demonstrate advanced layout features with custom options
logger.info("Creating dashboard with advanced layout features")

dashboard_page = DashboardPage(
    title="Advanced Layout Features",
    blocks=[
        # Row 1: Header with custom styling
        (
            [(header_text, {"md": 12, "className": "text-center bg-light p-3"})],
            {"className": "mb-4", "style": {"backgroundColor": "#f8f9fa"}},
        ),
        # Row 2: KPI row with custom gap and alignment
        (
            [
                (total_sales_kpi, {"md": 4, "className": "border rounded p-2"}),
                (total_units_kpi, {"md": 4, "className": "border rounded p-2"}),
                (avg_price_kpi, {"md": 4, "className": "border rounded p-2"}),
            ],
            {"g": 3, "justify": "center", "className": "mb-4"},
        ),
        # Row 3: Two charts with responsive breakpoints
        (
            [
                (sales_chart, {"xs": 6, "sm": 6, "md": 8, "lg": 8, "xl": 8}),
                (units_chart, {"xs": 6, "sm": 6, "md": 4, "lg": 4, "xl": 4}),
            ],
            {"align": "start", "className": "mb-4"},
        ),
        # Row 4: Single chart with offset
        (
            [(units_chart2, {"md": 6, "offset": 3, "className": "border shadow-sm"})],
            {"className": "mb-4"},
        ),
    ],
    theme=dbc.themes.BOOTSTRAP,
)

# 4. Set up and run the Dash app
app = dash.Dash(__name__, external_stylesheets=[dashboard_page.theme])
app.layout = dashboard_page.build_layout()

# Register callbacks
dashboard_page.register_callbacks(app)

if __name__ == "__main__":
    logger.info("Starting advanced layouts demo server")
    app.run(debug=True, use_reloader=False)
