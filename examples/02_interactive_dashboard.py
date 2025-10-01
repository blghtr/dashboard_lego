# 02_interactive_dashboard.py

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc

from dashboard_lego.blocks.chart import Control, InteractiveChartBlock
from dashboard_lego.blocks.kpi import KPIBlock
from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.core.page import DashboardPage
from dashboard_lego.utils.logger import get_logger, setup_logging

# 1. Setup logging for demonstration
setup_logging(level="DEBUG")  # Enable DEBUG level to see hierarchy
logger = get_logger(__name__)
logger.info("Starting interactive dashboard example")


# 2. Define a custom data source
class SalesDataSource(BaseDataSource):
    def __init__(self, file_path):
        self.file_path = file_path
        super().__init__()

    def _load_data(self, params: dict) -> pd.DataFrame:
        logger.debug(f"Loading data with params: {params}")
        df = pd.read_csv(self.file_path)
        # In a real app, params would be used to filter data from a DB
        # Here, we simulate filtering based on the category from the dropdown
        category = params.get("category_filter")
        if category and category != "All":
            logger.info(f"Filtering data by category: {category}")
            filtered_df = df[df["Category"] == category]
            logger.debug(f"Filtered data shape: {filtered_df.shape}")
            return filtered_df
        logger.info("No category filter applied, returning full dataset")
        return df

    def get_kpis(self) -> dict:
        if self._data is None:
            return {}
        return {
            "total_sales": self._data["Sales"].sum(),
            "total_units": self._data["UnitsSold"].sum(),
            "fruit_count": len(self._data["Fruit"].unique()),
        }

    def get_filter_options(self, filter_name: str) -> list:
        """Provides options for filter controls."""
        if self._data is None:
            self.init_data()
        if filter_name == "category_filter":
            categories = self._data["Category"].unique().tolist()
            return ["All"] + categories
        return []

    def get_summary(self) -> str:
        return ""


# 3. Define plotting functions
def plot_sales_by_fruit(df: pd.DataFrame, ctx) -> go.Figure:
    logger.debug(f"Creating chart with {len(df)} rows")
    fig = px.bar(df, x="Fruit", y="Sales", title="Sales by Fruit")
    logger.info("Chart created successfully")
    return fig


# 4. Instantiate data source and blocks
logger.info("Creating datasource and blocks")
datasource = SalesDataSource(file_path="examples/sample_data.csv")

# This block has its own controls and PUBLISHES its state
logger.debug("Creating interactive chart block")
interactive_chart = InteractiveChartBlock(
    block_id="interactive_chart",
    datasource=datasource,
    title="Sales Distribution",
    chart_generator=plot_sales_by_fruit,
    controls={
        "category_filter": Control(
            component=dcc.Dropdown,
            props={
                "options": datasource.get_filter_options("category_filter"),
                "value": "All",
                "clearable": False,
            },
        )
    },
)

# This block SUBSCRIBES to the state published by the interactive chart
logger.debug("Creating KPI block")
kpi_block = KPIBlock(
    block_id="sales_kpis",
    datasource=datasource,
    kpi_definitions=[
        {"key": "total_sales", "title": "Total Sales"},
        {"key": "total_units", "title": "Units Sold"},
        {"key": "fruit_count", "title": "Fruit Varieties"},
    ],
    # Subscribes to the state from the dropdown in the other block
    subscribes_to="interactive_chart-category_filter",
)

# 5. Create the Dashboard Page using layout presets
from dashboard_lego.presets.layouts import two_column_8_4

logger.info("Creating dashboard page")
dashboard_page = DashboardPage(
    title="Interactive Sales Dashboard",
    blocks=two_column_8_4(interactive_chart, kpi_block),  # Main chart with KPI sidebar
    theme=dbc.themes.DARKLY,
)

# 6. Set up and run the Dash app
logger.info("Setting up Dash application")
app = dash.Dash(__name__, external_stylesheets=[dashboard_page.theme])
app.layout = dashboard_page.build_layout()

# This will now generate the callback that connects the dropdown to the chart and KPIs
dashboard_page.register_callbacks(app)

if __name__ == "__main__":
    logger.info("Starting Dash server")
    app.run(debug=True, use_reloader=False)
