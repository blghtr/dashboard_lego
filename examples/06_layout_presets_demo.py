# 06_layout_presets_demo_final.py

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import html

from blocks.chart import StaticChartBlock
from blocks.kpi import KPIBlock
from blocks.text import TextBlock
from core.datasources.csv_source import CsvDataSource
from core.page import DashboardPage
from presets.layouts import (
    kpi_row_top,
    one_column,
    sidebar_main_3_9,
    three_column_4_4_4,
    two_column_6_6,
    two_column_8_4,
)
from utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)

# 1. Use the library's CsvDataSource
datasource = CsvDataSource(file_path="examples/sample_data.csv")
datasource.init_data()

# 2. Create various blocks for demonstration
dummy_state = "dummy_state_for_init"

# KPI blocks - each with unique ID
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

# Additional KPI blocks for different rows
total_sales_kpi2 = KPIBlock(
    block_id="total_sales_2",
    datasource=datasource,
    kpi_definitions=[
        {"key": "total_sales", "title": "Total Sales", "color": "success"}
    ],
    subscribes_to=dummy_state,
)

total_units_kpi2 = KPIBlock(
    block_id="total_units_2",
    datasource=datasource,
    kpi_definitions=[{"key": "total_units", "title": "Total Units", "color": "info"}],
    subscribes_to=dummy_state,
)

avg_price_kpi2 = KPIBlock(
    block_id="avg_price_2",
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


def plot_sales_distribution(df, ctx):
    """Creates a histogram of sales distribution."""
    fig = px.histogram(df, x="Sales", title="Sales Distribution", nbins=10)
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

sales_dist_chart = StaticChartBlock(
    block_id="sales_dist_chart",
    datasource=datasource,
    title="Sales Distribution",
    chart_generator=plot_sales_distribution,
    subscribes_to=dummy_state,
)

# Additional chart blocks for different rows
sales_chart2 = StaticChartBlock(
    block_id="sales_chart_2",
    datasource=datasource,
    title="Sales Analysis",
    chart_generator=plot_sales_by_fruit,
    subscribes_to=dummy_state,
)

units_chart2 = StaticChartBlock(
    block_id="units_chart_2",
    datasource=datasource,
    title="Units Analysis",
    chart_generator=plot_units_by_category,
    subscribes_to=dummy_state,
)


# Text blocks
def welcome_content_generator(df):
    return html.Div(
        [
            html.H3("Welcome to Layout Presets Demo"),
            html.P(
                "This dashboard demonstrates various layout presets available in dashboard-lego."
            ),
        ]
    )


def sidebar_content_generator(df):
    return html.Div(
        [
            html.H4("Sidebar Content"),
            html.P("This is a narrow sidebar with additional information."),
        ]
    )


def footer_content_generator(df):
    return html.P([html.Em("Dashboard created with dashboard-lego layout presets")])


welcome_text = TextBlock(
    block_id="welcome",
    datasource=datasource,
    content_generator=welcome_content_generator,
    subscribes_to=dummy_state,
)

sidebar_text = TextBlock(
    block_id="sidebar_info",
    datasource=datasource,
    content_generator=sidebar_content_generator,
    subscribes_to=dummy_state,
)

footer_text = TextBlock(
    block_id="footer",
    datasource=datasource,
    content_generator=footer_content_generator,
    subscribes_to=dummy_state,
)

# 3. Demonstrate different layout presets
logger.info("Creating dashboard with layout presets demonstration")

# Create a comprehensive dashboard using multiple presets
dashboard_page = DashboardPage(
    title="Layout Presets Demonstration",
    blocks=[
        # Row 1: Welcome message using one_column preset
        *one_column([welcome_text]),
        # Row 2: KPI row using kpi_row_top preset
        *kpi_row_top(
            kpi_blocks=[total_sales_kpi, total_units_kpi, avg_price_kpi],
            content_rows=[],
        ),
        # Row 3: Two column layout using two_column_8_4 preset
        *two_column_8_4(sales_chart, units_chart),
        # Row 4: Three column layout using three_column_4_4_4 preset
        *three_column_4_4_4(sales_dist_chart, total_sales_kpi2, total_units_kpi2),
        # Row 5: Sidebar layout using sidebar_main_3_9 preset
        *sidebar_main_3_9(sidebar_text, avg_price_kpi2),
        # Row 6: Equal two column using two_column_6_6 preset
        *two_column_6_6(units_chart2, sales_chart2),
        # Row 7: Footer using one_column preset
        *one_column([footer_text]),
    ],
    theme=dbc.themes.BOOTSTRAP,
)

# 4. Set up and run the Dash app
app = dash.Dash(__name__, external_stylesheets=[dashboard_page.theme])
app.layout = dashboard_page.build_layout()

# Register callbacks
dashboard_page.register_callbacks(app)

if __name__ == "__main__":
    logger.info("Starting layout presets demo server")
    app.run(debug=True, use_reloader=False)
