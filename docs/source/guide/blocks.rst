.. _guide-blocks:

Blocks Module API
=================

Visual components for building dashboards.

.. contents::
   :local:
   :depth: 2

BaseBlock
---------

**Location:** ``dashboard_lego.blocks.base``

Abstract base class for all dashboard blocks.

For detailed API documentation, see :ref:`api-blocks`.

TypedChartBlock
---------------

**Location:** ``dashboard_lego.blocks.typed_chart``

**Status:** ✅ **RECOMMENDED & UNIFIED (v0.15+)**

Unified chart block using a plot registry with optional embedded controls.

**Key Features:**

-   ✅ **Unified API**: One block for both static and interactive charts
-   ✅ **Reusable Plots**: Central plot registry promotes code reuse
-   ✅ **Declarative**: Define charts with parameters, not imperative code
-   ✅ **Block-Level Transformations**: ``transform_fn`` allows for powerful, localized data manipulation
-   ✅ **Robust**: Works correctly in navigation sections and with embedded controls

**Constructor:**

.. code-block:: python

   def __init__(
       self,
       block_id: str,
       datasource: DataSource,
       plot_type: str,              # Name of the plot function from the registry
       plot_params: Dict[str, Any] = None,  # Params with {{placeholders}} for controls
       plot_kwargs: Dict[str, Any] = None,  # Static kwargs for the plot function
       title: Optional[str] = None,         # Static card title (no placeholders)
       plot_title: Optional[str] = None,   # Dynamic plot title (supports {{placeholders}})
       controls: Optional[Dict[str, Control]] = None,  # Optional embedded controls
       subscribes_to: Union[str, List[str], None] = None,
       transform_fn: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,  # NEW in v0.15
       **kwargs
   )

**Title vs Plot Title (v0.15+):**

Dashboard Lego separates static card titles from dynamic plot titles:

- **``title``**: Static card header (no placeholder support)
- **``plot_title``**: Dynamic plot title (supports ``{{placeholders}}``)

**Example:**

.. code-block:: python

   chart = TypedChartBlock(
       block_id="sales_chart",
       datasource=datasource,
       plot_type="scatter",
       plot_params={"x": "date", "y": "sales", "color": "{{metric_selector}}"},
       title="Sales Analysis",                    # Static card title
       plot_title="Sales by {{metric_selector}}", # Dynamic plot title with placeholder
       subscribes_to=["metric_selector"]
   )

**Block-Level Data Transformations (v0.15):**

The ``transform_fn`` parameter allows blocks to apply custom data transformations (aggregation, pivoting, filtering) *after* global filters but *before* plotting.

**Example:**

.. code-block:: python

   top_products_chart = TypedChartBlock(
       block_id="top_products",
       datasource=datasource,
       plot_type='bar',
       plot_params={'x': 'Product', 'y': 'total_revenue'},
       title="Top 10 Products by Revenue",
       subscribes_to=['filters-category'],
       transform_fn=lambda df: (
           df.groupby('Product')['Revenue']
             .sum()
             .reset_index(name='total_revenue')
             .sort_values('total_revenue', ascending=False)
             .head(10)
       )
   )

Metrics Factory Pattern
------------------------

**Location:** ``dashboard_lego.blocks.metrics_factory``

**Status:** ✅ **RECOMMENDED (v0.15+)**

Factory function to create individual metric blocks for flexible layout.

**Why Factory Pattern?**

- ✅ **Composable**: Mix metrics with other blocks naturally
- ✅ **Layout Compliant**: Proper equal-height rows via flexbox
- ✅ **Compact**: No empty space in metric cards
- ✅ **Theme-Aware**: Colors resolved via ThemeConfig

**Factory Function:**

.. code-block:: python

   def get_metric_row(
       metrics_spec: Dict[str, Dict[str, Any]],
       datasource: DataSource,
       subscribes_to: Optional[Union[str, List[str]]] = None,
       row_options: Optional[Dict[str, Any]] = None,
       block_id_prefix: str = "metric",
   ) -> Tuple[List[SingleMetricBlock], Dict[str, Any]]

**Metrics Spec Format:**

.. code-block:: python

   metrics_spec = {
       'metric_id': {
           'column': str,           # Column name to aggregate
           'agg': str | Callable,   # Aggregation function
           'title': str,            # Display title
           'color': str,            # Bootstrap theme color
           'dtype': str,            # Type conversion (optional)
           'color_rules': dict      # Conditional coloring (optional)
       }
   }

**Example:**

.. code-block:: python

   from dashboard_lego.blocks import get_metric_row

   metrics, row_opts = get_metric_row(
       metrics_spec={
           'total_revenue': {
               'column': 'Revenue',
               'agg': 'sum',
               'title': 'Total Revenue',
               'color': 'success'  # Bootstrap theme color
           },
           'avg_price': {
               'column': 'Price',
               'agg': 'mean',
               'title': 'Average Price',
               'color': 'info'
           },
           'units_sold': {
               'column': 'Quantity',
               'agg': 'sum',
               'title': 'Units Sold',
               'color': 'primary'
           }
       },
       datasource=datasource,
       subscribes_to=['filters-category']
   )

   # Use in page layout
   page = DashboardPage(
       title="Dashboard",
       blocks=[
           (metrics, row_opts),  # Metrics row
           [chart1, chart2]      # Charts row
       ]
   )

**Conditional Coloring (Optional):**

.. code-block:: python

   metrics_spec = {
       'profit_margin': {
           'column': 'Profit',
           'agg': lambda df: df['Profit'].sum() / df['Revenue'].sum(),
           'title': 'Profit Margin %',
           'color_rules': {
               'thresholds': [0.0, 0.15, 0.30],
               'colors': ['danger', 'warning', 'success']
               # < 0%: danger, 0-15%: warning, 15-30%: success
           }
       }
   }

MetricsBlock (Deprecated)
--------------------------

**Status:** ⚠️ **DEPRECATED** - Use ``get_metric_row()`` for new applications.

.. deprecated:: 0.15.0
   Use :func:`get_metric_row` instead. MetricsBlock violates layout contracts
   by returning dbc.Row internally.

The ``MetricsBlock`` is maintained for backward compatibility but returns
a composite Row component, preventing proper equal-height layout integration.

ControlPanelBlock
-----------------

**Location:** ``dashboard_lego.blocks.control_panel``

Standalone control panel for global filters/settings.

**Control Defaults:**
- Sliders: Full width (``{"xs": 12, "md": 12}``) with ``modern-slider`` CSS class
- Dropdowns: Narrow width (``{"xs": 12, "md": 4}``) with ``compact-dropdown`` CSS class
- Other controls: Auto width (``{"xs": 12, "md": "auto"}``)

**Available CSS Classes:**
- ``modern-slider``: Modern styling for sliders with proper width and colors (uses CSS, not inline styles)
- ``compact-dropdown``: Compact styling for dropdowns to save space

Override defaults by specifying ``col_props`` and ``className`` in your control specifications.
Note: ``dcc.Slider`` doesn't support ``style`` prop - use ``className`` for styling.

See :ref:`api-blocks` for detailed documentation.

TextBlock
---------

**Location:** ``dashboard_lego.blocks.text``

Display dynamic markdown or HTML text content.

See :ref:`api-blocks` for detailed documentation.

KPIBlock (Deprecated)
---------------------

**Status:** ⚠️ **DEPRECATED** - Use ``MetricsBlock`` for new applications.

The ``KPIBlock`` relied on the ``datasource.get_kpis()`` method, which was removed in v0.15.0. The new ``MetricsBlock`` provides a more powerful and flexible declarative API.
