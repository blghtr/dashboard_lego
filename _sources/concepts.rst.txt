Core Concepts
==============

Understanding the key concepts of Dashboard Lego will help you build better dashboards.

Modular Architecture
--------------------

Dashboard Lego is built around the concept of modular, reusable components called "blocks". Each block is a self-contained unit that:

* Displays specific content (KPIs, charts, text)
* Manages its own data requirements
* Can interact with other blocks through state management
* Can be easily combined to create complex dashboards

Block Types
-----------

BaseBlock
~~~~~~~~~

All blocks inherit from :class:`BaseBlock`, which provides:

* Unique identification system
* State management integration
* Layout and styling capabilities
* Callback registration

Chart Blocks
~~~~~~~~~~~~

* :class:`StaticChartBlock`: Non-interactive charts that display data
* :class:`InteractiveChartBlock`: Charts with controls (dropdowns, sliders, etc.)

Data Display Blocks
~~~~~~~~~~~~~~~~~~~

* :class:`KPIBlock`: Key Performance Indicators with metrics
* :class:`TextBlock`: Text content and markdown

Data Sources
------------

Data sources abstract data loading and provide a consistent interface for blocks. They handle:

* Data loading from various sources (CSV, Parquet, SQL, etc.)
* Caching for performance
* Filtering and aggregation
* KPI calculations

State Management
----------------

Dashboard Lego uses a publish-subscribe pattern for block interaction:

* **Publishers**: Blocks that emit state changes (e.g., filter selections)
* **Subscribers**: Blocks that react to state changes (e.g., charts that update)
* **StateManager**: Central coordinator that manages state flow

Example of state flow:

.. code-block:: python

   # Block A publishes filter state
   interactive_chart = InteractiveChartBlock(
       block_id="filter_chart",
       controls={"category": Control(...)}
   )

   # Block B subscribes to filter state
   kpi_block = KPIBlock(
       block_id="filtered_kpis",
       subscribes_to="filter_chart-category"  # Subscribes to category filter
   )

Layout System
-------------

Dashboard Lego uses a flexible grid system based on Bootstrap:

* **Rows**: Horizontal groups of blocks
* **Columns**: Bootstrap grid columns (1-12 width)
* **Responsive**: Different layouts for different screen sizes
* **Presets**: Pre-built layout patterns for common arrangements

Example layout:

.. code-block:: python

   # Two-column layout: 8 columns + 4 columns
   layout = [
       [(chart_block, {'md': 8}), (kpi_block, {'md': 4})]
   ]

Presets
-------

Presets are pre-built blocks for common use cases:

* **EDA Presets**: Exploratory data analysis visualizations
* **ML Presets**: Machine learning model visualizations
* **Layout Presets**: Common dashboard arrangements

Block-Level Data Transformations
---------------------------------

Dashboard Lego v0.16.0 introduces block-specific data transformations, allowing each
block to apply custom transformations (aggregation, filtering, pivoting) to the data
it displays without affecting other blocks.

Overview
~~~~~~~~

The ``transform_fn`` parameter enables blocks to define their own data transformation
logic that executes **after** the global data pipeline. This allows for:

* Block-specific aggregations (groupby, pivot tables)
* Custom filtering without affecting other blocks
* Data reshaping for specific visualizations
* Complex multi-step transformations

Data Flow
~~~~~~~~~

The complete data pipeline with block transforms:

.. code-block:: text

    1. Data Builder (load + process)
           ↓
    2. Global Filter (optional)
           ↓
    3. Block Transform (if specified) ← NEW in v0.15.0
           ↓
    4. Block Rendering

Each block with a ``transform_fn`` gets a specialized datasource that chains
the transform after the global filter.

Basic Usage
~~~~~~~~~~~

.. code-block:: python

   from dashboard_lego.blocks.typed_chart import TypedChartBlock

   # Block without transform - shows raw data
   raw_chart = TypedChartBlock(
       block_id="raw_sales",
       datasource=datasource,
       plot_type='scatter',
       plot_params={'x': 'date', 'y': 'sales'}
   )

   # Block with aggregation transform
   aggregated_chart = TypedChartBlock(
       block_id="category_totals",
       datasource=datasource,
       plot_type='bar',
       plot_params={'x': 'category', 'y': 'total_sales'},
       transform_fn=lambda df: df.groupby('category')['sales'].sum().reset_index(name='total_sales')
   )

Common Patterns
~~~~~~~~~~~~~~~

**Aggregation:**

.. code-block:: python

   # Group by category and sum sales
   transform_fn=lambda df: df.groupby('category')['sales'].sum().reset_index()

**Filtering:**

.. code-block:: python

   # Show only high-value transactions
   transform_fn=lambda df: df[df['sales'] > 1000]

**Pivot Tables:**

.. code-block:: python

   # Create category × region matrix
   transform_fn=lambda df: df.pivot_table(
       index='category',
       columns='region',
       values='sales',
       aggfunc='mean'
   )

**Complex Multi-Step:**

.. code-block:: python

   def complex_transform(df):
       # Step 1: Filter
       filtered = df[df['category'] == 'Electronics']
       # Step 2: Aggregate
       grouped = filtered.groupby('region')['sales'].sum()
       # Step 3: Calculate metrics
       return grouped.reset_index(name='total_sales')

   transform_fn=complex_transform

Key Concepts
~~~~~~~~~~~~

**Immutability:**
  The original datasource is never modified. Each block with a ``transform_fn``
  gets an independent specialized clone.

**Order Matters:**
  Transforms execute in order: Build → Global Filter → Block Transform

**Independence:**
  Multiple blocks can have different transforms on the same datasource without
  interfering with each other.

**Caching:**
  Each specialized datasource maintains independent cache keys, so transforms
  are only computed once.

Example Scenarios
~~~~~~~~~~~~~~~~~

**Scenario 1: Different Aggregations**

.. code-block:: python

   # Dashboard showing same data aggregated different ways
   sales_by_category = TypedChartBlock(
       block_id="by_category",
       datasource=datasource,
       plot_type='bar',
       plot_params={'x': 'category', 'y': 'total'},
       transform_fn=lambda df: df.groupby('category')['sales'].sum().reset_index(name='total')
   )

   sales_by_region = TypedChartBlock(
       block_id="by_region",
       datasource=datasource,
       plot_type='bar',
       plot_params={'x': 'region', 'y': 'total'},
       transform_fn=lambda df: df.groupby('region')['sales'].sum().reset_index(name='total')
   )

**Scenario 2: With Global Filters**

.. code-block:: python

   # Global filter applies first, then block transform
   datasource = BaseDataSource(
       data_builder=builder,
       data_transformer=DateRangeFilter()  # Global filter
   )

   # This block will:
   # 1. Apply DateRangeFilter (global)
   # 2. Then aggregate by category (block-specific)
   chart = TypedChartBlock(
       block_id="filtered_totals",
       datasource=datasource,
       plot_type='bar',
       plot_params={'x': 'category', 'y': 'total'},
       transform_fn=lambda df: df.groupby('category')['sales'].sum().reset_index(name='total')
   )

Best Practices
--------------

Block Design
~~~~~~~~~~~~

* Keep blocks focused on a single responsibility
* Use meaningful block IDs
* Implement proper error handling
* Document data requirements

State Management
~~~~~~~~~~~~~~~~

* Use descriptive state names
* Avoid circular dependencies
* Group related state changes
* Handle state initialization properly

Data Transformations
~~~~~~~~~~~~~~~~~~~~

* Keep transform functions simple and readable
* Use descriptive lambda names for complex transforms
* Consider extracting complex transforms to named functions
* Remember: transforms execute after global filters
* Test transforms independently before adding to blocks

Performance
~~~~~~~~~~~

* Use data source caching
* Implement efficient data filtering
* Minimize callback complexity
* Use appropriate chart types for data size
* Block transforms are cached automatically

Layout Design
~~~~~~~~~~~~~

* Use layout presets when possible
* Consider responsive design
* Group related blocks together
* Maintain consistent spacing and alignment
