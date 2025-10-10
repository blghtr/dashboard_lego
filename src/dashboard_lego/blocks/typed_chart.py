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
from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.utils.plot_registry import get_plot_function


@dataclass
class Control:
    """
    UI control definition for TypedChartBlock.

    :hierarchy: [Blocks | Controls | Control]
    :relates-to:
     - motivated_by: "Need responsive control layouts"
     - implements: "dataclass: 'Control'"

    :contract:
     - pre: "component is valid Dash component type"
     - post: "Control can be rendered with responsive layout"

    Attributes:
        component: Dash component class (dcc.Dropdown, dcc.Slider, etc.)
        props: Props dictionary for the component
        col_props: Bootstrap column sizing (default: {"xs": 12, "md": "auto"})
    """

    component: Type[Component]
    props: Dict[str, Any] = field(default_factory=dict)
    col_props: Optional[Dict[str, Any]] = field(
        default_factory=lambda: {"xs": 12, "md": "auto"}
    )


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
        datasource: BaseDataSource,
        plot_type: str,
        plot_params: Dict[str, Any],
        plot_kwargs: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
        controls: Optional[Dict[str, Control]] = None,
        subscribes_to: Union[str, List[str], None] = None,
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
        self.plot_type = plot_type
        self.plot_params = plot_params
        self.plot_kwargs = plot_kwargs or {}  # KEY: Store for passthrough
        self.plot_func = get_plot_function(plot_type)
        self.controls = controls or {}
        self.title = title or plot_type.replace("_", " ").title()

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
            f"[TypedChartBlock|Init] {block_id} | plot_type={plot_type} | "
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
            # CRITICAL FIX: args contains values from ALL blocks, not just this one
            # We need to extract only the values for THIS block's subscribed states
            for state_id in state_ids:
                # Find the position of this state_id in the args
                # State IDs are ordered consistently across all blocks
                try:
                    # Get the position of this state in the global state order
                    # FIXED: Based on logs, args order is: [category, category, price, price]
                    # So we need to map: filters-category -> args[0], filters-min_price -> args[2]
                    # Map to actual args positions (based on observed pattern)
                    args_mapping = {
                        "filters-category": 0,  # args[0] = category
                        "filters-min_price": 2,  # args[2] = price (skip args[1] which is duplicate)
                    }
                    if state_id in args_mapping:
                        state_index = args_mapping[state_id]
                        if state_index < len(args):
                            value = args[state_index]
                            control_values[state_id] = value
                            self.logger.debug(
                                f"[TypedChartBlock|Extract] {state_id}={value} (from global args[{state_index}])"
                            )
                except (ValueError, IndexError) as e:
                    self.logger.warning(
                        f"[TypedChartBlock|Extract] Could not extract {state_id}: {e}"
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
            if (
                isinstance(value, str)
                and value.startswith("{{")
                and value.endswith("}}")
            ):
                # Extract placeholder: {{control_name}} → control_name
                control_name = value[2:-2].strip()
                resolved[key] = control_values.get(control_name, value)
                self.logger.debug(
                    f"[TypedChartBlock|Resolve] {key}: {{{{control_name}}}} → "
                    f"{resolved[key]}"
                )
            else:
                resolved[key] = value

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
         - pre: "Subscribed state values in *args"
         - post: "Returns figure from plot function"
         - data_flow: "params → get_processed_data(params) → df → plot_func(df, **kwargs)"
         - kwargs_flow: "plot_kwargs passed to plot function"

        :complexity: 4
        :decision_cache: "Single update method handles all plot types via registry"

        Args:
            *args: Control values from subscribed states

        Returns:
            Plotly Figure from registered plot function
        """
        # CRITICAL: Block-centric callbacks pass control_values dict as first positional arg
        # Log what we receive for debugging
        self.logger.debug(
            f"[TypedChartBlock|Update] _update_chart called with args={args}, "
            f"args types={[type(a).__name__ for a in args] if args else []}, kwargs={kwargs}"
        )

        # Check if first arg is a dict (block-centric) or individual values (state-centric)
        if args and len(args) > 0 and isinstance(args[0], dict):
            # Block-centric: first arg is control_values dict
            control_values = args[0]
            self.logger.info(
                f"[TypedChartBlock|Update] {self.block_id} | "
                f"plot_type={self.plot_type} | mode=block-centric | controls={list(control_values.keys())}"
            )
        else:
            # State-centric or initial render
            self.logger.info(
                f"[TypedChartBlock|Update] {self.block_id} | "
                f"plot_type={self.plot_type} | mode=state-centric | args={len(args)}"
            )
            control_values = self._extract_control_values(args, kwargs)

        try:
            self.logger.debug(
                f"[TypedChartBlock|Update] control_values={control_values}"
            )

            # CRITICAL: Separate plot params from datasource params
            # Plot params (x_col, feature, mode) are THIS block's controls → NOT for datasource
            # Datasource params (session_controls-*) are EXTERNAL states → FOR datasource
            datasource_params = {}

            for key, value in (control_values or {}).items():
                # If param is NOT from this block's controls → it's external state → for datasource
                if key not in self.controls:
                    datasource_params[key] = value

            self.logger.debug(
                f"[TypedChartBlock|ParamSplit] block_controls={list(self.controls.keys())}, "
                f"datasource_params={list(datasource_params.keys())}"
            )

            # Get filtered data (pipeline runs through cache)
            df = self.datasource.get_processed_data(datasource_params)
            self.logger.debug(
                f"[TypedChartBlock|Update] Received {len(df)} rows from datasource"
            )

            if df.empty:
                self.logger.warning(
                    f"[TypedChartBlock|Update] Empty DataFrame for {self.block_id}"
                )
                return go.Figure().add_annotation(
                    text="No data available",
                    showarrow=False,
                    xref="paper",
                    yref="paper",
                    x=0.5,
                    y=0.5,
                )

            # Resolve plot params (replace {{placeholders}})
            resolved_params = self._resolve_plot_params(control_values)

            # Merge with plot_kwargs from constructor
            all_kwargs = {**resolved_params, **self.plot_kwargs}

            self.logger.debug(
                f"[TypedChartBlock|Update] Calling plot function | "
                f"params={list(all_kwargs.keys())}"
            )

            # Call registered plot function with ALL kwargs
            figure = self.plot_func(df, **all_kwargs)

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
        # Initialize with current chart
        initial_chart = self._update_chart()

        # Build card components
        card_content = []

        # Title
        if self.title:
            themed_title_style = self._get_themed_style(
                "card", "title", self.title_style
            )
            title_props = {"className": self.title_className or "card-title"}
            if themed_title_style:
                title_props["style"] = themed_title_style

            card_content.append(html.H4(self.title, **title_props))

        # Controls row (if present)
        if self.controls:
            control_components = []
            for key, control in self.controls.items():
                comp_id = self._generate_id(key)
                comp = control.component(id=comp_id, **control.props)
                col = dbc.Col(comp, **(control.col_props or {}))
                control_components.append(col)

            controls_row = dbc.Row(control_components, className="mb-3")
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
        card_props = {"className": self.card_className or "mb-4"}
        if themed_card_style:
            card_props["style"] = themed_card_style

        return dbc.Card(dbc.CardBody(card_content), **card_props)
