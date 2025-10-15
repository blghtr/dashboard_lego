.. _guide-export:

Exporting Figures
=================

Dashboard Lego supports exporting Plotly figures without running a Dash server,
enabling static report generation, notebook integration, and programmatic figure creation.

Single Figure Export
--------------------

Export individual chart blocks using the ``get_figure()`` method:

.. code-block:: python

   from dashboard_lego.blocks import TypedChartBlock
   from dashboard_lego.core import BaseDataSource, DataBuilder

   # Create chart block
   chart = TypedChartBlock(
       block_id="sales_chart",
       datasource=datasource,
       plot_type="bar",
       plot_params={"x": "Product", "y": "Sales"},
       title="Product Sales"
   )

   # Export figure
   fig = chart.get_figure()

   # Save as HTML
   fig.write_html("sales_chart.html")

   # Save as image (requires kaleido)
   fig.write_image("sales_chart.png", width=800, height=600)

   # Display in notebook
   fig.show()

With Parameters
^^^^^^^^^^^^^^^

For blocks with controls, pass parameter values:

.. code-block:: python

   histogram = GroupedHistogramPreset(
       block_id="distribution",
       datasource=datasource,
       subscribes_to=[]
   )

   # Export with specific column selection
   fig = histogram.get_figure(params={
       'x_col': 'Price',
       'group_by': 'Category'
   })

Layout Export
-------------

Export entire dashboard layouts as single figure using subplots:

.. code-block:: python

   from dashboard_lego.core import DashboardPage
   from dashboard_lego.utils.layout_export import export_layout_to_figure

   # Define layout
   layout = [
       [chart1, chart2],  # Row 1: 2 charts
       [chart3]           # Row 2: 1 chart full width
   ]

   # Method 1: Via DashboardPage
   page = DashboardPage(title="Dashboard", blocks=layout)
   fig = page.export_to_figure(title="Monthly Report")
   fig.write_html("dashboard.html")

   # Method 2: Direct utility
   fig = export_layout_to_figure(
       layout,
       title="Monthly Report",
       vertical_spacing=0.15,
       horizontal_spacing=0.1
   )

Use Cases
---------

Static Reports
^^^^^^^^^^^^^^

Generate HTML reports for email distribution:

.. code-block:: python

   # Generate monthly report
   fig = page.export_to_figure(
       params={'month': 'December'},
       title="December Sales Report"
   )
   fig.write_html("december_report.html")

Jupyter Notebooks
^^^^^^^^^^^^^^^^^

Display figures inline without Dash server:

.. code-block:: python

   # In notebook cell
   chart = TypedChartBlock(...)
   fig = chart.get_figure()
   fig.show()  # Displays inline

Programmatic Generation
^^^^^^^^^^^^^^^^^^^^^^^

Batch generate figures for multiple scenarios:

.. code-block:: python

   for region in ['North', 'South', 'East', 'West']:
       fig = chart.get_figure(params={'region': region})
       fig.write_html(f"report_{region}.html")

Limitations
-----------

- Only chart blocks are exported (metrics, text, controls skipped)
- Navigation dashboards cannot be exported as single figure
- Interactive Dash callbacks are not preserved in static exports
- Subplot layout may differ from dashboard grid layout
