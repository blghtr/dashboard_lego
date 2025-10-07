"""
Demo of ControlPanelBlock - standalone control panels for dashboard settings.

This example demonstrates:
1. Creating a control panel with multiple controls (sliders, dropdowns)
2. Initializing control values from datasource
3. Using ControlPanelBlock as a publisher of control values
4. Customizing control panel styles

:hierarchy: [Examples | ControlPanelBlock | Demo]
:relates-to:
 - motivated_by: "PRD: Demonstrate ControlPanelBlock usage patterns"
 - implements: "example: '11_control_panel_demo'"
 - uses: ["class: 'ControlPanelBlock'", "class: 'StaticChartBlock'"]

:rationale: "Simple example showing ControlPanelBlock features."
:contract:
 - pre: "Required packages are installed."
 - post: "Running dashboard with interactive control panel."

"""

import plotly.express as px
from dash import Dash, dcc

from dashboard_lego.blocks.chart import Control, ControlPanelBlock, StaticChartBlock
from dashboard_lego.blocks.kpi import KPIBlock
from dashboard_lego.core.datasources.csv_source import CsvDataSource
from dashboard_lego.core.page import DashboardPage
from dashboard_lego.presets.layouts import one_column
from dashboard_lego.utils.logger import setup_logging

# Setup DEBUG logging for detailed troubleshooting
setup_logging(level="DEBUG")

# Create datasource from sample CSV
datasource = CsvDataSource("examples/sample_data.csv")
datasource.init_data()  # Initialize data


# Value initializer - computes initial control values from data
def initialize_control_values(df):
    """Initialize control values based on the datasource data."""
    if df.empty:
        return {}

    # Use "All" as default to show all fruits initially
    return {
        "fruit_filter": "All",  # Show all fruits by default
        # "min_sales": avg_sales,  # Commented out to use default value from props
    }


# Chart generator for sales
def sales_chart_generator(df, ctx):
    """
    Generates a bar chart of sales by fruit with filtering support.

    :hierarchy: [Examples | ControlPanelBlock | Chart Generator]
    :relates-to:
     - motivated_by: "Bug Fix: Chart must react to control panel slider values"
     - implements: "function: 'sales_chart_generator' with filtering"
     - uses: ["class: 'ChartContext'", "library: 'plotly.express'"]

    :rationale: "Added filtering by min_sales threshold from control panel to demonstrate state interaction."
    :contract:
     - pre: "DataFrame with 'Fruit' and 'Sales' columns is provided."
     - post: "Returns filtered bar chart showing fruits above minimum sales threshold."

    """
    if df.empty:
        return px.bar(title="No data available")

    # Apply filtering based on control panel values
    filtered_df = df.copy()

    # Filter by minimum sales if provided
    min_sales = ctx.controls.get("min_sales")
    if min_sales is not None:
        filtered_df = filtered_df[filtered_df["Sales"] >= min_sales]

    # Filter by fruit if provided
    fruit_filter = ctx.controls.get("fruit_filter")
    if fruit_filter and fruit_filter != "All":
        filtered_df = filtered_df[filtered_df["Fruit"] == fruit_filter]

    if filtered_df.empty:
        return px.bar(title="No data matches the current filters")

    fig = px.bar(
        filtered_df,
        x="Fruit",
        y="Sales",
        title=f"Sales by Fruit (Min: {min_sales if min_sales else 'None'})",
        color="Fruit",
        color_discrete_sequence=px.colors.qualitative.Set2,
    )
    return fig


# Define controls for the panel with responsive column sizing
controls = {
    "fruit_filter": Control(
        component=dcc.Dropdown,
        props={
            "options": [
                {"label": "All", "value": "All"},
                {"label": "Apple", "value": "Apple"},
                {"label": "Banana", "value": "Banana"},
                {"label": "Orange", "value": "Orange"},
            ],
            "value": "All",
            "clearable": False,
            "style": {"minWidth": "200px"},
        },
        col_props={"xs": 12, "md": 4},  # 4 колонки на средних экранах
    ),
    "min_sales": Control(
        component=dcc.Slider,
        props={
            "min": 0,
            "max": 200,
            "step": 5,
            "value": 100,
            "marks": {0: "0", 50: "50", 100: "100", 150: "150", 200: "200"},
            "tooltip": {"placement": "bottom", "always_visible": True},
            "updatemode": "drag",
            "included": True,
            "className": "slider-control",
        },
        col_props={"xs": 12, "md": 8},  # 8 колонок, заполняет остаток
    ),
}

# Create control panel block
control_panel = ControlPanelBlock(
    block_id="settings_panel",
    datasource=datasource,
    title="Dashboard Settings 🎛️",
    controls=controls,
    value_initializer=initialize_control_values,
    # Style customization
    card_style={
        "backgroundColor": "#f8f9fa",
        "border": "2px solid #dee2e6",
    },
    title_style={"color": "#495057", "fontWeight": "bold"},
    controls_row_style={"padding": "15px"},
)

# Create KPI block
kpi_block = KPIBlock(
    block_id="kpi_summary",
    datasource=datasource,
    kpi_definitions=[
        {
            "key": "total_sales",
            "title": "Total Sales",
            "icon": "💰",
            "color": "success",
        },
        {
            "key": "avg_sales",
            "title": "Avg Sales",
            "icon": "📈",
            "color": "info",
        },
        {
            "key": "total_units",
            "title": "Total Units",
            "icon": "📦",
            "color": "warning",
        },
    ],
    subscribes_to="settings_panel-fruit_filter",
)

# Create chart block
sales_chart = StaticChartBlock(
    block_id="sales_chart",
    datasource=datasource,
    title="Sales by Fruit",
    chart_generator=sales_chart_generator,
    subscribes_to=["settings_panel-min_sales", "settings_panel-fruit_filter"],
    figure_layout={"height": 400},
)

# Create dashboard page
page = DashboardPage(
    title="Control Panel Demo",
    blocks=one_column([control_panel, kpi_block, sales_chart]),
)

# Create Dash app
app = Dash(__name__, external_stylesheets=[page.theme])

# Add custom CSS for slider
app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            .slider-control {
                min-width: 200px !important;  /* reduced minimum width */
                width: 100% !important;       /* растягивается на всю доступную ширину колонки */
                margin: 5px !important;       /* reduced margin */
                display: block !important;    /* ensure it's visible */
            }
            .slider-control .rc-slider {
                display: block !important;    /* ensure slider is visible */
                width: 100% !important;
            }
            .slider-control .rc-slider-track {
                background-color: #007bff !important;
                height: 6px !important;
            }
            .slider-control .rc-slider-rail {
                background-color: #e9ecef !important;
                height: 6px !important;
            }
            .slider-control .rc-slider-handle {
                border: 2px solid #007bff !important;
                background-color: #fff !important;
                width: 20px !important;
                height: 20px !important;
                margin-top: -7px !important;
            }
            .slider-control .rc-slider-handle:hover {
                border-color: #0056b3 !important;
            }
            .slider-control .rc-slider-mark {
                font-size: 12px !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

app.layout = page.build_layout()
page.register_callbacks(app)


if __name__ == "__main__":
    print("=" * 60)
    print("Control Panel Demo - dashboard_lego")
    print("=" * 60)
    print("\nFeatures demonstrated:")
    print("  ✓ Control panel with dropdown and slider")
    print("  ✓ Value initialization from datasource")
    print("  ✓ Controls publish values to state")
    print("  ✓ Custom styling for control panel")
    print("\nOpen http://127.0.0.1:8050 in your browser")
    print("=" * 60)
    app.run(debug=True, use_reloader=False)
