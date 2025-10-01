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

Performance
~~~~~~~~~~~

* Use data source caching
* Implement efficient data filtering
* Minimize callback complexity
* Use appropriate chart types for data size

Layout Design
~~~~~~~~~~~~~

* Use layout presets when possible
* Consider responsive design
* Group related blocks together
* Maintain consistent spacing and alignment
