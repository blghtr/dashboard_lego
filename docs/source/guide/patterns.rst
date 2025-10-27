.. _guide-patterns:

Integration Patterns
====================

Common patterns and best practices for building dashboards.

.. contents::
   :local:
   :depth: 2

Publisher/Subscriber Pattern
-----------------------------

Blocks publish state changes and other blocks subscribe to react.

**Flow:**

.. code-block:: text

   ControlPanelBlock → publishes → StateManager → notifies → TypedChartBlock
                                                           → notifies → MetricsBlock

**Example:**

.. code-block:: python

   # Publisher: Control Panel
   control_panel = ControlPanelBlock(
       block_id="filters",
       datasource=datasource,
       title="Filters",
       controls={"category": Control(...)}
   )
   # Publishes: "filters-category"

   # Subscribers: Charts and Metrics
   chart = TypedChartBlock(
       block_id="chart1",
       datasource=datasource,
       plot_type='bar',
       plot_params={'x': 'Product', 'y': 'Sales'},
       subscribes_to="filters-category"
   )

   metrics = MetricsBlock(
       block_id="metrics",
       datasource=datasource,
       metrics_spec={...},
       subscribes_to="filters-category"
   )

Multi-State Subscriptions
--------------------------

A block can subscribe to multiple state sources.

**Example:**

.. code-block:: python

   # Multiple publishers
   date_filter = ControlPanelBlock(
       block_id="date_filter",
       datasource=datasource,
       title="Date Range",
       controls={"date_range": Control(...)}
   )

   category_filter = ControlPanelBlock(
       block_id="category_filter",
       datasource=datasource,
       title="Category",
       controls={"category": Control(...)}
   )

   # Subscriber to multiple states
   chart = TypedChartBlock(
       block_id="multi_chart",
       datasource=datasource,
       title="Filtered Analysis",
       plot_type='bar',
       plot_params={'x': 'Product', 'y': 'Sales'},
       subscribes_to=[
           "date_filter-date_range",
           "category_filter-category"
       ]
   )

Navigation Pattern
------------------

Multi-section dashboards with lazy-loaded sections.

**Example:**

.. code-block:: python

   from dashboard_lego.core.page import NavigationConfig, NavigationSection

   def create_overview_section():
       return kpi_row_top(
           kpi_blocks=[kpi1, kpi2, kpi3],
           content_rows=[[summary_chart]]
       )

   def create_details_section():
       return two_column_8_4(
           main=detail_chart,
           side=filter_panel
       )

   navigation = NavigationConfig(
       sections=[
           NavigationSection(
               title="Overview",
               block_factory=create_overview_section,
               icon="📊"
           ),
           NavigationSection(
               title="Details",
               block_factory=create_details_section,
               icon="🔍"
           )
       ],
       position="left"
   )

   page = DashboardPage(
       title="Multi-Section Dashboard",
       navigation=navigation
   )

Theme Customization Pattern
----------------------------

Apply consistent theming across all components.

**Example:**

.. code-block:: python

   from dashboard_lego.core.theme import ThemeConfig, ColorScheme, Typography

   # Create custom theme
   theme = ThemeConfig.custom_theme(
       name="corporate",
       colors=ColorScheme(
           primary="#003366",
           secondary="#6699CC",
           success="#009966",
           background="#f5f5f5"
       ),
       typography=Typography(
           font_family="'Arial', sans-serif",
           font_size_base="16px"
       )
   )

   # Apply to page
   page = DashboardPage(
       title="Corporate Dashboard",
       blocks=my_blocks,
       theme_config=theme
   )

Layout Composition Pattern
---------------------------

Build complex layouts from simple presets.

**Example:**

.. code-block:: python

   from dashboard_lego.presets.layouts import (
       kpi_row_top,
       two_column_8_4,
       three_column_4_4_4
   )

   # Compose complex layout
   layout = kpi_row_top(
       kpi_blocks=[kpi1, kpi2, kpi3, kpi4],
       content_rows=[
           # Row 1: Main chart with sidebar
           two_column_8_4(main=main_chart, side=filter_panel),
           # Row 2: Three comparison charts
           three_column_4_4_4(a=chart1, b=chart2, c=chart3),
           # Row 3: Full-width table
           [table_block]
       ]
   )

   page = DashboardPage(
       title="Complex Dashboard",
       blocks=layout
   )

Data Processing Pipeline Pattern (v0.15)
-----------------------------------------

Staged data processing with DataBuilder + DataTransformer for optimal caching.

**Pipeline Flow:**

.. code-block:: text

   Control Panel → Params → DataSource → Build → Transform → Blocks
                                ↓              ↓         ↓
                            Classifier      Cache     Cache

**Example:**

.. code-block:: python

   from dashboard_lego.core import DataSource, DataBuilder, DataTransformer

   # Step 1: Define DataBuilder
   class SalesDataBuilder(DataBuilder):
       def __init__(self, file_path: str):
           super().__init__()
           self.file_path = file_path

       def build(self, params):
           df = pd.read_csv(self.file_path)
           df['Revenue'] = df['Price'] * df['Quantity']
           df['Date'] = pd.to_datetime(df['Date'])
           return df

   # Step 2: Define DataTransformer
   class SalesTransformer(DataTransformer):
       def transform(self, data, params):
           df = data.copy()
           if 'filters-category' in params:
               cat = params['filters-category']
               if cat != 'All':
                   df = df[df['Category'] == cat]
           return df

   # Step 3: Define param classifier
   def classify_params(key):
       return 'transform' if key.startswith('filters-') else 'build'

   # Step 4: Create datasource
   datasource = DataSource(
       data_builder=SalesDataBuilder("sales.csv"),
       data_transformer=SalesTransformer(),
       param_classifier=classify_params,
       cache_ttl=600
   )

**Benefits:**

1. **Performance**: Changing filters only triggers transform stage
2. **Clarity**: Each component has one responsibility
3. **Testability**: Test builder and transformer independently
4. **Reusability**: Same components can be used in multiple dashboards

**Cache Sharing (v0.15.2):**

Cache objects are automatically shared across datasource instances to prevent duplicate builds:

- **Same cache_dir**: Multiple datasources with identical ``cache_dir`` paths share cache
- **In-memory**: All ``cache_dir=None`` datasources share single global in-memory cache
- **Stage1 (Build) optimization**: When using ``with_transform_fn()``, the derived datasource
  reuses the parent's cache → ``build()`` executes only once

Example:

.. code-block:: python

   from dashboard_lego.core import DataSource, DataBuilder

   # Create main datasource
   main_ds = DataSource(
       data_builder=MyDataBuilder(),
       cache_dir=None  # In-memory cache
   )

   # Create derived datasource with additional transform
   filtered_ds = main_ds.with_transform_fn(
       lambda df: df[df['Category'] == 'A']
   )

   # Cache is shared automatically:
   assert main_ds.cache is filtered_ds.cache  # True!

   # Stage1 (builder.build) executes only ONCE:
   data1 = main_ds.get_processed_data()      # Triggers build()
   data2 = filtered_ds.get_processed_data()  # Reuses cached build, only applies filter

   # Result: No duplicate expensive data loading/processing

**When cache sharing happens:**

1. **Explicit matching**: ``DataSource(..., cache_dir="/path")`` → all instances with same path share cache
2. **In-memory default**: ``DataSource(..., cache_dir=None)`` → all in-memory instances share cache
3. **Derived datasources**: ``ds.with_transform_fn(...)`` → automatically inherits parent's cache

Quick Dashboard Pattern
-----------------------

The ``quick_dashboard()`` factory enables rapid prototyping in Jupyter notebooks,
Python scripts, and anywhere Dash runs, with minimal code. Supports simple mode
(DataFrame + card specs) and advanced mode (pre-built blocks).

**Smart Layout Algorithm:**

The factory uses an intelligent layout algorithm optimized for notebook readability:

1. **Metrics are compact**: All metrics grouped in single row using ``get_metric_row()``
2. **Charts need space**: Maximum 2 charts per row
3. **Vertical scroll friendly**: Optimized for notebook viewing

**Layout Examples:**

- ``2M + 2C`` → metrics_row + [chart1_50, chart2_50]
- ``1M + 3C`` → metrics_row + [chart1_full] + [chart2_50, chart3_50]
- ``4M + 0C`` → metrics_row (all 4 in one compact row)
- ``0M + 3C`` → [chart1_full] + [chart2_50, chart3_50]

**Simple Mode:**

For quick exploration with 1-4 cards:

.. code-block:: python

   from dashboard_lego.utils.quick_dashboard import quick_dashboard
   import pandas as pd

   # Load data
   df = pd.DataFrame({
       'Product': ['Widget', 'Gadget', 'Tool', 'Device'],
       'Sales': [100, 200, 150, 180],
       'Revenue': [1000, 2000, 1500, 1800]
   })

   # Create dashboard with card specs
   app = quick_dashboard(
       df=df,
       cards=[
           {"type": "metric", "column": "Revenue", "agg": "sum",
            "title": "Total Revenue", "color": "success"},
           {"type": "chart", "plot_type": "bar", "x": "Product", "y": "Sales",
            "title": "Sales by Product"},
           {"type": "text", "content": "## Sales Dashboard\nQuick analysis"}
       ],
       title="Sales Dashboard",
       theme="lux"
   )

   # Run inline (requires jupyter-dash)
   app.run_server(mode='inline')

   # Or open in new browser tab
   app.run_server(debug=True)

**Card Specification Reference:**

Metric Card:
  - **Required**: ``type="metric"``, ``column``, ``agg``, ``title``
  - **Optional**: ``color`` (success, info, primary, danger, warning, secondary)
  - **Example**: ``{"type": "metric", "column": "Sales", "agg": "sum", "title": "Total Sales", "color": "success"}``

Chart Card:
  - **Required**: ``type="chart"``, ``plot_type``, ``x``, ``y``, ``title``
  - **Optional**: ``color`` (for color mapping), ``size`` (for scatter plots)
  - **Example**: ``{"type": "chart", "plot_type": "bar", "x": "Product", "y": "Sales", "title": "Sales Chart"}``
  - **Plot types**: bar, line, scatter, histogram, box, violin, pie, etc.

Text Card:
  - **Required**: ``type="text"``, ``content``
  - **Supports**: Markdown formatting
  - **Example**: ``{"type": "text", "content": "## Analysis\n\nKey insights..."}``

**Advanced Mode:**

For full control with pre-built blocks:

.. code-block:: python

   from dashboard_lego.blocks import SingleMetricBlock, TypedChartBlock
   from dashboard_lego.core import DataSource, DataBuilder
   from dashboard_lego.utils import quick_dashboard

   # Create custom datasource
   class MyDataBuilder(DataBuilder):
       def build(self, params):
           # Your custom data loading logic
           return pd.read_csv("data.csv")

   datasource = DataSource(data_builder=MyDataBuilder())

   # Create custom blocks with full configuration
   blocks = [
       SingleMetricBlock(
           block_id="metric1",
           datasource=datasource,
           metric_spec={
               'column': 'Revenue',
               'agg': 'sum',
               'title': 'Total Revenue',
               'color': 'success'
           }
       ),
       TypedChartBlock(
           block_id="chart1",
           datasource=datasource,
           plot_type="bar",
           plot_params={"x": "Product", "y": "Sales"},
           title="Sales Chart"
       )
   ]

   # Create dashboard from blocks
   app = quick_dashboard(blocks=blocks, title="Custom Dashboard")
   app.run_server(debug=True)

**Installation:**

.. code-block:: bash

   # Install with Jupyter support
   pip install dashboard-lego[jupyter]

   # Or install jupyter-dash separately
   pip install jupyter-dash

**Features:**

1. **Zero disk I/O**: Uses in-memory data pipeline (``cache_ttl=0``)
2. **Smart layout**: Metrics grouped in compact row, charts max 2 per row
3. **Theme support**: All Bootstrap themes supported (lux, dark, light, cyborg, etc.)
4. **Universal**: Works in Jupyter, Python scripts, anywhere Dash runs
5. **Type safety**: Validates card specifications at runtime

Export Pattern
--------------

Export dashboard figures for static reports and notebooks.

**Single Figure:**

.. code-block:: python

   chart = TypedChartBlock(
       block_id="chart",
       datasource=datasource,
       plot_type="scatter",
       plot_params={"x": "X", "y": "Y"}
   )

   fig = chart.get_figure()
   fig.write_html("chart.html")

**Layout Export:**

.. code-block:: python

   layout = [[chart1, chart2], [chart3]]
   fig = export_layout_to_figure(layout, title="Dashboard")
   fig.write_html("dashboard.html")

See :ref:`guide-export` for complete documentation.

IPython Magic Commands
-----------------------

For even faster dashboard creation in Jupyter notebooks, Dashboard Lego provides
IPython magic commands that reduce code to a single line.

**Loading the Extension:**

.. code-block:: python

   %load_ext dashboard_lego.ipython_magics

**Magic 1: %dashboard (Line Magic)**

Create dashboard in one line:

.. code-block:: python

   # Syntax
   %dashboard df --metric column agg title [color] --chart plot_type x y title

   # Example
   %dashboard df -m Sales sum "Total Sales" success -c bar Product Sales "Sales Chart"

   # Short flags: -m (metric), -c (chart), -x (text), -t (title), -p (port)

**Magic 2: %dashboard_theme**

Set default theme for future dashboards:

.. code-block:: python

   # Set theme
   %dashboard_theme cyborg

   # View current theme and list all available
   %dashboard_theme

**Magic 3: %%dashboard_cell (Cell Magic)**

Multi-line YAML-like configuration:

.. code-block:: python

   %%dashboard_cell
   dataframe: df
   title: "Sales Analytics"
   theme: dark
   port: 8050
   cards:
     - metric: Revenue, sum, "Total Revenue", success
     - metric: Profit, sum, "Total Profit", warning
     - chart: bar, Product, Sales, "Sales Chart"
     - text: "## Summary\n\nKey insights..."

**Comparison:**

Traditional API (3 lines):

.. code-block:: python

   app = quick_dashboard(df=df, cards=[...])
   app.run(port=8050)

Magic command (1 line):

.. code-block:: python

   %dashboard df -m Sales sum "Total" -c bar Product Sales

**Use Cases:**

- Quick exploration and prototyping
- Interactive data analysis sessions
- Minimal typing for ephemeral dashboards
- Teaching and demonstrations

Placeholders Guide
------------------

Dashboard Lego supports ``{{placeholders}}`` in specific contexts for dynamic content. This guide explains where placeholders work and where they don't.

**Supported Contexts:**

1. **Plot Parameters (``plot_params``)**: Dynamic column selection and visual encoding
2. **Plot Title (``plot_title``)**: Dynamic chart title inside the plot
3. **Control Properties**: Dynamic control options and values

**Unsupported Contexts:**

1. **Card Title (``title``)**: Static card header (no placeholders)
2. **Text Content**: Static markdown content

**Best Practices:**

1. **Use ``plot_title`` for Dynamic Chart Titles**:

   .. code-block:: yaml

      # ✅ Good: Dynamic chart title
      - type: chart
        title: "Session Analysis"           # Static card header
        plot_title: "Analysis @ step={{window_step_selector}}"  # Dynamic chart title

      # ❌ Avoid: Placeholders in card title
      - type: chart
        title: "Analysis @ step={{window_step_selector}}"  # Won't work

2. **Use ``plot_params`` for Dynamic Visual Encoding**:

   .. code-block:: yaml

      # ✅ Good: Dynamic visual properties
      - type: chart
        plot_type: scatter
        x: session_length
        y: max_idle
        color: "{{metric_selector}}"       # Dynamic color
        size: "{{size_selector}}"          # Dynamic size

3. **Use Variable Interpolation for Control Options**:

   .. code-block:: yaml

      # ✅ Good: Dynamic control options
      environment:
        - metric_options
      cards:
        - type: control_panel
          controls:
            - name: metric_selector
              type: dropdown
              options: $metric_options      # Variable interpolation
              value: "{{default_metric}}"  # Placeholder for default

**Common Patterns:**

**Pattern 1: Interactive Scatter Plot**

.. code-block:: yaml

   cards:
     - type: control_panel
       title: "Select Metrics"
       controls:
         - name: color_metric
           type: dropdown
           options: $metric_options
           value: "n_sessions"
         - name: size_metric
           type: dropdown
           options: $metric_options
           value: "median_session_length"

     - type: chart
       title: "Session Analysis"                    # Static card title
       plot_type: scatter
       x: session_length
       y: max_idle
       color: "{{color_metric}}"                    # Dynamic color
       size: "{{size_metric}}"                      # Dynamic size
       plot_title: "Sessions vs Idle @ {{color_metric}}"  # Dynamic plot title

**Pattern 2: Parameterized Analysis**

.. code-block:: yaml

   cards:
     - type: control_panel
       title: "Analysis Parameters"
       controls:
         - name: window_step
           type: slider
           min: 1
           max: 10
           value: 1

     - type: chart
       title: "Parameter Analysis"                  # Static card title
       plot_type: scatter
       x: session_length
       y: max_idle
       plot_title: "Analysis @ step={{window_step}}"  # Dynamic plot title

**Troubleshooting:**

**Problem: Placeholder not resolving**
- **Symptoms**: ``{{placeholder}}`` appears literally in output
- **Solutions**: Check placeholder name matches control name exactly, ensure control is subscribed to the chart, verify placeholder is in supported context

**Problem: Card title not updating**
- **Symptoms**: Card title stays static when controls change
- **Solutions**: Use ``plot_title`` instead of ``title`` for dynamic content, keep ``title`` static for card header

**Problem: Control not affecting chart**
- **Symptoms**: Changing controls doesn't update chart
- **Solutions**: Check ``subscribes_to`` includes correct state IDs, verify control names match placeholder names, ensure control publishes state changes
