.. _guide-reference:

Quick Reference
===============

Quick reference for common tasks and configurations.

.. contents::
   :local:

Class Summary
-------------

Data Pipeline (v0.15)
^^^^^^^^^^^^^^^^^^^^^

- **BaseDataSource**: Concrete data source with 2-stage pipeline → ``get_processed_data(params)``
- **DataBuilder**: Data building stage (load + process) → ``build(params)``
- **DataTransformer**: Data transformation stage → ``transform(data, params)``

Data Sources
^^^^^^^^^^^^

- **CsvDataSource**: Load CSV files → ``__init__(file_path, **kwargs)``
- **ParquetDataSource**: Load Parquet files → ``__init__(file_path, **kwargs)``
- **SqlDataSource**: Load from databases → ``__init__(connection, query)``

Core Components
^^^^^^^^^^^^^^^

- **DashboardPage**: Main orchestrator → ``build_layout()``, ``register_callbacks()``
- **StateManager**: State coordination → ``register_publisher()``, ``bind_callbacks()``
- **ThemeConfig**: Theme configuration → ``light_theme()``, ``dark_theme()``, ``get_figure_layout()``

Blocks
^^^^^^

- **BaseBlock**: Abstract block → ``layout()``, ``output_target()``
- **MetricsBlock**: Metrics from data → ``__init__(metrics_spec)``
- **TypedChartBlock**: Chart with plot registry → ``__init__(plot_type, plot_params)``
- **ControlPanelBlock**: Control panel only → ``__init__(controls)``
- **TextBlock**: Text/markdown → ``__init__(content_generator)``

Configuration Options
---------------------

Bootstrap Grid System
^^^^^^^^^^^^^^^^^^^^^

+-------------+---------------+---------------+
| Breakpoint  | Screen Width  | Column Width  |
+=============+===============+===============+
| ``xs``      | <576px        | 1-12          |
+-------------+---------------+---------------+
| ``sm``      | ≥576px        | 1-12          |
+-------------+---------------+---------------+
| ``md``      | ≥768px        | 1-12          |
+-------------+---------------+---------------+
| ``lg``      | ≥992px        | 1-12          |
+-------------+---------------+---------------+
| ``xl``      | ≥1200px       | 1-12          |
+-------------+---------------+---------------+

**Default:** If no width specified, columns auto-size equally

State Naming Convention
^^^^^^^^^^^^^^^^^^^^^^^

+-----------------------------------+------------------------+---------------------------+
| Pattern                           | Example                | Usage                     |
+===================================+========================+===========================+
| ``{block_id}-{control_name}``     | ``filters-category``   | Control panel state       |
+-----------------------------------+------------------------+---------------------------+
| ``dummy_state``                   | ``dummy_state``        | Static blocks (no pub)    |
+-----------------------------------+------------------------+---------------------------+

Loading Types
^^^^^^^^^^^^^

+----------------+------------------------+
| Type           | Appearance             |
+================+========================+
| ``"default"``  | Spinner                |
+----------------+------------------------+
| ``"graph"``    | Graph-specific loader  |
+----------------+------------------------+
| ``"cube"``     | Cube animation         |
+----------------+------------------------+
| ``"circle"``   | Circle animation       |
+----------------+------------------------+
| ``"dot"``      | Dot animation          |
+----------------+------------------------+

Common Patterns
---------------

Minimal Dashboard
^^^^^^^^^^^^^^^^^

.. code-block:: python

   import dash
   import dash_bootstrap_components as dbc
   from dashboard_lego import DashboardPage
   from dashboard_lego.core import BaseDataSource, DataBuilder
   from dashboard_lego.blocks import MetricsBlock

   class MyDataBuilder(DataBuilder):
       def build(self, params):
           return pd.read_csv("data.csv")

   datasource = BaseDataSource(data_builder=MyDataBuilder())

   metrics = MetricsBlock(
       block_id="metrics",
       datasource=datasource,
       metrics_spec={
           "total": {"column": "id", "agg": "count", "title": "Total"}
       },
       subscribes_to="dummy_state"
   )

   page = DashboardPage(title="Dashboard", blocks=[[metrics]])

   app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
   app.layout = page.build_layout()
   page.register_callbacks(app)
   app.run_server(debug=True)

Interactive Dashboard
^^^^^^^^^^^^^^^^^^^^^

.. code-block:: python

   control_panel = ControlPanelBlock(
       block_id="controls",
       datasource=datasource,
       title="Filters",
       controls={"category": Control(...)}
   )

   chart = TypedChartBlock(
       block_id="chart",
       datasource=datasource,
       plot_type='bar',
       plot_params={'x': 'Product', 'y': 'Sales'},
       subscribes_to="controls-category"
   )

   page = DashboardPage(
       title="Interactive Dashboard",
       blocks=two_column_8_4(main=chart, side=control_panel)
   )

Error Handling
--------------

+----------------------------+------------------------+-----------------------------------------+
| Exception                  | When Raised            | Recommended Action                      |
+============================+========================+=========================================+
| ``DataLoadError``          | Data loading fails     | Check file path, permissions, format    |
+----------------------------+------------------------+-----------------------------------------+
| ``CacheError``             | Cache operation fails  | Check cache directory permissions       |
+----------------------------+------------------------+-----------------------------------------+
| ``ConfigurationError``     | Invalid parameters     | Verify constructor arguments            |
+----------------------------+------------------------+-----------------------------------------+
| ``BlockError``             | Block operation fails  | Check block_id uniqueness, datasource   |
+----------------------------+------------------------+-----------------------------------------+
| ``StateError``             | State management fails | Check for duplicate outputs, circular   |
|                            |                        | dependencies                            |
+----------------------------+------------------------+-----------------------------------------+

Performance Tips
----------------

1. **Use Disk Cache:** Set ``cache_dir`` for persistent caching
2. **Tune Cache TTL:** Balance freshness vs performance
3. **Lazy Loading:** Use navigation for large dashboards
4. **Data Filtering:** Filter at datasource level, not in generators
5. **Parquet Format:** Use for large datasets (faster than CSV)
6. **Block-Centric Callbacks:** Built-in optimization (one callback per block)
7. **Staged Pipeline:** Use DataBuilder + DataTransformer for optimal caching
