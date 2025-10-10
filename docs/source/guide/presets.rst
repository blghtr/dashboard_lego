.. _guide-presets:

Presets Module API
==================

Pre-built blocks and layouts for common visualization patterns.

.. contents::
   :local:

EDA Presets
-----------

**Location:** ``dashboard_lego.presets.eda_presets``

Pre-built blocks for exploratory data analysis.

**Available Presets:**

- ``CorrelationHeatmapPreset``: Correlation matrix heatmap
- ``GroupedHistogramPreset``: Interactive histogram with grouping
- ``MissingValuesPreset``: Missing values visualization
- ``BoxPlotPreset``: Distribution comparison box plots

ML Presets
----------

**Location:** ``dashboard_lego.presets.ml_presets``

Pre-built blocks for machine learning visualization.

**Available Presets:**

- ``FeatureImportancePreset``: Feature importance bar chart
- ``ConfusionMatrixPreset``: Confusion matrix heatmap
- ``ROC_CurvePreset``: ROC curve for binary classification
- ``MetricCardBlock``: Compact ML metrics display

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
