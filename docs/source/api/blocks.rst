Blocks Module
==============

The blocks module contains the building blocks for creating dashboard components.

Base Block
----------

.. automodule:: dashboard_lego.blocks.base
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: dashboard_lego.blocks.base.BaseBlock
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Block-Level Transformations (v0.16.0+)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

All blocks support an optional ``transform_fn`` parameter that enables block-specific
data transformations without affecting other blocks or the original datasource.

**Parameters:**

* ``transform_fn`` (Optional[Callable[[pd.DataFrame], pd.DataFrame]]): A function that
  transforms the DataFrame before visualization. The function receives the DataFrame
  after global filters have been applied and should return a transformed DataFrame.

**Example:**

.. code-block:: python

   from dashboard_lego.blocks.typed_chart import TypedChartBlock

   # Simple aggregation transform
   chart = TypedChartBlock(
       block_id="category_sales",
       datasource=datasource,
       plot_type='bar',
       plot_params={'x': 'category', 'y': 'total'},
       transform_fn=lambda df: df.groupby('category')['sales'].sum().reset_index(name='total')
   )

**Common Use Cases:**

* Aggregation: ``lambda df: df.groupby('column').agg({'metric': 'sum'})``
* Filtering: ``lambda df: df[df['value'] > threshold]``
* Pivot: ``lambda df: df.pivot_table(index='x', columns='y', values='z')``
* Complex transforms: Define a function with multiple steps

**Technical Details:**

* Transform executes **after** global filters (Build → Global Filter → Block Transform)
* Each block with ``transform_fn`` gets an independent specialized datasource clone
* Original datasource remains unchanged (immutable pattern)
* Transforms are cached for performance

See :doc:`../concepts` for detailed information on block-level transformations.

Chart Blocks
------------

.. automodule:: dashboard_lego.blocks.chart
   :members:
   :undoc-members:
   :show-inheritance:

Static Chart Block
^^^^^^^^^^^^^^^^^^

.. autoclass:: dashboard_lego.blocks.chart.StaticChartBlock
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Interactive Chart Block
^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: dashboard_lego.blocks.chart.InteractiveChartBlock
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Control Class
^^^^^^^^^^^^^

.. autoclass:: dashboard_lego.blocks.chart.Control
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

KPI Block
---------

.. automodule:: dashboard_lego.blocks.kpi
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: dashboard_lego.blocks.kpi.KPIBlock
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Text Block
----------

.. automodule:: dashboard_lego.blocks.text
   :members:
   :undoc-members:
   :show-inheritance:

.. autoclass:: dashboard_lego.blocks.text.TextBlock
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:
