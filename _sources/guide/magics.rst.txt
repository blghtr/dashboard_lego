.. _guide-magics:

IPython Magic Commands
======================

Dashboard Lego provides IPython magic commands for ultra-fast dashboard creation and Plotly figure export directly from Jupyter notebooks.

Installation
------------

First, load the extension in your Jupyter notebook:

.. code-block:: python

   %load_ext dashboard_lego.ipython_magics

Dashboard Creation
------------------

Quick Dashboard from DataFrame
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Create dashboards from DataFrame variables with minimal code:

.. code-block:: python

   # Load data
   import pandas as pd
   df = pd.read_csv('sales_data.csv')

   # Create dashboard with metrics and charts
   %dashboard df
     title: "Sales Dashboard"
     theme: lux
     cards:
       - type: metric
         metric_spec:
           column: Sales
           agg: sum
           title: "Total Sales"
           color: success
       - type: metric
         metric_spec:
           column: Profit
           agg: sum
           title: "Total Profit"
           color: info
       - type: chart
         plot_type: bar
         plot_params: {x: Product, y: Sales}
         title: "Sales by Product"
       - type: chart
         plot_type: line
         plot_params: {x: Date, y: Sales}
         title: "Sales Trend"
       - type: text
         content_generator: |
           ## Summary

           Key insights from the data

   # Simple single chart dashboard
   %dashboard df
     cards:
       - type: chart
         plot_type: scatter
         plot_params: {x: Price, y: Sales}
         title: "Price vs Sales"

**Configuration Keys:**

- ``dataframe``: Name of DataFrame variable (required)
- ``title``: Dashboard title
- ``theme``: Theme name (uses current preference if not specified)
- ``port``: Server port (default: 8050)
- ``environment``: List of variable names to import from IPython namespace
- ``cards``: List of card specifications with optional controls

**Card Types (YAML = kwargs + type):**
- **Metric:** ``type: metric``, ``metric_spec: {column, agg, title, [color], [dtype]}``
- **Chart:** ``type: chart``, ``plot_type: str``, ``plot_params: {x, y, [color], [size]}``, ``title: str``, optional ``controls``
- **Minimal Chart:** ``type: minimal_chart``, ``plot_params: {x, y, ...}``, optional ``plot_type`` (defaults to ``scatter``), optional ``controls``
- **Text:** ``type: text``, ``content_generator: callable`` (returns str or Component)
- **Control Panel:** ``type: control_panel``, ``title: str``, ``controls: [...]``

.. note::
   YAML for magics MUST match block constructor kwargs (plus ``type``). No legacy
   top-level ``x/y`` or ``column/agg/title``. Use ``metric_spec``, ``plot_params``,
   and ``content_generator`` exactly as in the Python API.

**Control Types:**
- **Dropdown:** ``name``, ``type: dropdown``, ``options``, ``value``, ``col_props``
- **Slider:** ``name``, ``type: slider``, ``min``, ``max``, ``step``, ``value``, ``marks``
- **Input:** ``name``, ``type: input``, ``input_type``, ``placeholder``, ``value``

**Environment Variables:**
- Use ``$variable_name`` syntax to reference variables from IPython namespace
- Variables must be declared in ``environment`` list for security

Available themes: lux, dark, light, cyborg, slate, solar, superhero, minty, flatly, cosmo, cerulean, journal, litera, lumen, pulse, sandstone, simplex, sketchy, spacelab, united, yeti

Cell Magic Dashboard
^^^^^^^^^^^^^^^^^^^^

Create dashboards using YAML configuration in notebook cells with support for controls and environment variables:

.. code-block:: python

   %%dashboard_cell
   dataframe: df
   title: "Sales Dashboard"
   theme: lux
   environment:
     - metric_options
     - color_palette
   cards:
     - type: metric
       metric_spec:
         column: Sales
         agg: sum
         title: "Total Sales"
         color: success
     - type: chart
       plot_type: scatter
       plot_params: {x: Product, y: Sales}
       title: "Sales Analysis"
       controls:
         - name: metric_selector
           type: dropdown
           options: $metric_options
           value: "Sales"
           col_props: {xs: 12, md: 6}
         - name: year_slider
           type: slider
           min: 2020
           max: 2024
           step: 1
           value: 2023
           marks: {2020: "2020", 2024: "2024"}
           col_props: {xs: 12, md: 6}
     - type: text
       content_generator: |
         ## Summary

         Key insights from the data:
         - Sales increased by 15% this quarter
         - Top performing product is Electronics

Understanding Control Bindings
-------------------------------

How Controls Wire Together (NEW)
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Controls define what gets controlled through **state identifiers**. Here's how it works:

**1. Control Panel Publishes State**

When you define a ControlPanelBlock with controls, each control publishes its value as a state:

.. code-block:: python

   ControlPanelBlock(
       block_id="filters",  # ← This becomes part of state ID
       title="Filters",
       controls={
           "category": Control(...),  # ← State ID: "filters-category"
           "price": Control(...)      # ← State ID: "filters-price"
       }
   )

**State ID formula:** ``{block_id}-{control_name}``

Examples:
- ``filters-category``
- ``filters-price``
- ``session_controls-duration``

**2. Chart/Metric Subscribes to State**

Other blocks subscribe to these state IDs using ``subscribes_to``:

.. code-block:: python

   TypedChartBlock(
       block_id="sales_chart",
       plot_type="bar",
       plot_params={"x": "Product", "y": "Sales"},
       subscribes_to="filters-category"  # ← Subscribe to control panel state
   )

**3. State Changes Trigger Updates**

When user changes control value → state updates → all subscribers re-render

YAML Example: Control Panel with Chart
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Here's a complete example showing how controls bind to charts:

.. code-block:: yaml

   %%dashboard_cell
   dataframe: df
   title: "Interactive Dashboard"
   cards:
     # STEP 1: Define control panel
     - type: control_panel
       title: "Filters"
       controls:
         - name: category
           type: dropdown
           options:
             - {label: "Electronics", value: "Electronics"}
             - {label: "Furniture", value: "Furniture"}
             - {label: "Office Supplies", value: "Supplies"}
           value: "Electronics"
         - name: min_price
           type: slider
           min: 0
           max: 1000
           value: 100

     # STEP 2: Chart subscribes to control panel states
     - type: chart
       plot_type: scatter
       plot_params: {x: Product, y: Sales}
       title: "Sales by Category"
       # Subscribe to BOTH controls
       subscribes_to:
         - "control_panel-category"    # Listens to category dropdown
         - "control_panel-min_price"   # Listens to price slider

**What Happens:**

1. Control panel block_id is automatically ``control_panel`` in cell magic
2. Control names become state suffixes: ``control_panel-category``, ``control_panel-min_price``
3. Chart subscribes to these states
4. When dropdown changes → state ``control_panel-category`` updates → chart re-renders
5. When slider changes → state ``control_panel-min_price`` updates → chart re-renders

Multiple Charts from One Control Panel
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

.. code-block:: yaml

   %%dashboard_cell
   dataframe: df
   cards:
     # Single control panel
     - type: control_panel
       title: "Filters"
       controls:
         - name: region
           type: dropdown
           options: $region_list
           value: "North America"

     # Chart 1 subscribes
     - type: chart
       plot_type: bar
       plot_params: {x: Product, y: Revenue}
       subscribes_to: "control_panel-region"

     # Chart 2 subscribes to SAME control
     - type: chart
       plot_type: line
       plot_params: {x: Month, y: Profit}
       subscribes_to: "control_panel-region"

Result: Changing region filter updates **both** charts

Advanced: Chart with Embedded Controls
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

Charts can have their own internal controls that don't affect other blocks:

.. code-block:: yaml

   - type: chart
     plot_type: histogram
     plot_params: {x: Price}
     title: "Price Distribution"
     # These are chart-local controls (don't publish state)
     controls:
       - name: x_col
         type: dropdown
         options:
           - {label: "Price", value: "Price"}
           - {label: "Quantity", value: "Quantity"}
         value: "Price"

**Key Difference:**
- **Control Panel controls** → publish state → can control other blocks
- **Chart embedded controls** → private to chart → don't affect other blocks

Dynamic Marker Size Configuration
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

For scatter plots with variable marker sizes, you can configure consistent pixel-based sizing that adapts to your data range:

.. code-block:: yaml

   - type: chart
     plot_type: scatter_minimal
     plot_params: {x: session_length, y: max_idle, size: "{{metric_selector_2}}"}
     plot_kwargs:
       marker_size_max_px: 42
       marker_size_min_px: 8

**Configuration:**
- ``marker_size_max_px``: Maximum marker size in pixels (largest data point)
- ``marker_size_min_px``: Minimum marker size in pixels (smallest data point)

**How it works:**
- Uses Plotly's ``sizeref`` formula to normalize marker sizes relative to current data range
- Automatically adapts when filters change the underlying data
- Ensures consistent visual scaling regardless of data distribution
- No modification of underlying DataFrame values

State ID Anatomy
^^^^^^^^^^^^^^^^

Understanding state ID structure is key:

.. code-block:: text

   State ID: "my_filters-category"
             └────┬────┘  └──┬──┘
             block_id    control_name

   Subscribe: subscribes_to: "my_filters-category"
   Result: Block listens to that control panel's category control

Explicit Parameter Naming with dep_param_name
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

By default, when a chart subscribes to external controls, the parameter name sent to the datasource is auto-parsed from the control name. For example, subscribing to ``"quick_card_1-window_step_selector"`` would send parameter ``window_step_selector`` to the datasource.

To explicitly control the parameter name sent to the datasource, use ``dep_param_name``:

.. code-block:: yaml

   %%dashboard_cell
   datasource: my_datasource
   cards:
     # Control panel with slider
     - type: control_panel
       title: "Select Step"
       controls:
         - name: window_step_selector
           type: slider
           min: 1
           max: 5
           value: 1

     # Chart with explicit dep_param_name
     - type: chart
       plot_type: scatter  # YAML x/y are adapted to plot_params internally
       x: session_length
       y: max_idle
       title: "Session Analysis"
       subscribes_to:
         - state_id: "quick_card_1-window_step_selector"
           dep_param_name: "window_step"  # ← Explicit datasource param name

**What happens:**

1. User changes slider → state ``quick_card_1-window_step_selector`` = 3
2. Chart receives update with ``{"quick_card_1-window_step_selector": 3}``
3. ``dep_param_name`` remaps this to ``{"window_step": 3}`` for datasource
4. Datasource receives ``datasource.get_processed_data({"window_step": 3})``

**Without dep_param_name (legacy):**

.. code-block:: yaml

   subscribes_to:
     - "quick_card_1-window_step_selector"  # Auto-parses to "window_step_selector"

**With dep_param_name (explicit):**

.. code-block:: yaml

   subscribes_to:
     - state_id: "quick_card_1-window_step_selector"
       dep_param_name: "window_step"  # Explicitly "window_step"

**Use Cases:**

- Your datasource expects ``window_step`` but control is named ``window_step_selector``
- Multiple controls map to same datasource parameter
- Legacy datasources with specific parameter names
- Cleaner API when control names don't match datasource parameters

Practical Workflow
^^^^^^^^^^^^^^^^^^

**Step 1: Define control panel with block_id**

.. code-block:: yaml

   - type: control_panel
     block_id: "filters"          # Optional, auto-generated if omitted
     title: "Dashboard Filters"
     controls:
       - name: category
         type: dropdown
         options: ["A", "B", "C"]

**Step 2: Note the state IDs produced**

- ``filters-category`` ← This is what other blocks subscribe to

**Step 3: Charts subscribe**

.. code-block:: yaml

   - type: chart
     plot_type: bar
     plot_params: {x: Product, y: Sales}
     subscribes_to: "filters-category"  # Now this chart listens to control changes

**Result:** User changes dropdown → chart updates automatically

Theme Management
----------------

Set default theme for future dashboards:

.. code-block:: python

   # Set theme
   %dashboard_theme cyborg

   # View current theme and available options
   %dashboard_theme

Plotly Export
-------------

Export Figures to Files
^^^^^^^^^^^^^^^^^^^^^^^

Export Plotly figures from dashboard blocks:

.. code-block:: python

   # Export as HTML with custom title
   %plotly_export chart_block
     format: html
     output: sales_chart.html
     title: "Sales Analysis"

   # Export as PNG image with custom dimensions
   %plotly_export chart_block
     format: png
     output: chart.png
     width: 1000
     height: 800

   # Export as JSON
   %plotly_export chart_block
     format: json
     output: data.json

   # Export with parameters for interactive controls
   %plotly_export histogram
     format: html
     output: distribution.html
     params:
       x_col: "Price"
       group_by: "Category"

**Configuration Keys:**

- ``block``: Name of dashboard block variable (required)
- ``format``: Export format (html, png, json, svg)
- ``output``: Output file path (required)
- ``title``: Figure title (for HTML)
- ``width``: Figure width (for images)
- ``height``: Figure height (for images)
- ``params``: JSON parameters for block.get_figure()

Display in Notebook
^^^^^^^^^^^^^^^^^^^

Display figures inline in Jupyter notebooks:

.. code-block:: python

   # Show figure with custom size and title
   %plotly_show chart_block
     title: "Interactive Chart"
     width: 900
     height: 600

   # Show with parameters for interactive controls
   %plotly_show histogram
     params:
       x_col: "Price"
       group_by: "Category"

Batch Export
^^^^^^^^^^^^

Export multiple figures using cell magic:

.. code-block:: python

   %%plotly_export
   exports:
     - block: sales_chart
       format: html
       output: sales_report.html
       title: "Sales Analysis"
     - block: profit_chart
       format: png
       output: profit_analysis.png
       width: 1200
       height: 800

Examples
--------

Complete Workflow Example with Controls:

.. code-block:: python

   # Load extension
   %load_ext dashboard_lego.ipython_magics

   # Load data and prepare variables
   import pandas as pd
   df = pd.read_csv('data.csv')

   # Prepare environment variables
   metric_options = [
       {"label": "Sales", "value": "sales"},
       {"label": "Profit", "value": "profit"},
       {"label": "Revenue", "value": "revenue"}
   ]

   color_palette = ["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728"]

   # Create dashboard with controls
   %%dashboard_cell
   dataframe: df
   title: "Interactive Sales Dashboard"
   theme: lux
   environment:
     - metric_options
     - color_palette
   cards:
     - type: metric
       metric_spec:
         column: Sales
         agg: sum
         title: "Total Sales"
         color: success
     - type: chart
       plot_type: scatter
       plot_params: {x: Product, y: Sales}
       title: "Sales Analysis"
       controls:
         - name: metric_selector
           type: dropdown
           options: $metric_options
           value: "sales"
           col_props: {xs: 12, md: 6}
         - name: year_slider
           type: slider
           min: 2020
           max: 2024
           step: 1
           value: 2023
           marks: {2020: "2020", 2024: "2024"}
           col_props: {xs: 12, md: 6}

   # Export charts
   %plotly_export sales_chart
     format: html
     output: dashboard_export.html
     title: "Sales Dashboard Export"

   # Display in notebook
   %plotly_show sales_chart
     title: "Interactive Sales Chart"

Common Patterns
---------------

**Quick Analysis with Controls:**

.. code-block:: python

   # Prepare environment
   metric_options = [{"label": "Sales", "value": "sales"}, {"label": "Profit", "value": "profit"}]

   %%dashboard_cell
   dataframe: df
   environment:
     - metric_options
   cards:
     - type: metric
       metric_spec:
         column: col1
         agg: mean
         title: "Average"
     - type: chart
       plot_type: histogram
       plot_params: {x: col1}
       title: "Distribution"
       controls:
         - name: metric_selector
           type: dropdown
           options: $metric_options
           value: "sales"

**Interactive Parameter Exploration:**

.. code-block:: python

   # Hyperparameter playground example
   session_params = {
       'session_length': [10, 15, 20, 25, 30],
       'max_idle': [600, 900, 1800, 3600, 7200],
       'window_step': [3, 5, 7, 10]
   }

   %%dashboard_cell
   dataframe: session_hp_datasource
   title: "Session Hyperparameters Playground"
   environment:
     - session_params
     - metric_options
   cards:
     - type: chart
       plot_type: scatter
       plot_params: {x: session_length, y: max_idle}
       title: "Session Length vs Max Idle"
       controls:
         - name: metric_selector
           type: dropdown
           options: $metric_options
           value: "n_sessions"
         - name: window_step_slider
           type: slider
           min: 3
           max: 10
           step: 1
           value: 5

**Report Generation:**

.. code-block:: python

   %plotly_export analysis_chart
     format: html
     output: report.html
     title: "Analysis Results"

   %plotly_export summary_chart
     format: png
     output: summary.png
     width: 800
     height: 400

**Interactive Exploration:**

.. code-block:: python

   %plotly_show chart
     title: "Interactive View"
   # Now you can interact with the chart in the notebook

Troubleshooting
---------------

**Block not found:** Ensure the block variable exists in the notebook namespace

**Export fails:** Check file permissions and disk space

**Display issues:** Ensure plotly is properly installed and configured for Jupyter

**Theme not applied:** Use ``%dashboard_theme`` to set default theme before creating dashboards

Error Messages
--------------

- ``❌ Error: Block variable 'X' not found`` - Variable doesn't exist in namespace
- ``❌ Error: Block 'X' does not support figure export`` - Block doesn't have ``get_figure()`` method
- ``❌ Error: --output/-o is required`` - Output file path not specified
- ``❌ Error: Environment variable 'X' not found`` - Variable not declared in environment list
- ``❌ Error: Invalid YAML format`` - YAML syntax error in cell configuration
- ``❌ Error: Control 'X': unknown type 'Y'`` - Unsupported control type (use dropdown, slider, input)
- ``❌ Error: Variable '$X' not found in environment`` - Referenced variable not in environment list
