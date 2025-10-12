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

   Control Panel → Params → BaseDataSource → Build → Transform → Blocks
                                ↓              ↓         ↓
                            Classifier      Cache     Cache

**Example:**

.. code-block:: python

   from dashboard_lego.core import BaseDataSource, DataBuilder, DataTransformer

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
   datasource = BaseDataSource(
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

Jupyter Quick Start Pattern
----------------------------

The ``quick_dashboard()`` factory enables rapid prototyping in Jupyter notebooks
with minimal code. Supports simple mode (DataFrame + card specs) and advanced mode
(pre-built blocks).

**Simple Mode:**

For quick exploration with 1-4 cards:

.. code-block:: python

   from dashboard_lego.utils import quick_dashboard
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
   from dashboard_lego.core import BaseDataSource, DataBuilder
   from dashboard_lego.utils import quick_dashboard

   # Create custom datasource
   class MyDataBuilder(DataBuilder):
       def build(self, params):
           # Your custom data loading logic
           return pd.read_csv("data.csv")

   datasource = BaseDataSource(data_builder=MyDataBuilder())

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
2. **Automatic layout**: Selects optimal grid based on card count (1-4)
3. **Theme support**: All Bootstrap themes supported (lux, dark, light, cyborg, etc.)
4. **JupyterDash integration**: Inline display if jupyter-dash installed, graceful fallback otherwise
5. **Type safety**: Validates card specifications at runtime

**Layout Selection:**

- 1 card: Full width (12 columns)
- 2 cards: 50/50 split (6/6 columns)
- 3 cards: 33/33/33 split (4/4/4 columns)
- 4 cards: 2x2 grid (two rows of 6/6 columns)
