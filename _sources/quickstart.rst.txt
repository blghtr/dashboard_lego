Quick Start Guide
==================

This guide will help you create your first dashboard using Dashboard Lego.

Creating Your First Dashboard
------------------------------

Let's create a simple sales dashboard step by step.

Step 1: Define a Data Builder
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

v0.15+ uses composition instead of inheritance. Create a :class:`DataBuilder`:

.. code-block:: python

   import pandas as pd
   from dashboard_lego.core import DataBuilder, DataSource

   class SalesDataBuilder(DataBuilder):
       def __init__(self, file_path):
           super().__init__()
           self.file_path = file_path

       def build(self, params):
           """Load CSV and optionally add calculated fields."""
           df = pd.read_csv(self.file_path)
           # Add any calculated columns here if needed
           return df

   # Create datasource using composition (no inheritance!)
   datasource = DataSource(
       data_builder=SalesDataBuilder("sample_data.csv")
   )

Step 2: Create Dashboard Blocks
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Create blocks using v0.15+ API:

.. code-block:: python

   import plotly.express as px
   from dashboard_lego.blocks.metrics import MetricsBlock
   from dashboard_lego.blocks.typed_chart import TypedChartBlock

   # MetricsBlock replaces get_kpis() pattern (v0.15+)
   metrics_block = MetricsBlock(
       block_id="sales_metrics",
       datasource=datasource,
       metrics_spec={
           "total_sales": {
               "column": "Sales",
               "agg": "sum",
               "title": "Total Sales",
               "color": "success"
           },
           "total_units": {
               "column": "UnitsSold",
               "agg": "sum",
               "title": "Total Units Sold",
               "color": "info"
           }
       },
       subscribes_to="dummy_state"
   )

   # TypedChartBlock with plot registry (v0.15+)
   chart_block = TypedChartBlock(
       block_id="sales_chart",
       datasource=datasource,
       plot_type="bar",  # Built-in plot type
       plot_params={"x": "Fruit", "y": "Sales"},
       title="Fruit Sales",                    # Static card title
       plot_title="Sales by Fruit",            # Dynamic plot title
       subscribes_to="dummy_state",
       # Optional: transform data at block level (v0.15+)
       transform_fn=lambda df: df.groupby("Fruit")["Sales"].sum().reset_index()
   )

.. note::
   v0.15 introduces ``MetricsBlock`` and ``TypedChartBlock`` which replace
   the legacy ``get_kpis()`` method and ``StaticChartBlock``.
   See :doc:`concepts` for more on block-level transformations.

Interactive Charts with Placeholders
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

For interactive charts with dynamic titles and parameters, use placeholders:

.. code-block:: python

   # Interactive chart with placeholders
   interactive_chart = TypedChartBlock(
       block_id="interactive_sales",
       datasource=datasource,
       plot_type="scatter",
       plot_params={
           "x": "Date",
           "y": "Sales",
           "color": "{{metric_selector}}",  # Placeholder for dynamic color
           "size": "{{size_selector}}"      # Placeholder for dynamic size
       },
       title="Sales Analysis",                           # Static card title
       plot_title="Sales by {{metric_selector}}",      # Dynamic plot title with placeholder
       subscribes_to=["metric_selector", "size_selector"]
   )

See :doc:`placeholders` for complete placeholder documentation.

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
       blocks=one_column([metrics_block, chart_block]),  # Stack blocks vertically
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

.. literalinclude:: ../../examples/01_simple_dashboard.py
   :language: python
   :caption: Complete simple dashboard example

Next Steps
----------

Now that you've created your first dashboard, you might want to:

1. **Add Interactivity**: Explore interactive blocks in the API reference (:doc:`api/blocks`).
2. **Use Presets**: See preset components in (:doc:`api/presets`).
3. **Custom Layouts**: Learn layout helpers in (:doc:`api/presets`).
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
