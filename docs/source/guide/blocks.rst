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
       datasource: BaseDataSource,
       plot_type: str,              # Name of the plot function from the registry
       plot_params: Dict[str, Any] = None,  # Params with {{placeholders}} for controls
       plot_kwargs: Dict[str, Any] = None,  # Static kwargs for the plot function
       title: str = "",
       controls: Optional[Dict[str, Control]] = None,  # Optional embedded controls
       subscribes_to: Union[str, List[str], None] = None,
       transform_fn: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,  # NEW in v0.15
       **kwargs
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

MetricsBlock
------------

**Location:** ``dashboard_lego.blocks.metrics``

Display aggregated metrics from filtered data (replaces get_kpis pattern).

**Constructor:**

.. code-block:: python

   def __init__(
       self,
       block_id: str,
       datasource: BaseDataSource,
       metrics_spec: Dict[str, Dict[str, Any]],
       subscribes_to: Union[str, List[str], None] = None,
       **kwargs
   )

**Metrics Spec Format:**

.. code-block:: python

   metrics_spec = {
       'metric_id': {
           'column': str,           # Column name to aggregate
           'agg': str | Callable,   # Aggregation function
           'title': str,            # Display title
           'color': str,            # Bootstrap color (optional)
           'dtype': str             # Type conversion (optional)
       }
   }

**Example:**

.. code-block:: python

   from dashboard_lego.blocks import MetricsBlock

   metrics = MetricsBlock(
       block_id="sales_metrics",
       datasource=datasource,
       metrics_spec={
           'total_revenue': {
               'column': 'Revenue',
               'agg': 'sum',
               'title': 'Total Revenue',
               'color': 'success'
           },
           'avg_price': {
               'column': 'Price',
               'agg': 'mean',
               'title': 'Average Price',
               'color': 'info'
           }
       },
       subscribes_to=['control-category']
   )

ControlPanelBlock
-----------------

**Location:** ``dashboard_lego.blocks.control_panel``

Standalone control panel for global filters/settings.

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
