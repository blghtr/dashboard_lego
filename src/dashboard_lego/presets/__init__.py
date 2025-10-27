"""
Preset modules for dashboard_lego.

:hierarchy: [Presets]
:relates-to:
 - motivated_by: "PRD: Reusable presets to avoid code duplication"
 - implements: "package: 'presets'"

"""

from .base_preset import BasePreset
from .css.control_styles import (
    compact_dropdown_style,
    control_panel_col_props,
    get_control_panel_css,
    modern_slider_style,
)
from .eda_presets import (
    BoxPlotPreset,
    CorrelationHeatmapPreset,
    GroupedHistogramPreset,
    KneePlotPreset,
    MissingValuesPreset,
)
from .ml_presets import (
    ConfusionMatrixPreset,
    FeatureImportancePreset,
    RocAucCurvePreset,
)

__all__ = [
    "BasePreset",
    "CorrelationHeatmapPreset",
    "GroupedHistogramPreset",
    "KneePlotPreset",
    "MissingValuesPreset",
    "BoxPlotPreset",
    "ConfusionMatrixPreset",
    "FeatureImportancePreset",
    "RocAucCurvePreset",
    # CSS styling utilities
    "compact_dropdown_style",
    "modern_slider_style",
    "control_panel_col_props",
    "get_control_panel_css",
]
