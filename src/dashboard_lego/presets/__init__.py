"""
Preset modules for dashboard_lego.

:hierarchy: [Presets]
:relates-to:
 - motivated_by: "PRD: Reusable presets to avoid code duplication"
 - implements: "package: 'presets'"

"""

from .control_styles import (
    compact_dropdown_style,
    control_panel_col_props,
    get_control_panel_css,
    modern_slider_style,
)

__all__ = [
    "modern_slider_style",
    "control_panel_col_props",
    "get_control_panel_css",
    "compact_dropdown_style",
]
