"""
TypedChartBlock - High-level chart block with built-in plot types.

NO chart_generator needed - just specify plot_type!

:hierarchy: [Blocks | Charts | TypedChartBlock]
:relates-to:
 - motivated_by: "v0.15.0: High-level API requiring minimal user code"
 - implements: "block: 'TypedChartBlock' with plot registry"
 - uses: ["module: 'plot_registry'", "class: 'BaseBlock'"]

:contract:
 - pre: "plot_type exists in PLOT_REGISTRY"
 - post: "Chart renders using registered plot function"
 - invariant: "plot_kwargs passed through to plot function"
 - guarantee: "Plot function receives pre-filtered DataFrame"

:complexity: 6
:decision_cache: "Registry pattern for extensibility without subclassing"
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.graph_objects as go
from dash import dcc, html
from dash.development.base_component import Component

from dashboard_lego.blocks.base import BaseBlock
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.utils.plot_registry import get_plot_function


@dataclass
class Control:
    """
    UI control definition for TypedChartBlock.

    :hierarchy: [Blocks | Controls | Control]
    :relates-to:
     - motivated_by: "Need responsive control layouts with content-based sizing"
     - implements: "dataclass: 'Control'"

    :contract:
     - pre: "component is valid Dash component type"
     - post: "Control can be rendered with responsive layout and optional auto-sizing"

    Attributes:
        component: Dash component class (dcc.Dropdown, dcc.Slider, etc.)
        props: Props dictionary for the component
        col_props: Bootstrap column sizing (default: {"xs": 12, "md": "auto"})
        dep_param_name: Optional parameter name override for datasource (default: None)
        auto_size: Enable content-based sizing instead of full width (default: True)
        max_ch: Maximum width in characters for auto-sized controls (default: 40)
    """

    component: Type[Component]
    props: Dict[str, Any] = field(default_factory=dict)
    col_props: Optional[Dict[str, Any]] = field(
        default_factory=lambda: {"xs": 12, "md": "auto"}
    )
    dep_param_name: Optional[str] = None
    auto_size: bool = True
    max_ch: Optional[int] = 40


class TypedChartBlock(BaseBlock):
    """
    High-level chart block using plot type registry.

    NO chart_generator needed - specify plot_type and plot_params!

    :hierarchy: [Blocks | Charts | TypedChartBlock]
    :relates-to:
     - motivated_by: "Eliminate chart_generator requirement for common plots"
     - implements: "block: 'TypedChartBlock'"
     - uses: ["module: 'plot_registry'", "class: 'BaseBlock'"]

    :rationale: "Registry pattern allows zero-code chart creation for 90% of cases"
    :contract:
     - pre: "plot_type exists in PLOT_REGISTRY"
     - post: "Chart renders via registered function with kwargs passed through"
     - invariant: "Block never stores data, always calls get_processed_data()"
     - kwargs_flow: "plot_kwargs → plot_function(**plot_kwargs)"

    :complexity: 6
    :decision_cache: "Single block type for all chart types via registry"

    Example:
        >>> chart = TypedChartBlock(
        ...     block_id="sales_hist",
        ...     datasource=datasource,
        ...     plot_type='histogram',
        ...     plot_params={'x': 'price'},
        ...     plot_kwargs={'bins': 30, 'title': 'Price Distribution'},
        ...     subscribes_to='control-category'
        ... )
    """

    def __init__(
        self,
        block_id: str,
        datasource: DataSource,
        plot_type: str,
        plot_params: Dict[str, Any],
        plot_kwargs: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
        plot_title: Optional[str] = None,
        controls: Optional[Dict[str, Control]] = None,
        subscribes_to: Union[str, List[str], Dict[str, Any], None] = None,
        transform_fn: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,
        # Styling
        card_style: Optional[Dict[str, Any]] = None,
        card_className: Optional[str] = None,
        title_style: Optional[Dict[str, Any]] = None,
        title_className: Optional[str] = None,
        loading_type: str = "default",
        graph_config: Optional[Dict[str, Any]] = None,
        graph_style: Optional[Dict[str, Any]] = None,
        **kwargs,
    ):
        """
        Initialize TypedChartBlock.

        :hierarchy: [Blocks | Charts | TypedChartBlock | Initialization]
        :relates-to:
         - motivated_by: "High-level API requiring minimal code"
         - motivated_by: "v0.15.0: Block-specific data transformations"
         - implements: "method: '__init__'"

        :contract:
         - pre: "plot_type valid, plot_params contains required keys"
         - post: "Block ready to render"
         - kwargs_flow: "plot_kwargs stored and passed to plot function"
         - transform_flow: "transform_fn → specialized datasource via BaseBlock"

        :complexity: 5

        Args:
            block_id: Unique identifier for this block
            datasource: DataSource instance
            plot_type: Type from PLOT_REGISTRY
                      Examples: 'histogram', 'scatter', 'overlay_histogram'
            plot_params: Plot-specific parameters (column names, bins, etc.)
                        Example: {'x': 'age', 'y': 'salary', 'color': 'dept'}
            plot_kwargs: Additional kwargs PASSED TO plot function
                        Example: {'title': 'My Chart', 'opacity': 0.7}
                        KEY POINT: These go directly to plotly!
            title: Block title (shown in card header)
            controls: Optional embedded controls
            subscribes_to: External state IDs to subscribe to
            transform_fn: Optional block-specific data transformation
                         Applied AFTER global filters
                         Signature: lambda df: df (returns transformed DataFrame)
                         Examples:
                         - lambda df: df.groupby('category')['sales'].sum().reset_index()
                         - lambda df: df.pivot_table(index='region', columns='product', values='revenue')
                         - lambda df: df[df['price'] > 100]
            card_style, card_className: Card styling
            loading_type: Loading animation type
            graph_config: Plotly graph configuration
        """
        self._plot_type = plot_type
        self.plot_params = plot_params
        self.plot_kwargs = plot_kwargs or {}  # KEY: Store for passthrough
        self.plot_func = get_plot_function(self._plot_type)
        self.controls = controls or {}
        self.title = title or self._plot_type.replace("_", " ").title()
        self.plot_title = plot_title  # Dynamic plot title with placeholders

        # Store styling
        self.card_style = card_style
        self.card_className = card_className
        self.title_style = title_style
        self.title_className = title_className
        self.loading_type = loading_type
        self.graph_config = graph_config or {}
        self.graph_style = graph_style

        # Build subscribes dict
        # CRITICAL: Do NOT subscribe to own controls here - they're handled by
        # block-centric callbacks via list_control_inputs()
        # Only subscribe to external states (e.g. global filters)
        external_states = self._normalize_subscribes_to(subscribes_to)

        subscribes_dict = {state: self._update_chart for state in external_states}

        # Store dep_param_name mapping for datasource parameter resolution
        # Format: {state_id: dep_param_name}
        self._dep_param_names: Dict[str, str] = {}
        if isinstance(subscribes_to, list):
            for item in subscribes_to:
                if isinstance(item, dict) and "state_id" in item:
                    state_id = item["state_id"]
                    if "dep_param_name" in item:
                        self._dep_param_names[state_id] = item["dep_param_name"]

        # Extract from embedded controls
        if self.controls:
            for control_name, control_obj in self.controls.items():
                if (
                    hasattr(control_obj, "dep_param_name")
                    and control_obj.dep_param_name
                ):
                    # For embedded controls, key is just control_name (after normalization)
                    self._dep_param_names[control_name] = control_obj.dep_param_name
                    self.logger.debug(
                        f"[TypedChartBlock|Init] Embedded control dep_param_name: "
                        f"{control_name} → {control_obj.dep_param_name}"
                    )

        # Build publishes for own controls
        publishes_list = [
            {"state_id": f"{block_id}-{ctrl}", "component_prop": "value"}
            for ctrl in self.controls.keys()
        ]

        # Pass to parent - BaseBlock handles registration and transform_fn!
        super().__init__(
            block_id,
            datasource,
            subscribes=subscribes_dict,
            publishes=publishes_list,
            transform_fn=transform_fn,  # Pass to BaseBlock for specialized datasource creation
            **kwargs,
        )

        self.logger.info(
            f"[TypedChartBlock|Init] {block_id} | plot_type={self._plot_type} | "
            f"controls={len(self.controls)}"
        )

    def _get_component_prop(self) -> str:
        """Override to use 'figure' property for Graph components."""
        return "figure"

    def output_target(self) -> tuple[str, str]:
        """
        Returns output target for chart blocks.

        :hierarchy: [Blocks | Charts | TypedChartBlock | OutputTarget]
        :contract:
         - pre: "Block initialized"
         - post: "Returns (component_id, 'figure')"
        """
        component_id = self._generate_id("container")
        return (component_id, "figure")

    def update_from_controls(self, control_values: Dict[str, Any]) -> go.Figure:
        """
        Update chart from block-centric callback.

        CRITICAL: TypedChartBlock with embedded controls has subscribes={} (empty),
        so BaseBlock.update_from_controls() returns None. We MUST override this
        to call _update_chart directly with control_values dict.

        :hierarchy: [Blocks | TypedChartBlock | Update]
        :relates-to:
         - motivated_by: "BaseBlock.update_from_controls returns None if subscribes empty"
         - implements: "method: 'update_from_controls' override"

        :contract:
         - pre: "control_values is {ctrl_name: value} dict from StateManager"
         - post: "Returns updated Plotly Figure"
         - spec_compliance: "Calls _update_chart with control_values as first arg"

        :complexity: 2

        Args:
            control_values: Dict mapping control names to values (e.g. {'x_col': 'Price'})

        Returns:
            Updated Plotly Figure
        """
        # Pass control_values dict as first positional arg to _update_chart
        self.logger.debug(
            f"[TypedChartBlock|UpdateFromControls] Calling _update_chart with control_values={control_values}"
        )
        return self._update_chart(control_values)

    def get_figure(self, params: Optional[Dict[str, Any]] = None) -> go.Figure:
        """
        Export standalone Plotly figure without Dash server.

        This is the official API for getting a Plotly figure object that can be
        saved, displayed, or further customized without running a dashboard.

        Args:
            params: Optional parameters for datasource filtering.
                    For blocks with controls, provide control values as dict.
                    Example: {'x_col': 'Price', 'y_col': 'Sales'}

        Returns:
            Plotly Figure object ready for export via:
            - figure.write_html('chart.html')
            - figure.write_image('chart.png')  # requires kaleido
            - figure.to_json()
            - figure.show()

        Example:
            >>> chart = TypedChartBlock(
            ...     block_id="sales",
            ...     datasource=datasource,
            ...     plot_type="bar",
            ...     plot_params={"x": "Product", "y": "Sales"}
            ... )
            >>> fig = chart.get_figure()
            >>> fig.write_html("sales_chart.html")
        """
        control_values = params or {}
        return self._update_chart(control_values)

    def list_control_inputs(self) -> list[tuple[str, str]]:
        """
        Returns list of control inputs for block-centric callbacks.

        CRITICAL: Must return the SAME IDs used in publishes registration.
        Uses string IDs (f"{block_id}-{ctrl}"), not pattern-matching dicts.

        :hierarchy: [Blocks | Charts | TypedChartBlock | ControlInputs]
        :contract:
         - pre: "Block initialized with controls"
         - post: "Returns list of (component_id, 'value') tuples matching publishes"

        Returns:
            List of control input specifications for Dash callbacks
        """
        if not self.controls:
            return []

        # CRITICAL: Use string IDs to match publishes registration
        # BaseBlock._register_state_interactions will convert to pattern-matching
        return [
            (f"{self.block_id}-{ctrl_name}", "value")
            for ctrl_name in self.controls.keys()
        ]

    def _extract_control_values(
        self, args: tuple = (), kwargs: dict = None
    ) -> Dict[str, Any]:
        """
        Extract control values from callback args or kwargs.

        CRITICAL: BaseBlock.update_from_controls() passes **kwargs with dict IDs as keys.
        TypedChartBlock must extract control values from these dict IDs.

        :hierarchy: [Blocks | Charts | TypedChartBlock | ControlExtraction]
        :relates-to:
         - motivated_by: "BaseBlock.update_from_controls contract: passes **{dict_id: value}"
         - implements: "method: '_extract_control_values' with kwargs support"

        :contract:
         - pre: "kwargs contains {dict_id: value} OR args are positional values"
         - post: "Returns {control_name: value} dict"
         - invariant: "Handles both *args (state-centric) and **kwargs (block-centric) patterns"
         - spec_compliance: "Satisfies BaseBlock.update_from_controls contract"

        :complexity: 3

        Args:
            args: Positional args from state-centric callbacks
            kwargs: Keyword args from block-centric callbacks (dict IDs as keys)

        Returns:
            Dictionary mapping control names to values

        Example:
            >>> # Block-centric: kwargs = {{'section': 1, 'type': 'distribution-x_col'}: 'Price'}
            >>> control_values = _extract_control_values((), kwargs)
            >>> # Result: {'x_col': 'Price'}
        """
        control_values = {}

        # CASE 1: Block-centric callback passes **kwargs with dict IDs
        if kwargs:
            for key, value in kwargs.items():
                # Extract control name from dict ID or string ID
                if isinstance(key, dict) and "type" in key:
                    # Pattern-matching ID: {'section': 1, 'type': 'distribution-x_col'}
                    id_str = key["type"]
                elif isinstance(key, str):
                    # String ID: 'distribution-x_col'
                    id_str = key
                else:
                    self.logger.warning(
                        f"[TypedChartBlock|Extract] Unknown key type: {type(key)}"
                    )
                    continue

                # Extract control name: "distribution-x_col" → "x_col"
                control_name = id_str.split("-")[-1]
                control_values[control_name] = value
                self.logger.debug(
                    f"[TypedChartBlock|Extract] {control_name}={value} (from kwargs[{id_str}])"
                )

        # CASE 2: State-centric callback passes *args (positional)
        elif args and hasattr(self, "subscribes") and self.subscribes:
            state_ids = list(self.subscribes.keys())
            # For external subscriptions, args should contain values in the same order as state_ids
            if len(args) >= len(state_ids):
                for i, state_id in enumerate(state_ids):
                    if i < len(args):
                        value = args[i]
                        # Extract control name from state_id: "metric_controls-metric_selector" -> "metric_selector"
                        control_name = state_id.split("-")[-1]
                        control_values[control_name] = value
                        self.logger.debug(
                            f"[TypedChartBlock|Extract] {control_name}={value} (from {state_id})"
                        )
            else:
                self.logger.warning(
                    f"[TypedChartBlock|Extract] Not enough args ({len(args)}) for states ({len(state_ids)})"
                )

        # CASE 3: Initial render (no args/kwargs), use initial values from controls
        if not control_values and self.controls:
            for ctrl_name, ctrl in self.controls.items():
                if "value" in ctrl.props:
                    control_values[ctrl_name] = ctrl.props["value"]
                    self.logger.debug(
                        f"[TypedChartBlock|Extract] {ctrl_name}={ctrl.props['value']} (initial)"
                    )

        return control_values

    def _resolve_string_placeholders(
        self, value: Any, control_values: Dict[str, Any]
    ) -> Any:
        """
        Resolve {{placeholders}} in string values.

        Supports two modes:
        - Standalone: "{{name}}" → returns control value (any type)
        - Inline: "Text {{name}}" → string with substitutions

        Args:
            value: Value to resolve (any type)
            control_values: {control_name: control_value} (may contain normalized keys)

        Returns:
            Resolved value (type depends on mode)
        """
        if not isinstance(value, str):
            return value

        # Helper function to find control value by name (with suffix matching and reverse mapping)
        def find_control_value(control_name: str):
            """Find control value by exact match, suffix match, or reverse dep_param_name mapping"""
            # Try exact match first
            if control_name in control_values:
                return True, control_values[control_name]

            # Try suffix match: any key ending with "-control_name"
            suffix = f"-{control_name}"
            matching_keys = [k for k in control_values.keys() if k.endswith(suffix)]
            if matching_keys:
                return True, control_values[matching_keys[0]]

            # Try reverse mapping: find normalized key that maps back to this control name
            # Check if any control has dep_param_name that matches a key in control_values
            for ctrl_name, ctrl_obj in (self.controls or {}).items():
                if hasattr(ctrl_obj, "dep_param_name") and ctrl_obj.dep_param_name:
                    if (
                        ctrl_obj.dep_param_name in control_values
                        and ctrl_name == control_name
                    ):
                        return True, control_values[ctrl_obj.dep_param_name]

            # Try embedded controls as fallback
            if (
                control_name in self.controls
                and "value" in self.controls[control_name].props
            ):
                return True, self.controls[control_name].props["value"]

            return False, None

        # Check if entire string is a standalone placeholder
        if value.startswith("{{") and value.endswith("}}"):
            control_name = value[2:-2].strip()
            found, result = find_control_value(control_name)

            if found:
                return result
            else:
                self.logger.warning(
                    f"[TypedChartBlock|Resolve] Standalone placeholder '{control_name}' unresolved → None"
                )
                return None

        # Handle inline placeholders using regex
        import re

        placeholder_pattern = r"\{\{([a-zA-Z_][a-zA-Z0-9_]*)\}\}"

        def replace_placeholder(match):
            control_name = match.group(1)
            found, result = find_control_value(control_name)

            if found:
                return str(result)
            else:
                self.logger.warning(
                    f"[TypedChartBlock|Resolve] Inline placeholder '{control_name}' unresolved → empty"
                )
                return ""

        return re.sub(placeholder_pattern, replace_placeholder, value)

    def _extract_datasource_params(
        self, control_values: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Extract datasource parameters from control values.

        Routes values to datasource based on:
        1. External subscribed states → datasource params (UNLESS used only in plot_params placeholders)
        2. NOT embedded controls → pass through if not recognized

        :hierarchy: [Blocks | Charts | TypedChartBlock | ParamExtraction]
        :relates-to:
         - motivated_by: "Clear routing of control values to datasource"
         - implements: "method: '_extract_datasource_params'"

        :contract:
         - pre: "control_values has normalized keys"
         - post: "Returns {param_name: value} for datasource.get_processed_data()"

        Args:
            control_values: Normalized {state_id/control_name: value}

        Returns:
            Dict of parameters for datasource
        """

        # Helper: Check if a control is used ONLY in plot_params placeholders (not for datasource)
        def is_plot_params_only(control_key: str) -> bool:
            """Returns True if control is referenced in plot_params but should not go to datasource"""
            # Extract short name from state_id (e.g., "quick_card_0-metric_selector_1" → "metric_selector_1")
            short_name = (
                control_key.split("-")[-1] if "-" in control_key else control_key
            )

            # Check if used in plot_params as {{placeholder}}
            for param_value in self.plot_params.values():
                if (
                    isinstance(param_value, str)
                    and f"{{{{{short_name}}}}}" in param_value
                ):
                    return True

            # Check plot_kwargs (e.g., title)
            for kwarg_value in self.plot_kwargs.values():
                if (
                    isinstance(kwarg_value, str)
                    and f"{{{{{short_name}}}}}" in kwarg_value
                ):
                    # If used ONLY in title (not in params), it's visual-only
                    return True

            return False

        datasource_params = {}

        for key, value in control_values.items():
            # Rule 1: External subscribed states → datasource (UNLESS plot-params-only)
            if key in (self.subscribes or {}):
                if is_plot_params_only(key):
                    self.logger.debug(
                        f"[TypedChartBlock|Datasource] {key} (external state) "
                        f"→ SKIPPED (used only in plot_params placeholders)"
                    )
                    continue

                # Keys are already normalized by _normalize_control_keys
                # Check if explicit dep_param_name was provided
                if key in self._dep_param_names:
                    param_name = self._dep_param_names[key]
                    self.logger.debug(
                        f"[TypedChartBlock|Datasource] {key} (external state) "
                        f"→ datasource param '{param_name}' (from dep_param_name)"
                    )
                else:
                    # Use key as-is (already normalized)
                    param_name = key
                    self.logger.debug(
                        f"[TypedChartBlock|Datasource] {key} (external state) "
                        f"→ datasource param '{param_name}' (normalized key)"
                    )

                datasource_params[param_name] = value

            # Rule 2: NOT embedded control AND NOT known system key → maybe datasource
            elif key not in (self.controls or {}) and key not in ["section", "type"]:
                # This is legacy support or external param
                datasource_params[key] = value
                self.logger.debug(
                    f"[TypedChartBlock|Datasource] {key} (unknown) "
                    f"→ datasource param '{key}' (passthrough)"
                )

            # Embedded controls: skip (not for datasource)
            else:
                self.logger.debug(
                    f"[TypedChartBlock|Datasource] {key} (embedded control) "
                    f"→ skipped"
                )

        return datasource_params

    def _resolve_plot_params(self, control_values: Dict[str, Any]) -> Dict[str, Any]:
        """
        Resolve plot params by replacing {{placeholders}} with control values.

        :hierarchy: [Blocks | Charts | TypedChartBlock | ParamResolution]
        :contract:
         - pre: "control_values contains values from subscribed controls"
         - post: "Returns plot_params with placeholders replaced"
         - invariant: "Non-placeholder values unchanged"

        :complexity: 2
        :decision_cache: "Chose {{placeholder}} syntax for clarity"

        Args:
            control_values: Dict of control_name → value

        Returns:
            Resolved plot_params ready for plot function

        Example:
            >>> plot_params = {'x': 'age', 'color': '{{selected_category}}'}
            >>> control_values = {'selected_category': 'Premium'}
            >>> resolved = _resolve_plot_params(control_values)
            >>> # Result: {'x': 'age', 'color': 'Premium'}
        """
        resolved = {}

        for key, value in self.plot_params.items():
            resolved[key] = self._resolve_string_placeholders(value, control_values)
            self.logger.debug(
                f"[TypedChartBlock|Resolve] {key}: {value} → {resolved[key]}"
            )

        return resolved

    def _update_chart(self, *args, **kwargs) -> go.Figure:
        """
        Update chart using registered plot function.

        :hierarchy: [Blocks | Charts | TypedChartBlock | UpdateLogic]
        :relates-to:
         - motivated_by: "Core update logic with plot_kwargs passthrough"
         - implements: "method: '_update_chart'"
         - uses: ["method: 'get_processed_data'", "registered plot function"]

        :contract:
         - pre: "args[0] is {state_id: value} dict or initial values dict"
         - post: "Returns figure from plot function"
         - data_flow: "params → get_processed_data(params) → df → plot_func(df, **kwargs)"
         - kwargs_flow: "plot_kwargs passed to plot function"

        :complexity: 4
        :decision_cache: "Single update method handles all plot types via registry"

        Args:
            *args: Control values from subscribed states (dict with state IDs)

        Returns:
            Plotly Figure from registered plot function
        """
        # Log what we receive for debugging
        self.logger.debug(
            f"[TypedChartBlock|Update] _update_chart called with args={args}, "
            f"args types={[type(a).__name__ for a in args] if args else []}, kwargs={kwargs}"
        )

        # Check if first arg is a dict (multi-state or block-centric) or individual values (legacy)
        if args and isinstance(args[0], dict):
            # Multi-state or block-centric: first arg is control_values dict with state IDs
            control_values = args[0]
            self.logger.info(
                f"[TypedChartBlock|Update] {self.block_id} | "
                f"plot_type={self._plot_type} | mode=dict | controls={list(control_values.keys())}"
            )
        else:
            # Legacy state-centric or initial render
            self.logger.info(
                f"[TypedChartBlock|Update] {self.block_id} | "
                f"plot_type={self._plot_type} | mode=legacy | args={len(args)}"
            )
            control_values = self._extract_control_values(args, kwargs)

        try:
            self.logger.debug(
                f"[TypedChartBlock|Update] control_values={control_values}"
            )

            # Use new method for clear datasource parameter routing
            datasource_params = self._extract_datasource_params(control_values)

            self.logger.debug(
                f"[TypedChartBlock|ParamSplit] "
                f"datasource_params={list(datasource_params.keys())}"
            )

            # Get filtered data (pipeline runs through cache)
            df = self.datasource.get_processed_data(datasource_params)
            self.logger.debug(
                f"[TypedChartBlock|Update] Received {len(df)} rows from datasource"
            )

            if df.empty:
                # Build context-aware error message
                error_context = []

                # Check if filters were applied
                if datasource_params:
                    applied_filters = [f"{k}={v}" for k, v in datasource_params.items()]
                    error_context.append(
                        f"Applied filters: {', '.join(applied_filters)}"
                    )
                else:
                    error_context.append("No filters applied")

                # Check if external states were used
                external_states = [
                    k for k in control_values.keys() if k in (self.subscribes or {})
                ]
                if external_states:
                    error_context.append(
                        f"External states: {', '.join(external_states)}"
                    )

                context_msg = " | ".join(error_context)

                self.logger.warning(
                    f"[TypedChartBlock|Update] Empty DataFrame for {self.block_id} | {context_msg}"
                )

                return go.Figure().add_annotation(
                    text=f"No data available ({context_msg})",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                )

            # Resolve plot params (replace {{placeholders}})
            resolved_params = self._resolve_plot_params(control_values)

            # Resolve plot_kwargs (replace {{placeholders}})
            resolved_kwargs = {
                k: self._resolve_string_placeholders(v, control_values)
                for k, v in self.plot_kwargs.items()
            }

            # Add dynamic plot_title if provided
            if self.plot_title:
                resolved_plot_title = self._resolve_string_placeholders(
                    self.plot_title, control_values
                )
                if resolved_plot_title:
                    resolved_kwargs["title"] = resolved_plot_title

            # Drop None values
            all_kwargs = {k: v for k, v in resolved_kwargs.items() if v is not None}

            self.logger.debug(
                f"[TypedChartBlock|Update] Calling plot function | "
                f"resolved_params={list(resolved_params.keys())} | "
                f"all_kwargs={list(all_kwargs.keys())}"
            )

            # Call registered plot function with resolved params and kwargs
            figure = self.plot_func(df, **resolved_params, **all_kwargs)

            # Apply theme if available
            if self.theme_config:
                theme_layout = self.theme_config.get_figure_layout()
                figure.update_layout(**theme_layout)
                self.logger.debug(
                    f"[TypedChartBlock|Update] Applied theme {self.theme_config.name}"
                )

            self.logger.info("[TypedChartBlock|Update] Chart updated successfully")
            return figure

        except Exception as e:
            self.logger.error(
                f"[TypedChartBlock|Update] Error in {self.block_id}: {e}", exc_info=True
            )
            return go.Figure().add_annotation(
                text=f"Error: {str(e)[:100]}",
                showarrow=False,
                xref="paper",
                yref="paper",
                x=0.5,
                y=0.5,
                font=dict(color="red"),
            )

    def layout(self) -> Component:
        """
        Render block layout with card, title, controls, and chart.

        :hierarchy: [Blocks | Charts | TypedChartBlock | Layout]
        :relates-to:
         - motivated_by: "Standard card-based layout for all chart types"
         - implements: "method: 'layout'"

        :contract:
         - pre: "Block initialized, theme may be available"
         - post: "Returns Dash Component tree"

        :complexity: 3

        Returns:
            Dash Component (Card with chart)
        """
        # Collect initial values from BOTH embedded controls AND external states
        initial_values = {
            name: ctrl.props.get("value")
            for name, ctrl in (self.controls or {}).items()
        }

        # Add external state initial values if available
        if hasattr(self, "_initial_external_values"):
            external_states = list(self.subscribes.keys()) if self.subscribes else []
            for state_id in external_states:
                if state_id in self._initial_external_values:
                    initial_values[state_id] = self._initial_external_values[state_id]

        self.logger.debug(
            f"[TypedChartBlock|Layout] Initial render | "
            f"embedded_controls={list(self.controls.keys()) if self.controls else []} | "
            f"external_states={list(self.subscribes.keys()) if self.subscribes else []} | "
            f"initial_values={list(initial_values.keys())}"
        )

        initial_chart = self._update_chart(initial_values)

        # Build card components
        card_content = []

        # Title (static card title, no placeholders supported)
        if self.title:
            themed_title_style = self._get_themed_style(
                "card", "title", self.title_style
            )
            title_props = {"className": self.title_className or "card-title"}
            if themed_title_style:
                title_props["style"] = themed_title_style

            # Static title: render once (no placeholders in card title)
            title_component = html.H4(self.title, **title_props)
            card_content.append(title_component)

        # Controls row (if present)
        if self.controls:
            control_components = []
            for key, control in self.controls.items():
                comp_id = self._generate_id(key)

                # Apply auto-size logic if enabled
                if control.auto_size:
                    comp_props = control.props.copy()
                    col_props = (control.col_props or {}).copy()

                    # Ensure column uses md="auto" if not explicitly set
                    if "md" not in col_props:
                        col_props["md"] = "auto"

                    # Apply auto-size styling based on component type
                    if control.component.__name__ == "Dropdown":  # dcc.Dropdown
                        # Compute longest label for min-width
                        longest_label_ch = self._compute_longest_label_ch(
                            comp_props.get("options", [])
                        )
                        cap = control.max_ch or 40
                        min_width_ch = min(max(longest_label_ch + 3, 10), cap)

                        # Build auto-size style
                        auto_style = {
                            "display": "inline-block",
                            "width": "fit-content",
                            "maxWidth": f"{cap}ch",
                            "minWidth": f"{min_width_ch}ch",
                        }

                        # Merge with existing style
                        existing_style = comp_props.get("style", {})
                        if isinstance(existing_style, dict):
                            auto_style.update(existing_style)
                        comp_props["style"] = auto_style

                        self.logger.debug(
                            f"[TypedChartBlock|AutoSize] Applied dcc.Dropdown auto-size | "
                            f"longest_label={longest_label_ch}ch | min_width={min_width_ch}ch | max_width={cap}ch"
                        )

                    elif control.component.__name__ in [
                        "Select",
                        "Input",
                        "Switch",
                    ]:  # dbc components
                        # Add Bootstrap w-auto class
                        existing_class = comp_props.get("className", "")
                        if "w-auto" not in existing_class:
                            comp_props["className"] = f"{existing_class} w-auto".strip()

                        # Add character-based width constraints
                        cap = control.max_ch or 40
                        auto_style = {"minWidth": "10ch", "maxWidth": f"{cap}ch"}

                        # Merge with existing style
                        existing_style = comp_props.get("style", {})
                        if isinstance(existing_style, dict):
                            auto_style.update(existing_style)
                        comp_props["style"] = auto_style

                        self.logger.debug(
                            f"[TypedChartBlock|AutoSize] Applied dbc.{control.component.__name__} auto-size | "
                            f"max_width={cap}ch"
                        )

                    comp = control.component(id=comp_id, **comp_props)
                    col = dbc.Col(comp, **col_props)
                else:
                    # Standard rendering without auto-size
                    comp = control.component(id=comp_id, **control.props)
                    col = dbc.Col(comp, **(control.col_props or {}))

                control_components.append(col)

            controls_row = dbc.Row(control_components, className="mb-1")
            card_content.append(controls_row)

        # Graph
        graph_props = {
            "id": self._generate_id("container"),
            "figure": initial_chart,
            "config": self.graph_config,
        }
        if self.graph_style:
            graph_props["style"] = self.graph_style

        card_content.append(
            dcc.Loading(
                id=self._generate_id("loading"),
                type=self.loading_type,
                children=dcc.Graph(**graph_props),
            )
        )

        # Build card
        themed_card_style = self._get_themed_style(
            "card", "background", self.card_style
        )
        # h-100 ensures equal height when multiple blocks in same row
        # Note: mb-4 removed, handled by Row.mb-4
        base_classes = "h-100"
        card_props = {
            "className": (
                f"{base_classes} {self.card_className}"
                if self.card_className
                else base_classes
            )
        }
        if themed_card_style:
            card_props["style"] = themed_card_style

        return dbc.Card(dbc.CardBody(card_content), **card_props)

    def _compute_longest_label_ch(self, options: List[Any]) -> int:
        """
        Compute the longest label length in characters from dropdown options.

        :hierarchy: [Blocks | Charts | TypedChartBlock | AutoSize]
        :relates-to:
         - motivated_by: "Auto-size controls need to know content width for min-width calculation"
         - implements: "method: '_compute_longest_label_ch'"

        :contract:
         - pre: "options is list of strings or dicts with label/value"
         - post: "Returns integer character count of longest label"

        Args:
            options: List of option strings or dicts with 'label' or 'value' keys

        Returns:
            Character count of longest label (minimum 1)
        """
        if not options:
            return 1

        max_length = 0
        for option in options:
            if isinstance(option, str):
                length = len(option)
            elif isinstance(option, dict):
                # Try 'label' first, then 'value' as fallback
                text = option.get("label") or option.get("value", "")
                length = len(str(text))
            else:
                length = len(str(option))

            max_length = max(max_length, length)

        return max(max_length, 1)  # Minimum 1 character
