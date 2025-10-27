.. _guide-presets:

Presets Module API
==================

Pre-built blocks and layouts for common visualization patterns.

All presets inherit from ``BasePreset``, which provides flexible control configuration:
- ``controls=False`` (default): No controls, expects values in kwargs
- ``controls=True``: Create default controls for all parameters
- ``controls=dict``: Custom control configuration (enable/disable or override specific controls)

.. contents::
   :local:

Base Preset
-----------

**Location:** ``dashboard_lego.presets.base_preset``

Abstract base class for all TypedChartBlock presets with standardized control configuration.

**Key Features:**
- Flexible control configuration via ``controls`` parameter
- Automatic plot parameter building based on available controls
- Dynamic plot title generation
- Datasource validation
- Consistent preset development pattern

**Usage:**
```python
from dashboard_lego.presets import KneePlotPreset

# No controls - use values from kwargs
preset = KneePlotPreset(
    block_id="knee-plot",
    datasource=datasource,
    x_col="k",
    y_col="inertia"
)

# All default controls
preset = KneePlotPreset(
    block_id="knee-plot",
    datasource=datasource,
    controls=True
)

# Custom control configuration
preset = KneePlotPreset(
    block_id="knee-plot",
    datasource=datasource,
    controls={
        "x_col": True,  # Enable default control
        "y_col": False, # Disable control
        "auto_knee": CustomControl(...)  # Override with custom control
    }
)
```

Auto-sizing Controls
-------------------

**Default Behavior:** All controls now auto-size to content by default.

Controls automatically:
- Size to fit content width instead of stretching full width
- Use Bootstrap `col-auto` for responsive layout
- Cap maximum width at 40 characters for readability
- Compute minimum width based on longest option text (for dropdowns)

**How it works:**
```python
# Default auto-sizing (enabled by default)
Control(
    component=dcc.Dropdown,
    props={"options": ["Short", "Very Long Option Name"]},
    # auto_size=True (default)
    # max_ch=40 (default)
    # col_props={"xs": 12, "md": "auto"} (default)
)

# Disable auto-sizing for specific control
Control(
    component=dcc.Dropdown,
    props={"options": [...]},
    auto_size=False,  # Disable auto-sizing
    col_props={"xs": 12, "md": 6}  # Use fixed width
)

# Custom character limit
Control(
    component=dcc.Dropdown,
    props={"options": [...]},
    max_ch=60  # Allow wider controls
)
```

**Benefits:**
- Cleaner, more compact layouts
- Better use of available space
- Consistent sizing across different content lengths
- Responsive behavior on different screen sizes

EDA Presets
-----------

**Location:** ``dashboard_lego.presets.eda_presets``

Pre-built blocks for exploratory data analysis.

**Available Presets:**

- ``CorrelationHeatmapPreset``: Correlation matrix heatmap
- ``GroupedHistogramPreset``: Interactive histogram with grouping
- ``MissingValuesPreset``: Missing values visualization
- ``BoxPlotPreset``: Distribution comparison box plots
- ``KneePlotPreset``: Knee/elbow plot for optimization analysis and cluster validation

ML Presets
----------

**Location:** ``dashboard_lego.presets.ml_presets``

Pre-built blocks for machine learning visualization.

**Available Presets:**

- ``FeatureImportancePreset``: Feature importance bar chart
- ``ConfusionMatrixPreset``: Confusion matrix heatmap
- ``RocAucCurvePreset``: ROC curve for binary and multi-class classification

Layout Presets
--------------

**Location:** ``dashboard_lego.presets.layouts``

Pre-built layout functions for common patterns.

**Available Layouts:**

- ``one_column()``: Stack blocks vertically
- ``two_column_6_6()``: Equal two-column split (50/50)
- ``two_column_8_4()``: Main content with sidebar (67/33)
- ``three_column_4_4_4()``: Three equal columns (33/33/33)
- ``sidebar_main_3_9()``: Narrow sidebar with content (25/75)
- ``kpi_row_top()``: KPIs in top row, content below

**Example:**

.. code-block:: python

   from dashboard_lego.presets.layouts import kpi_row_top, two_column_8_4

   layout = kpi_row_top(
       kpi_blocks=[kpi1, kpi2, kpi3],
       content_rows=[
           two_column_8_4(main=chart, side=filter_panel),
           [table_block]
       ]
   )

Control Styles
--------------

**Location:** ``dashboard_lego.presets.control_styles``

Modern UI styling functions for controls.

**Available Functions:**

- ``modern_slider_style()``: Modern slider styling
- ``compact_dropdown_style()``: Compact dropdown styling
- ``control_panel_col_props()``: Responsive column properties
- ``get_control_panel_css()``: Custom CSS for control panels

For detailed documentation, see :ref:`api-presets`.
