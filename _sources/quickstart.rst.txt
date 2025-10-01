Quick Start Guide
==================

This guide will help you create your first dashboard using Dashboard Lego.

Creating Your First Dashboard
------------------------------

Let's create a simple sales dashboard step by step.

Step 1: Define a Data Source
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

First, create a data source by inheriting from :class:`BaseDataSource`:

.. code-block:: python

   import pandas as pd
   from dashboard_lego.core.datasource import BaseDataSource

   class SalesDataSource(BaseDataSource):
       def __init__(self, file_path):
           self.file_path = file_path
           super().__init__()

       def _load_data(self, params: dict) -> pd.DataFrame:
           """Load data from CSV file."""
           return pd.read_csv(self.file_path)

       def get_kpis(self) -> dict:
           """Calculate key performance indicators."""
           if self._data is None:
               return {}
           return {
               "total_sales": self._data["Sales"].sum(),
               "total_units": self._data["UnitsSold"].sum()
           }

       def get_filter_options(self, filter_name: str) -> list:
           """Provide filter options (not used in this example)."""
           return []

       def get_summary(self) -> str:
           """Provide data summary (not used in this example)."""
           return ""

Step 2: Create Dashboard Blocks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create blocks for displaying your data:

.. code-block:: python

   import plotly.express as px
   import plotly.graph_objects as go
   from dashboard_lego.blocks.kpi import KPIBlock
   from dashboard_lego.blocks.chart import StaticChartBlock

   # Initialize data source
   datasource = SalesDataSource(file_path="sample_data.csv")
   datasource.init_data()

   # Create KPI block
   kpi_block = KPIBlock(
       block_id="sales_kpis",
       datasource=datasource,
       kpi_definitions=[
           {"key": "total_sales", "title": "Total Sales", "color": "success"},
           {"key": "total_units", "title": "Total Units Sold", "color": "info"},
       ],
       subscribes_to="dummy_state"  # Not used in static dashboard
   )

   # Define chart function
   def plot_sales_by_fruit(df: pd.DataFrame, ctx) -> go.Figure:
       """Create a bar chart of sales by fruit."""
       sales_by_fruit = df.groupby("Fruit")["Sales"].sum().reset_index()
       return px.bar(sales_by_fruit, x="Fruit", y="Sales", title="Sales by Fruit")

   # Create chart block
   chart_block = StaticChartBlock(
       block_id="sales_chart",
       datasource=datasource,
       title="Fruit Sales",
       chart_generator=plot_sales_by_fruit,
       subscribes_to="dummy_state"
   )

Step 3: Create Dashboard Page
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Assemble your blocks into a dashboard page:

.. code-block:: python

   from dashboard_lego.core.page import DashboardPage
   from dashboard_lego.presets.layouts import one_column
   import dash_bootstrap_components as dbc

   # Create dashboard page using layout presets
   dashboard_page = DashboardPage(
       title="Simple Sales Dashboard",
       blocks=one_column([kpi_block, chart_block]),  # Stack blocks vertically
       theme=dbc.themes.LUX
   )

Step 4: Run the Application
~~~~~~~~~~~~~~~~~~~~~~~~~~~

Set up and run your Dash application:

.. code-block:: python

   import dash

   # Create Dash app
   app = dash.Dash(__name__, external_stylesheets=[dashboard_page.theme])
   app.layout = dashboard_page.build_layout()

   # Register callbacks (handled automatically)
   dashboard_page.register_callbacks(app)

   # Run the app
   if __name__ == "__main__":
       app.run_server(debug=True)

Complete Example
----------------

Here's the complete code for your first dashboard:

.. literalinclude:: ../examples/01_simple_dashboard.py
   :language: python
   :caption: Complete simple dashboard example

Next Steps
----------

Now that you've created your first dashboard, you might want to:

1. **Add Interactivity**: Learn about :doc:`interactivity` to connect blocks together
2. **Use Presets**: Explore :doc:`presets/index` for ready-made visualization blocks
3. **Custom Layouts**: Discover :doc:`layouts` for different dashboard arrangements
4. **Create Custom Blocks**: Learn how to extend Dashboard Lego with your own components

Running the Example
-------------------

To run this example:

1. Save the code to a file (e.g., ``my_dashboard.py``)
2. Create a sample data file with columns: ``Fruit``, ``Sales``, ``UnitsSold``
3. Run: ``python my_dashboard.py``
4. Open your browser to ``http://localhost:8050``

Troubleshooting
---------------

Common issues and solutions:

**Import Error**: Make sure Dashboard Lego is installed:
   .. code-block:: bash
      pip install dashboard-lego

**Data Loading Error**: Check that your data file exists and has the expected columns.

**Chart Not Displaying**: Verify that your data source is properly initialized with ``datasource.init_data()``.
