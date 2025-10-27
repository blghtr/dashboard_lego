"""
Control building helpers for Dashboard Lego.

Provides shared utilities for creating and normalizing controls
across different contexts (magics, quick dashboard, etc.).

:hierarchy: [Blocks | ControlHelpers]
:relates-to:
 - motivated_by: "Need consistent control building across magics and quick factory:
                  options normalization, col_props defaults, component mapping"
 - implements: "Shared control building utilities"
 - uses: ["Control dataclass", "dash components"]

:contract:
 - pre: "control_specs is list of control specification dicts"
 - post: "returns dict of {control_name: Control} with normalized options"
 - invariant: "deterministic normalization, consistent defaults"

:complexity: 3
:decision_cache: "Extracted from magics to avoid duplication between
                  ipython_magics and quick_dashboard control building"
"""

from typing import Any, Dict, List, Optional

from dashboard_lego.blocks.typed_chart import Control
from dashboard_lego.utils.logger import get_logger

logger = get_logger(__name__)


def build_controls_from_spec(
    controls_spec: Optional[List[Dict[str, Any]]]
) -> Dict[str, Control]:
    """
    Build Control objects from specification with normalization.

    Supports: dropdown, slider, input
    Normalizes: options (list[str] → list[dict]), col_props defaults

    Args:
        controls_spec: List of control specifications

    Returns:
        {control_name: Control} dict

    Raises:
        ValueError: If required fields missing or unknown control type

    Example:
        >>> spec = [
        ...     {"name": "metric", "type": "dropdown", "options": ["A", "B"]},
        ...     {"name": "year", "type": "slider", "min": 2020, "max": 2024}
        ... ]
        >>> controls = build_controls_from_spec(spec)
        >>> controls["metric"].props["options"]
        [{"label": "A", "value": "A"}, {"label": "B", "value": "B"}]
    """
    from dash import dcc

    if not controls_spec:
        return {}

    controls = {}

    for i, control_spec in enumerate(controls_spec):
        try:
            name = control_spec.get("name")
            if not name:
                raise ValueError(f"Control {i}: 'name' is required")

            control_type = control_spec.get("type")
            if not control_type:
                raise ValueError(f"Control '{name}': 'type' is required")

            # Set responsive defaults based on control type
            if control_spec.get("col_props") is not None:
                col_props = control_spec.get("col_props")
            else:
                if control_type == "slider":
                    col_props = {"xs": 12, "md": 12}  # Full width for sliders
                elif control_type == "dropdown":
                    col_props = {"xs": 12, "md": 4}  # Narrower for dropdowns
                else:
                    col_props = {"xs": 12, "md": "auto"}  # Default for other controls

            if control_type == "dropdown":
                options = control_spec.get("options", [])
                # Normalize: list[str] → list[dict]
                if (
                    options
                    and isinstance(options, list)
                    and isinstance(options[0], str)
                ):
                    options = [{"label": opt, "value": opt} for opt in options]

                # Build props with CSS class
                props = {
                    "options": options,
                    "value": control_spec.get("value"),
                    "placeholder": control_spec.get("placeholder", "Select..."),
                    "clearable": control_spec.get("clearable", True),
                }
                # Add CSS class (default or explicit)
                if "className" in control_spec:
                    props["className"] = control_spec["className"]
                else:
                    props["className"] = "compact-dropdown"

                controls[name] = Control(
                    component=dcc.Dropdown,
                    props=props,
                    col_props=col_props,
                    dep_param_name=control_spec.get("dep_param_name"),
                )
                logger.debug(f"[ControlHelpers] Created dropdown: {name}")

            elif control_type == "slider":
                # Build props with CSS class
                props = {
                    "min": control_spec.get("min", 0),
                    "max": control_spec.get("max", 100),
                    "step": control_spec.get("step", 1),
                    "value": control_spec.get("value", 50),
                    "marks": control_spec.get("marks", {}),
                    "tooltip": control_spec.get("tooltip", {}),
                }
                # Add CSS class (default or explicit)
                if "className" in control_spec:
                    props["className"] = control_spec["className"]
                else:
                    props["className"] = "modern-slider"

                controls[name] = Control(
                    component=dcc.Slider,
                    props=props,
                    col_props=col_props,
                    dep_param_name=control_spec.get("dep_param_name"),
                )
                logger.debug(f"[ControlHelpers] Created slider: {name}")

            elif control_type == "input":
                controls[name] = Control(
                    component=dcc.Input,
                    props={
                        "type": control_spec.get("input_type", "text"),
                        "placeholder": control_spec.get("placeholder", "Enter value"),
                        "value": control_spec.get("value", ""),
                        "debounce": control_spec.get("debounce", True),
                    },
                    col_props=col_props,
                    dep_param_name=control_spec.get("dep_param_name"),
                )
                logger.debug(f"[ControlHelpers] Created input: {name}")

            else:
                raise ValueError(f"Control '{name}': unknown type '{control_type}'")

        except (KeyError, ValueError) as e:
            logger.error(f"[ControlHelpers] Error creating control {i}: {e}")
            raise ValueError(f"Invalid control specification: {e}")

    logger.debug(f"[ControlHelpers] Built {len(controls)} controls")
    return controls
