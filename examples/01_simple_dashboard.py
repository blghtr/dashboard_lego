# 01_simple_dashboard.py

import dash
import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from blocks.chart import StaticChartBlock
from blocks.kpi import KPIBlock
from core.datasource import BaseDataSource
from core.page import DashboardPage
from utils.logger import get_logger, setup_logging

setup_logging()
logger = get_logger(__name__)


# 1. Define a custom data source
# We inherit from BaseDataSource and implement the data loading and processing methods.
class SalesDataSource(BaseDataSource):
    def __init__(self, file_path):
        self.file_path = file_path
        # Call super() to initialize the cache
        super().__init__()

    def _load_data(self, params: dict) -> pd.DataFrame:
        """Load data from the CSV file."""
        return pd.read_csv(self.file_path)

    def get_kpis(self) -> dict:
        """Calculate Key Performance Indicators."""
        if self._data is None:
            return {}
        return {
            "total_sales": self._data["Sales"].sum(),
            "total_units": self._data["UnitsSold"].sum(),
        }

    # These methods are required by the abstract base class but not used in this simple example.
    def get_filter_options(self, filter_name: str) -> list:
        return []

    def get_summary(self) -> str:
        return ""


# 2. Define a plotting function
# This function takes a DataFrame and ChartContext and returns a Plotly figure.
def plot_sales_by_fruit(df: pd.DataFrame, ctx) -> go.Figure:
    """Creates a bar chart of sales by fruit."""
    sales_by_fruit = df.groupby("Fruit")["Sales"].sum().reset_index()
    fig = px.bar(sales_by_fruit, x="Fruit", y="Sales", title="Sales by Fruit")
    return fig


# 3. Instantiate your data source
datasource = SalesDataSource(file_path="examples/sample_data.csv")
# Initialize the data. This will load and cache it.
datasource.init_data()

# 4. Define your dashboard blocks

kpi_block = KPIBlock(
    block_id="sales_kpis",
    datasource=datasource,
    kpi_definitions=[
        {"key": "total_sales", "title": "Total Sales", "color": "success"},
        {"key": "total_units", "title": "Total Units Sold", "color": "info"},
    ],
    subscribes_to="dummy_state",  # In a static dashboard, this is not used but required
)

chart_block = StaticChartBlock(
    block_id="sales_chart",
    datasource=datasource,
    title="Fruit Sales",
    chart_generator=plot_sales_by_fruit,
    subscribes_to="dummy_state",  # Not used here, but required
)

# 5. Create the Dashboard Page using layout presets
from presets.layouts import one_column

dashboard_page = DashboardPage(
    title="Simple Sales Dashboard",
    blocks=one_column([kpi_block, chart_block]),  # Stack blocks vertically
    theme=dbc.themes.LUX,
)

# 6. Set up and run the Dash app
app = dash.Dash(__name__, external_stylesheets=[dashboard_page.theme])
app.layout = dashboard_page.build_layout()

# The callback registration is now handled by the page object, but since we have
# no real interactivity, this part is trivial. In an interactive dashboard,
# this would generate all the necessary callbacks.
dashboard_page.register_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
