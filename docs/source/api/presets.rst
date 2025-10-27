Presets Module
===============

The presets module contains pre-built blocks for common data analysis and visualization tasks.

Base Preset
-----------

Abstract base class for all TypedChartBlock presets with standardized control configuration.

.. automodule:: dashboard_lego.presets.base_preset
   :members:
   :undoc-members:
   :show-inheritance:

Base Preset Class
^^^^^^^^^^^^^^^^^

.. autoclass:: dashboard_lego.presets.base_preset.BasePreset
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

EDA Presets
-----------

Exploratory Data Analysis presets for common data visualization patterns.

.. automodule:: dashboard_lego.presets.eda_presets
   :members:
   :undoc-members:
   :show-inheritance:

Correlation Heatmap Preset
^^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: dashboard_lego.presets.eda_presets.CorrelationHeatmapPreset
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Grouped Histogram Preset
^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: dashboard_lego.presets.eda_presets.GroupedHistogramPreset
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Missing Values Preset
^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: dashboard_lego.presets.eda_presets.MissingValuesPreset
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Box Plot Preset
^^^^^^^^^^^^^^^

.. autoclass:: dashboard_lego.presets.eda_presets.BoxPlotPreset
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Knee Plot Preset
^^^^^^^^^^^^^^^^

.. autoclass:: dashboard_lego.presets.eda_presets.KneePlotPreset
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

ML Presets
----------

Machine Learning visualization presets for common ML workflows.

.. automodule:: dashboard_lego.presets.ml_presets
   :members:
   :undoc-members:
   :show-inheritance:

Confusion Matrix Preset
^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: dashboard_lego.presets.ml_presets.ConfusionMatrixPreset
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Feature Importance Preset
^^^^^^^^^^^^^^^^^^^^^^^^^

.. autoclass:: dashboard_lego.presets.ml_presets.FeatureImportancePreset
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

ROC AUC Curve Preset
^^^^^^^^^^^^^^^^^^^^

.. autoclass:: dashboard_lego.presets.ml_presets.RocAucCurvePreset
   :members:
   :undoc-members:
   :show-inheritance:
   :noindex:

Layout Presets
--------------

Pre-built layout patterns for common dashboard arrangements.

.. automodule:: dashboard_lego.presets.layouts
   :members:
   :undoc-members:
   :show-inheritance:

Layout Functions
^^^^^^^^^^^^^^^^

.. autofunction:: dashboard_lego.presets.layouts.one_column
   :noindex:

.. autofunction:: dashboard_lego.presets.layouts.two_column_6_6
   :noindex:

.. autofunction:: dashboard_lego.presets.layouts.two_column_8_4
   :noindex:

.. autofunction:: dashboard_lego.presets.layouts.three_column_4_4_4
   :noindex:

.. autofunction:: dashboard_lego.presets.layouts.kpi_row_top
   :noindex:
