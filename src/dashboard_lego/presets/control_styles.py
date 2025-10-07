"""
Preset styles and layouts for control panels.

:hierarchy: [Presets | Control Styles]
:relates-to:
 - motivated_by: "PRD: Reusable style presets to avoid CSS sprawl"
 - implements: "module: 'control_styles'"

"""

from typing import Any, Dict


def modern_slider_style() -> str:
    """
    Returns CSS for modern slider styling.

    :hierarchy: [Presets | Control Styles | Modern Slider]
    :relates-to:
     - motivated_by: "PRD: Consistent, modern styling for sliders"
     - implements: "function: 'modern_slider_style'"
     - uses: ["CSS: 'rc-slider' classes"]

    :rationale: "Provides consistent, modern styling for sliders with proper colors and sizing."
    :contract:
     - pre: "None."
     - post: "Returns CSS string for modern slider styling."

    Returns:
        CSS string for slider styling
    """
    return """
        .modern-slider {
            width: 100% !important;
            min-width: 200px !important;
            margin: 10px 0 !important;
        }
        .modern-slider .rc-slider-track {
            background-color: #007bff !important;
            height: 6px !important;
        }
        .modern-slider .rc-slider-rail {
            background-color: #e9ecef !important;
            height: 6px !important;
        }
        .modern-slider .rc-slider-handle {
            border: 2px solid #007bff !important;
            background-color: #fff !important;
            width: 20px !important;
            height: 20px !important;
            margin-top: -7px !important;
        }
        .modern-slider .rc-slider-handle:hover {
            border-color: #0056b3 !important;
        }
        .modern-slider .rc-slider-mark {
            font-size: 12px !important;
        }
    """


def control_panel_col_props(
    dropdown_cols: int = 4, slider_cols: int = 8
) -> Dict[str, Dict[str, Any]]:
    """
    Returns responsive column props for typical control panel layout.

    :hierarchy: [Presets | Control Styles | Column Props]
    :relates-to:
     - motivated_by: "PRD: Standard responsive layouts for control panels"
     - implements: "function: 'control_panel_col_props'"
     - uses: ["Bootstrap: 'responsive grid system'"]

    :rationale: "Provides standard responsive column sizing for common control panel layouts."
    :contract:
     - pre: "dropdown_cols and slider_cols are integers between 1 and 12."
     - post: "Returns dict with responsive column properties for dropdown and slider."

    Args:
        dropdown_cols: Number of columns for dropdown (1-12)
        slider_cols: Number of columns for slider (1-12)

    Returns:
        Dict with 'dropdown' and 'slider' col_props
    """
    return {
        "dropdown": {"xs": 12, "md": dropdown_cols},
        "slider": {"xs": 12, "md": slider_cols},
    }


def get_control_panel_css() -> str:
    """
    Returns complete CSS for control panels with modern styling.

    :hierarchy: [Presets | Control Styles | Complete CSS]
    :relates-to:
     - motivated_by: "PRD: Single function to get all control panel styles"
     - implements: "function: 'get_control_panel_css'"
     - uses: ["function: 'modern_slider_style'"]

    :rationale: "Provides a single entry point for all control panel styling."
    :contract:
     - pre: "None."
     - post: "Returns complete CSS string for control panels."

    Returns:
        Complete CSS string for control panels with modern styling
    """
    return modern_slider_style()


def compact_dropdown_style() -> str:
    """
    Returns CSS for compact dropdown styling.

    :hierarchy: [Presets | Control Styles | Compact Dropdown]
    :relates-to:
     - motivated_by: "PRD: Compact styling for dropdowns in control panels"
     - implements: "function: 'compact_dropdown_style'"
     - uses: ["CSS: 'Select' classes"]

    :rationale: "Provides compact styling for dropdowns to save space in control panels."
    :contract:
     - pre: "None."
     - post: "Returns CSS string for compact dropdown styling."

    Returns:
        CSS string for compact dropdown styling
    """
    return """
        .compact-dropdown .Select-control {
            min-height: 32px !important;
            border-radius: 4px !important;
        }
        .compact-dropdown .Select-placeholder {
            line-height: 30px !important;
        }
        .compact-dropdown .Select-value {
            line-height: 30px !important;
        }
    """
