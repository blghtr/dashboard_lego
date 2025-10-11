.. _guide-core:

Core Module API
===============

This section documents the core components that form the foundation of dashboard_lego.

.. contents::
   :local:
   :depth: 2

BaseDataSource
--------------

**Location:** ``dashboard_lego.core.datasource``

**Hierarchy:** ``[Core | DataSources | BaseDataSource]``

**Purpose:** Concrete data source with a 2-stage processing pipeline using composition.

Pipeline Architecture (v0.15)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Data flows through a 2-stage pipeline with independent caching at each stage. This is a shift from the previous 3-stage model.

.. code-block:: text

   ┌─────────────┐     ┌────────────────┐     ┌──────────┐
   │ DataBuilder │ --> │ DataTransformer│ --> │ Output   │
   │ (Build)     │     │ (Transform)    │     │ (Blocks) │
   └─────────────┘     └────────────────┘     └──────────┘
         ↑                      ↑
         │                      │
      build                  transform
      params                 params

**Contract:**

.. code-block:: python

   :contract:
    - pre: data_builder and data_transformer are provided to the constructor via composition.
    - post: Data flows through the 2-stage pipeline: build → transform.
    - invariant: get_processed_data() always runs the pipeline, leveraging the cache at each stage.
    - no_abstract_methods: BaseDataSource is fully concrete and should not be subclassed for data loading.

Key Architectural Changes (v0.15)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

1.  **Simpler 2-Stage Pipeline**: The previous ``Load → Preprocess → Filter`` pipeline is now ``Build → Transform``.
2.  **Semantic Clarity**: ``Build`` clearly means "construct the complete dataset from a source". ``Transform`` means "apply any df→df transformation" (filtering, aggregation, etc.).
3.  **Composition over Inheritance**: ``BaseDataSource`` is now a concrete class. You no longer subclass it. Instead, you provide ``DataBuilder`` and ``DataTransformer`` instances to its constructor.
4.  **Staged Caching**: Changing ``transform`` parameters (e.g., from a filter control) will only re-run the second stage, reusing the cached result from the ``build`` stage for better performance.

Constructor
^^^^^^^^^^^

.. code-block:: python

   def __init__(
       self,
       data_builder: Optional[DataBuilder] = None,
       data_transformer: Optional[DataTransformer] = None,
       param_classifier: Optional[Callable[[str], str]] = None,
       cache_dir: Optional[str] = None,
       cache_ttl: int = 300,
       **kwargs
   )

**Pipeline Parameters:**

- ``data_builder``: A ``DataBuilder`` instance for Stage 1 (loading and initial processing).
- ``data_transformer``: A ``DataTransformer`` instance for Stage 2 (filtering, aggregation, reshaping).
- ``param_classifier``: A function that routes parameters from controls to the correct pipeline stage. It must return either ``'build'`` or ``'transform'``.

**Param Classifier Example:**

.. code-block:: python

   def classify_params(param_key: str) -> str:
       """Route params to the correct pipeline stage."""
       # Params from filter controls go to the transform stage.
       if param_key.startswith('filters-'):
           return 'transform'
       # All other params go to the build stage.
       return 'build'

   datasource = BaseDataSource(
       data_builder=MyDataBuilder(),
       data_transformer=MyDataTransformer(),
       param_classifier=classify_params
   )

Public Methods
^^^^^^^^^^^^^^

.. code-block:: python

   def get_processed_data(self, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
       """
       Runs the 2-stage pipeline and returns the final, transformed data.

       Args:
           params: A dictionary of parameters for both build and transform stages.

       Returns:
           A transformed DataFrame.

       Pipeline Stages:
           1. Classify params into 'build' vs 'transform' categories.
           2. Build data (cached by build params).
           3. Transform data (cached by transform params).
       """

   def with_transform_fn(self, transform_fn: Callable[[pd.DataFrame], pd.DataFrame]) -> "BaseDataSource":
       """
       Creates a new, specialized datasource instance with an additional transformation.
       This is the key to block-level transformations.
       """

Implementation Example (v0.15 Pattern)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   from dashboard_lego.core import BaseDataSource, DataBuilder, DataTransformer
   from dashboard_lego.blocks import MetricsBlock
   import pandas as pd

   # Step 1: Define a DataBuilder (combines loading and initial processing)
   class SalesDataBuilder(DataBuilder):
       def __init__(self, file_path: str, **kwargs):
           super().__init__(**kwargs)
           self.file_path = file_path

       def build(self, params: dict) -> pd.DataFrame:
           # Load AND process in one method
           df = pd.read_csv(self.file_path)
           df['Revenue'] = df['Price'] * df['Quantity']
           df['Date'] = pd.to_datetime(df['Date'])
           return df

   # Step 2: Define a DataTransformer (for filtering, aggregation, etc.)
   class SalesTransformer(DataTransformer):
       def transform(self, data: pd.DataFrame, params: dict) -> pd.DataFrame:
           df = data.copy()
           if 'filters-category' in params:
               category = params['filters-category']
               if category and category != 'All':
                   df = df[df['Category'] == category]
           # ... other transformations
           return df

   # Step 3: Define a parameter classifier
   def param_classifier(key: str) -> str:
       return 'transform' if key.startswith('filters-') else 'build'

   # Step 4: Create the DataSource instance using composition
   datasource = BaseDataSource(
       data_builder=SalesDataBuilder("sales.csv"),
       data_transformer=SalesTransformer(),
       param_classifier=param_classifier,
       cache_ttl=600
   )

   # Step 5: Use blocks like MetricsBlock to consume the data.
   # The get_kpis() method is removed from the datasource.
   metrics = MetricsBlock(
       block_id="sales_metrics",
       datasource=datasource,
       metrics_spec={
           'total_revenue': {'column': 'Revenue', 'agg': 'sum', 'title': 'Total Revenue'},
           'avg_price': {'column': 'Price', 'agg': 'mean', 'title': 'Avg Price'}
       },
       subscribes_to=['filters-category']
   )

DashboardPage
-------------

**Location:** ``dashboard_lego.core.page``

**Hierarchy:** ``[Core | Orchestration | DashboardPage]``

**Purpose:** Main orchestrator for dashboard lifecycle and layout

**Contract:**

.. code-block:: python

   :contract:
    - pre: Blocks must be provided via 'blocks' param or navigation sections
    - post: Complete Dash layout with registered callbacks
    - lifecycle: instantiate → build_layout() → register_callbacks() → serve

Constructor
^^^^^^^^^^^

.. code-block:: python

   def __init__(
       self,
       title: str = "Dashboard",
       blocks: Optional[LayoutSpec] = None,
       navigation: Optional[NavigationConfig] = None,
       theme: Optional[str] = None,  # dbc.themes.* URL
       theme_config: Optional[ThemeConfig] = None,
       **kwargs
   )

   # LayoutSpec format:
   # Single block: BaseBlock
   # Row: [block1, block2, ...] or [(block1, col_opts), ...]
   # Multiple rows: [[row1_blocks], [row2_blocks], ...]
   # With row options: [([blocks], row_opts), ...]

**Column Options:**

.. code-block:: python

   col_opts = {
       "xs": int,      # Width on extra-small screens (1-12)
       "sm": int,      # Width on small screens (1-12)
       "md": int,      # Width on medium screens (1-12)
       "lg": int,      # Width on large screens (1-12)
       "xl": int,      # Width on extra-large screens (1-12)
       "offset": int,  # Column offset (0-11)
       "align": str,   # Vertical align: "start"|"center"|"end"
       "className": str,
       "style": dict,
   }

**Row Options:**

.. code-block:: python

   row_opts = {
       "align": str,    # Vertical alignment: "start"|"center"|"end"
       "justify": str,  # Horizontal alignment: "start"|"center"|"end"|"between"|"around"
       "g": int,        # Gutter size (0-5)
       "className": str,
       "style": dict,
   }

Public Methods
^^^^^^^^^^^^^^

.. code-block:: python

   def build_layout(self) -> Component:
       """
       Constructs complete Dash layout from blocks.

       Returns:
           Dash Component tree ready for app.layout assignment

       Side effects:
           - Creates StateManager
           - Registers all blocks with StateManager
           - Injects theme_config into blocks
       """

   def register_callbacks(self, app: Dash) -> None:
       """
       Registers all callbacks with Dash app.

       Args:
           app: Dash application instance

       Side effects:
           - Calls state_manager.bind_callbacks() for block-centric callbacks
           - Registers navigation callbacks if navigation is enabled
       """

Layout Examples
^^^^^^^^^^^^^^^

.. code-block:: python

   # Simple one-column layout
   page = DashboardPage(
       title="My Dashboard",
       blocks=one_column([kpi_block, chart_block]),
       theme=dbc.themes.LUX
   )

   # Two-column layout with custom column widths
   page = DashboardPage(
       title="My Dashboard",
       blocks=[
           [(kpi_block, {"md": 8}), (sidebar_block, {"md": 4})]
       ]
   )

   # Complex multi-row layout
   page = DashboardPage(
       title="My Dashboard",
       blocks=[
           # KPI row (full width)
           [(kpi_block, {"md": 12})],
           # Two charts side-by-side
           [(chart1, {"md": 6}), (chart2, {"md": 6})],
           # Three cards in a row
           [(card1, {"md": 4}), (card2, {"md": 4}), (card3, {"md": 4})]
       ]
   )

For more core components (NavigationConfig, StateManager, ThemeConfig, DataBuilder, DataTransformer, DataProcessingContext, SidebarConfig), see the :ref:`API documentation <api-core>`.
