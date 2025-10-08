"""
This module defines chart-related blocks.

"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import dcc, html
from dash.development.base_component import Component

from dashboard_lego.blocks.base import BaseBlock
from dashboard_lego.core.chart_context import ChartContext
from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.core.state import StateManager


@dataclass
class Control:
    """
    A dataclass to define a UI control for an InteractiveChartBlock or ControlPanelBlock.

    :hierarchy: [Blocks | Controls | Control]
    :relates-to:
     - motivated_by: "PRD: Need responsive control layouts with explicit column sizing"
     - implements: "dataclass: 'Control' with col_props support"
     - uses: ["component: 'Dash Component'"]

    :rationale: "Added col_props to enable responsive Bootstrap column sizing for controls."
    :contract:
     - pre: "component is a valid Dash component type."
     - post: "Control can be rendered with custom column properties for responsive layout."

    """

    component: Type[Component]
    props: Dict[str, Any] = field(default_factory=dict)
    col_props: Optional[Dict[str, Any]] = field(
        default_factory=lambda: {"xs": 12, "md": "auto"}
    )


class StaticChartBlock(BaseBlock):
    """
    A block for displaying a single chart that is updated by external state
    changes with customizable styling options.

        :hierarchy: [Blocks | Charts | StaticChartBlock]
        :relates-to:
         - motivated_by: "PRD: Need to display visualizations that react to
           global filters with customizable styling"
         - implements: "block: 'StaticChartBlock'"
         - uses: ["interface: 'BaseBlock'"]

        :rationale: "Enhanced with style customization parameters to allow
         fine-grained control over appearance while maintaining backward
         compatibility."
        :contract:
         - pre: "A valid `subscribes_to` state ID and a `chart_generator`
           function must be provided."
         - post: "The block renders a chart that updates when the subscribed
           state changes with customizable styling applied."

    """

    def __init__(
        self,
        block_id: str,
        datasource: BaseDataSource,
        title: str,
        chart_generator: Callable,
        subscribes_to: Union[str, List[str]],
        # Style customization parameters
        card_style: Optional[Dict[str, Any]] = None,
        card_className: Optional[str] = None,
        title_style: Optional[Dict[str, Any]] = None,
        title_className: Optional[str] = None,
        loading_type: str = "default",
        graph_config: Optional[Dict[str, Any]] = None,
        graph_style: Optional[Dict[str, Any]] = None,
        figure_layout: Optional[Dict[str, Any]] = None,
        # Callback configuration
        allow_duplicate_output: bool = False,
    ):
        self.title = title
        self.chart_generator = chart_generator

        # Store style customization parameters
        self.card_style = card_style
        self.card_className = card_className
        self.title_style = title_style
        self.title_className = title_className
        self.loading_type = loading_type
        self.graph_config = graph_config or {}
        self.graph_style = graph_style
        self.figure_layout = figure_layout or {}

        # Normalize subscribes_to to list and build subscribes dict
        state_ids = self._normalize_subscribes_to(subscribes_to)
        subscribes_dict = {state_id: self._update_chart for state_id in state_ids}

        # Store subscribes dict for use in _update_chart BEFORE super().__init__
        # because layout() is called during page.build_layout() which accesses this
        self.subscribes = subscribes_dict

        super().__init__(
            block_id,
            datasource,
            subscribes=subscribes_dict,
            allow_duplicate_output=allow_duplicate_output,
        )

        self.logger.debug(f"Static chart {block_id} with title: {title}")

    def _get_component_prop(self) -> str:
        """Override to use 'figure' property for Graph components."""
        return "figure"

    def output_target(self) -> tuple[str, str]:
        """
        Returns the output target for chart blocks.

        :hierarchy: [Architecture | Output Targets | StaticChartBlock]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Chart components require
           figure property updates for Plotly integration"
         - implements: "method: 'output_target' override"
         - uses: ["method: '_generate_id'"]

        :rationale: "Chart blocks update the 'figure' property, not 'children'."
        :contract:
         - pre: "Block is properly initialized."
         - post: "Returns tuple with container ID and 'figure' property."

        Returns:
            Tuple of (container_id, 'figure') for chart output target.
        """
        component_id = self._generate_id("container")
        return (component_id, "figure")

    def _update_chart(self, *args, **kwargs) -> go.Figure:
        """
        Updates the chart with current data and subscribed state values.

        :hierarchy: [Blocks | Charts | StaticChartBlock | Update Logic]
        :relates-to:
         - motivated_by: "Bug Fix: StaticChartBlock must handle generic state updates, not hardcoded ones."
         - implements: "method: '_update_chart' with generic *args handling"
        :contract:
         - pre: "Datasource is available and chart_generator function is provided."
         - post: "Returns updated figure with subscribed state values passed to chart generator."
        """
        self.logger.info(
            f"🔄 Updating chart for {self.block_id} with {len(args)} positional args"
        )
        try:
            params = {}
            if args and hasattr(self, "subscribes") and self.subscribes:
                state_ids = list(self.subscribes.keys())
                for idx, value in enumerate(args):
                    if idx < len(state_ids):
                        params[state_ids[idx]] = value

                self.logger.debug(
                    f"Refreshing datasource for {self.block_id} with params: {params}"
                )
                self.datasource.init_data(params)

            df = self.datasource.get_processed_data()
            if df.empty:
                self.logger.warning(f"Empty data for chart {self.block_id}")
                return go.Figure()

            # For static charts, the context controls are the state values themselves
            control_values = params

            ctx = ChartContext(
                datasource=self.datasource, controls=control_values, logger=self.logger
            )

            self.logger.debug(f"📊 Calling chart_generator for {self.block_id}")
            figure = self.chart_generator(df, ctx)

            if self.theme_config:
                theme_layout = self.theme_config.get_figure_layout()
                figure.update_layout(**theme_layout)
                self.logger.debug(f"Applied theme '{self.theme_config.name}' to figure")

            if self.figure_layout:
                figure.update_layout(**self.figure_layout)

            self.logger.info(f"✅ Chart updated successfully for {self.block_id}")
            return figure
        except Exception as e:
            self.logger.error(
                f"❌ Error updating StaticChartBlock [{self.block_id}]: {e}",
                exc_info=True,
            )
            return go.Figure()

    def layout(self) -> Component:
        """
        Returns the Dash component layout for the StaticChartBlock with theme-aware styling.

        :hierarchy: [Blocks | Charts | StaticChartBlock | Layout]
        :relates-to:
         - motivated_by: "PRD: Automatic theme application to chart blocks"
         - implements: "method: 'layout' with theme integration"
         - uses: ["method: '_get_themed_style'", "attribute: 'card_style'", "attribute: 'title_style'"]

        :rationale: "Uses theme system for consistent styling with user override capability."
        :contract:
         - pre: "Block is properly initialized, theme_config may be available."
         - post: "Returns a themed Card component with automatic styling."

        """
        # Initialize with current chart instead of empty container
        initial_chart = self._update_chart()

        # Build card props with theme-aware style
        themed_card_style = self._get_themed_style(
            "card", "background", self.card_style
        )
        card_props = {
            "className": self.card_className or "mb-4",
        }
        if themed_card_style:
            card_props["style"] = themed_card_style

        # Build title props with theme-aware style
        themed_title_style = self._get_themed_style("card", "title", self.title_style)
        title_props = {
            "className": self.title_className or "card-title",
        }
        if themed_title_style:
            title_props["style"] = themed_title_style

        # Build graph props with style overrides
        graph_props = {
            "id": self._generate_id("container"),
            "figure": initial_chart,
            "config": self.graph_config,
        }
        if self.graph_style:
            graph_props["style"] = self.graph_style

        return dbc.Card(
            dbc.CardBody(
                [
                    html.H4(self.title, **title_props),
                    dcc.Loading(
                        id=self._generate_id("loading"),
                        type=self.loading_type,
                        children=dcc.Graph(**graph_props),
                    ),
                ]
            ),
            **card_props,
        )


class InteractiveChartBlock(BaseBlock):
    """
    A block for a chart that has its own interactive controls and can react
    to global state with customizable styling options.

    This block is both a publisher (for its own controls) and a subscriber
    (to its own controls and optionally to external states).

        :hierarchy: [Blocks | Charts | InteractiveChartBlock]
        :relates-to:
         - motivated_by: "PRD: Need self-contained, interactive charts with
           their own controls and customizable styling"
         - implements: "block: 'InteractiveChartBlock'"
         - uses: ["interface: 'BaseBlock'", "dataclass: 'Control'"]

        :rationale: "Enhanced with style customization parameters to allow fine-grained
         control over appearance while maintaining backward compatibility."
        :contract:
         - pre: "A `chart_generator` function and a dictionary of `controls`
           must be provided."
         - post: "The block renders a chart with UI controls that update the
           chart on interaction with customizable styling applied."

    """

    def __init__(
        self,
        block_id: str,
        datasource: BaseDataSource,
        title: str,
        chart_generator: Callable,
        controls: Dict[str, Control],
        subscribes_to: Union[str, List[str], None] = None,
        # Style customization parameters (inherited from StaticChartBlock)
        card_style: Optional[Dict[str, Any]] = None,
        card_className: Optional[str] = None,
        title_style: Optional[Dict[str, Any]] = None,
        title_className: Optional[str] = None,
        loading_type: str = "default",
        graph_config: Optional[Dict[str, Any]] = None,
        graph_style: Optional[Dict[str, Any]] = None,
        figure_layout: Optional[Dict[str, Any]] = None,
        # Interactive-specific parameters
        controls_row_style: Optional[Dict[str, Any]] = None,
        controls_row_className: Optional[str] = None,
    ):
        self.title = title
        self.chart_generator = chart_generator
        self.controls = controls
        self._external_subscribes_to = subscribes_to

        # Store style customization parameters
        self.card_style = card_style
        self.card_className = card_className
        self.title_style = title_style
        self.title_className = title_className
        self.loading_type = loading_type
        self.graph_config = graph_config or {}
        self.graph_style = graph_style
        self.figure_layout = figure_layout or {}
        self.controls_row_style = controls_row_style
        self.controls_row_className = controls_row_className

        # Call super() without state interaction logic
        super().__init__(block_id, datasource)
        self.logger.debug(
            f"Interactive chart {block_id} with title: {title}, controls: {list(controls.keys())}"
        )

    def _get_component_prop(self) -> str:
        """Override to use 'figure' property for Graph components."""
        return "figure"

    def output_target(self) -> tuple[str, str]:
        """
        Returns the output target for interactive chart blocks.

        :hierarchy: [Architecture | Output Targets | InteractiveChartBlock]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Chart components require
           figure property updates for Plotly integration"
         - implements: "method: 'output_target' override"
         - uses: ["method: '_generate_id'"]

        :rationale: "Interactive chart blocks update the 'figure' property, not 'children'."
        :contract:
         - pre: "Block is properly initialized."
         - post: "Returns tuple with container ID and 'figure' property."

        Returns:
            Tuple of (container_id, 'figure') for chart output target.
        """
        component_id = self._generate_id("container")
        return (component_id, "figure")

    def _update_chart(self, *args, **kwargs) -> go.Figure:
        """
        Updates the chart with current data and subscribed state values.
        This method handles two calling conventions:
        1. From layout(): Called with **kwargs representing initial control values.
        2. From StateManager: Called with *args representing all subscribed state values.
        """
        self.logger.debug(
            f"Updating interactive chart for {self.block_id} with {len(args)} args and {len(kwargs)} kwargs"
        )
        try:
            params = {}
            control_values = {}

            if kwargs and not args:
                # Called from layout() with initial control values
                self.logger.debug(f"Initial layout call with kwargs: {kwargs}")
                control_values = kwargs
                # The params for the datasource are just the initial control values
                params = {f"{self.block_id}-{k}": v for k, v in kwargs.items()}
            elif args:
                # Called from StateManager callback with positional args
                self.logger.debug(f"Callback call with args: {args}")
                all_subscription_keys = list(self.subscribes.keys())
                for i, value in enumerate(args):
                    if i < len(all_subscription_keys):
                        state_id = all_subscription_keys[i]
                        params[state_id] = value

                # Filter params to get just this block's own control values
                control_values = {
                    key.split("-", 1)[-1]: value
                    for key, value in params.items()
                    if key.startswith(self.block_id)
                }

            # Refresh datasource with all available parameters
            if params:
                self.logger.debug(
                    f"Refreshing datasource for {self.block_id} with params: {params}"
                )
                self.datasource.init_data(params)

            df = self.datasource.get_processed_data()
            if df.empty:
                self.logger.warning(f"Empty data for chart {self.block_id}")
                return go.Figure()

            self.logger.debug(f"Control values for chart_generator: {control_values}")

            ctx = ChartContext(
                datasource=self.datasource, controls=control_values, logger=self.logger
            )
            figure = self.chart_generator(df, ctx)

            if self.theme_config:
                theme_layout = self.theme_config.get_figure_layout()
                figure.update_layout(**theme_layout)
                self.logger.debug(
                    f"Applied theme '{self.theme_config.name}' to interactive chart"
                )

            if self.figure_layout:
                figure.update_layout(**self.figure_layout)

            self.logger.debug(
                f"Interactive chart updated successfully for {self.block_id}"
            )
            return figure
        except Exception as e:
            self.logger.error(
                f"Error updating InteractiveChartBlock [{self.block_id}]: {e}",
                exc_info=True,
            )
            return go.Figure()

    def _register_state_interactions(self, state_manager: StateManager):
        """
        Lazily defines and registers state interactions.

        This method is called by DashboardPage after the navigation context
        (self.navigation_mode, self.section_index) has been set. It moves
        the creation of `publishes` and `subscribes` attributes out of
        `__init__` to ensure that state and component IDs are generated
        with the correct context.

        :hierarchy: [Blocks | Charts | InteractiveChartBlock | State Registration]
        :relates-to:
         - motivated_by: "Refactoring to fix timing issue with lazy-loaded navigation sections"
         - implements: "Lazy state interaction setup for InteractiveChartBlock"
        :contract:
         - pre: "self.navigation_mode and self.section_index are set by DashboardPage."
         - post: "self.publishes and self.subscribes are populated; state interactions are registered with StateManager."
        :complexity: 3
        :decision_cache: "Chose lazy setup in _register_state_interactions over passing context into __init__ to keep block constructors clean and decouple them from page-level logic."
        """
        # Generate publishes list with string state_ids
        self.publishes = [
            {"state_id": f"{self.block_id}-{key}", "component_prop": "value"}
            for key in self.controls
        ]

        # Combine internal and external subscriptions
        external_subscriptions = self._normalize_subscribes_to(
            self._external_subscribes_to
        )
        internal_subscriptions = [p["state_id"] for p in self.publishes]
        all_subscriptions = external_subscriptions + internal_subscriptions

        # The keys for self.subscribes must be strings
        self.subscribes = {state: self._update_chart for state in all_subscriptions}

        # Now call the parent method to perform the actual registration
        super()._register_state_interactions(state_manager)

    def list_control_inputs(self) -> list[tuple[str, str]]:
        """
        Returns list of (component_id, property) tuples for all controls.

        :hierarchy: [Architecture | Block-centric Callbacks | InteractiveChartBlock]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Each block must manage its own
           callback lifecycle for modularity and performance"
         - implements: "method: 'list_control_inputs'"
         - uses: ["method: '_generate_id'"]

        :rationale: "Provides input list for block-centric callback registration."
        :contract:
         - pre: "Block is properly initialized with controls."
         - post: "Returns list of (component_id, property) tuples for all controls."

        Returns:
            List of (component_id, property) tuples for all control inputs.
        """
        inputs = []
        for key, control in self.controls.items():
            component_id = self._generate_id(key)
            # Most controls use 'value' property
            prop = "value"
            inputs.append((component_id, prop))
        return inputs

    def update_from_controls(self, control_values: dict):
        """
        Updates the chart based on control values.

        :hierarchy: [Architecture | Block-centric Callbacks | InteractiveChartBlock]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Each block must manage its own
           callback lifecycle for modularity and performance"
         - implements: "method: 'update_from_controls'"
         - uses: ["method: '_update_chart'"]

        :rationale: "Called by block-centric callback to update chart with control values."
        :contract:
         - pre: "Control values dictionary is provided."
         - post: "Returns updated figure for the chart."

        Args:
            control_values: Dictionary mapping control names to their values.

        Returns:
            Updated figure for the chart.
        """
        # Convert control_values to kwargs format expected by _update_chart
        kwargs = {
            f"{self.block_id}-{key}": value for key, value in control_values.items()
        }
        return self._update_chart(**kwargs)

    def layout(self) -> Component:
        """
        Returns the Dash component layout for the InteractiveChartBlock with theme-aware styling.

        :hierarchy: [Blocks | Charts | InteractiveChartBlock | Layout]
        :relates-to:
         - motivated_by: "PRD: Automatic theme application to interactive chart blocks"
         - implements: "method: 'layout' with theme integration"
         - uses: ["method: '_get_themed_style'", "attribute: 'card_style'", "attribute: 'title_style'"]

        :rationale: "Uses theme system for consistent styling with user override capability."
        :contract:
         - pre: "Block is properly initialized, theme_config may be available."
         - post: "Returns a themed Card component with automatic styling and controls."

        """
        # Initialize with current chart data using default control values
        initial_control_values = {}
        for key, control in self.controls.items():
            # Extract initial value from control props
            if "value" in control.props:
                initial_control_values[key] = control.props["value"]

        initial_chart = self._update_chart(**initial_control_values)

        # Build card props with theme-aware style
        themed_card_style = self._get_themed_style(
            "card", "background", self.card_style
        )
        card_props = {
            "className": self.card_className or "mb-4",
        }
        if themed_card_style:
            card_props["style"] = themed_card_style

        # Build title props with theme-aware style
        themed_title_style = self._get_themed_style("card", "title", self.title_style)
        title_props = {
            "className": self.title_className or "card-title",
        }
        if themed_title_style:
            title_props["style"] = themed_title_style

        # Build controls row props with style overrides
        controls_row_props = {
            "className": self.controls_row_className or "mb-3 align-items-center",
        }
        if self.controls_row_style:
            controls_row_props["style"] = self.controls_row_style

        # Build graph props with style overrides
        graph_props = {
            "id": self._generate_id("container"),
            "figure": initial_chart,
            "config": self.graph_config,
        }
        if self.graph_style:
            graph_props["style"] = self.graph_style

        control_elements = []
        for key, control in self.controls.items():
            # Use col_props from Control, with fallback to defaults
            col_props = control.col_props or {"xs": 12, "md": "auto"}

            self.logger.debug(
                f"🎨 Building interactive control '{key}' with col_props: {col_props}"
            )

            control_elements.append(
                dbc.Col(
                    control.component(id=self._generate_id(key), **control.props),
                    **col_props,
                )
            )

        return dbc.Card(
            dbc.CardBody(
                [
                    html.H4(self.title, **title_props),
                    dbc.Row(control_elements, **controls_row_props),
                    dcc.Loading(
                        id=self._generate_id("loading"),
                        type=self.loading_type,
                        children=dcc.Graph(**graph_props),
                    ),
                ]
            ),
            **card_props,
        )


class ControlPanelBlock(BaseBlock):
    """
    A block for displaying only UI controls (sliders, dropdowns, etc.) without any chart visualization.

    This block is primarily a publisher of control values to state, but can also subscribe
    to external states for synchronized control updates.

        :hierarchy: [Blocks | Controls | ControlPanelBlock]
        :relates-to:
         - motivated_by: "PRD: Need standalone control panels for dashboard settings
           and filters without chart visualization"
         - implements: "block: 'ControlPanelBlock'"
         - uses: ["interface: 'BaseBlock'", "dataclass: 'Control'"]

        :rationale: "Separated control panel functionality from InteractiveChartBlock
         to follow Single Responsibility Principle. Enables pure control panels
         for global settings."
        :contract:
         - pre: "A dictionary of `controls` must be provided."
         - post: "The block renders UI controls that publish their values to state,
           with optional initialization from datasource."

    """

    def __init__(
        self,
        block_id: str,
        datasource: BaseDataSource,
        title: str,
        controls: Dict[str, Control],
        subscribes_to: Union[str, List[str], None] = None,
        value_initializer: Optional[Callable] = None,
        # Style customization parameters
        card_style: Optional[Dict[str, Any]] = None,
        card_className: Optional[str] = None,
        title_style: Optional[Dict[str, Any]] = None,
        title_className: Optional[str] = None,
        controls_row_style: Optional[Dict[str, Any]] = None,
        controls_row_className: Optional[str] = None,
        container_style: Optional[Dict[str, Any]] = None,
        container_className: Optional[str] = None,
    ):
        self.title = title
        self.controls = controls
        self.value_initializer = value_initializer
        self._external_subscribes_to = subscribes_to

        # Store style customization parameters
        self.card_style = card_style
        self.card_className = card_className
        self.title_style = title_style
        self.title_className = title_className
        self.controls_row_style = controls_row_style
        self.controls_row_className = controls_row_className
        self.container_style = container_style
        self.container_className = container_className

        # Call super() without state interaction logic
        super().__init__(block_id, datasource)
        self.logger.debug(
            f"Control panel {block_id} with title: {title}, controls: {list(controls.keys())}"
        )

        # Initialize control values from datasource if value_initializer is provided
        self._initial_control_values = self._initialize_control_values()

    def _register_state_interactions(self, state_manager: StateManager):
        """
        Lazily defines and registers state interactions.

        This method is called by DashboardPage after the navigation context
        (self.navigation_mode, self.section_index) has been set. It moves
        the creation of `publishes` and `subscribes` attributes out of
        `__init__` to ensure that state and component IDs are generated
        with the correct context.

        :hierarchy: [Blocks | Controls | ControlPanelBlock | State Registration]
        :relates-to:
         - motivated_by: "Refactoring to fix timing issue with lazy-loaded navigation sections"
         - implements: "Lazy state interaction setup for ControlPanelBlock"
        :contract:
         - pre: "self.navigation_mode and self.section_index are set by DashboardPage."
         - post: "self.publishes and self.subscribes are populated; state interactions are registered with StateManager."
        :complexity: 3
        :decision_cache: "Chose lazy setup in _register_state_interactions over passing context into __init__ to keep block constructors clean and decouple them from page-level logic."
        """
        # Publishes: each control publishes its value to state
        self.publishes = [
            {"state_id": f"{self.block_id}-{key}", "component_prop": "value"}
            for key in self.controls
        ]

        # Subscribes: optionally subscribe to external states
        subscribes_dict = {}
        if self._external_subscribes_to:
            external_subscriptions = self._normalize_subscribes_to(
                self._external_subscribes_to
            )
            subscribes_dict = {
                state: self._update_controls for state in external_subscriptions
            }
        self.subscribes = subscribes_dict

        super()._register_state_interactions(state_manager)

    def _initialize_control_values(self) -> Dict[str, Any]:
        """
        Initializes control values from datasource using value_initializer.

        :hierarchy: [Blocks | Controls | ControlPanelBlock | Initialization]
        :relates-to:
         - motivated_by: "PRD: Control panels should be able to initialize
           their values dynamically from datasource"
         - implements: "method: '_initialize_control_values'"
         - uses: ["attribute: 'value_initializer'", "method: 'datasource.get_processed_data'"]

        :rationale: "Enables dynamic initialization of control values based on data,
         such as setting slider ranges based on data min/max."
        :contract:
         - pre: "Datasource is available; value_initializer is optional."
         - post: "Returns dictionary of control_name -> value mappings, or empty dict."

        Returns:
            Dictionary mapping control names to their initial values.

        """
        if not self.value_initializer:
            return {}

        try:
            df = self.datasource.get_processed_data()
            if df.empty:
                self.logger.warning(f"Empty data for control panel {self.block_id}")
                return {}

            initialized_values = self.value_initializer(df)
            self.logger.debug(f"Initialized control values: {initialized_values}")
            return initialized_values
        except Exception as e:
            self.logger.error(
                f"Error initializing control values for {self.block_id}: {e}",
                exc_info=True,
            )
            return {}

    def _update_controls(self, *args, **kwargs) -> Component:
        """
        Updates the control panel in response to external state changes.

        :hierarchy: [Blocks | Controls | ControlPanelBlock | Update Logic]
        :relates-to:
         - motivated_by: "PRD: Control panels should be able to react to
           external state changes for synchronized updates"
         - implements: "method: '_update_controls'"
         - uses: ["method: 'layout'"]

        :rationale: "Allows control panels to be updated based on external states,
         enabling scenarios like resetting controls or synchronized multi-panel UIs."
        :contract:
         - pre: "Block is properly initialized."
         - post: "Returns updated control panel layout."

        Returns:
            Updated Dash component with current control values.

        """
        self.logger.debug(f"Updating control panel for {self.block_id}")
        try:
            # Re-initialize control values if needed
            self._initial_control_values = self._initialize_control_values()

            # Return the control elements (no need to recreate entire layout)
            return self._build_control_elements()
        except Exception as e:
            self.logger.error(
                f"Error updating ControlPanelBlock [{self.block_id}]: {e}",
                exc_info=True,
            )
            return html.Div("Error updating controls")

    def _build_control_elements(self) -> Component:
        """
        Builds the control elements row with responsive column sizing.

        :hierarchy: [Blocks | Controls | ControlPanelBlock | Layout Helper]
        :relates-to:
         - motivated_by: "PRD: Need responsive control layouts with explicit column sizing"
         - implements: "method: '_build_control_elements' with col_props support"
         - uses: ["attribute: 'controls'", "dataclass: 'Control'"]

        :rationale: "Enhanced to use col_props from Control dataclass for responsive Bootstrap layout."
        :contract:
         - pre: "Controls are defined and block_id is set."
         - post: "Returns Row component with responsive control elements."

        Returns:
            dbc.Row component containing all controls with responsive column sizing.

        """
        control_elements = []
        for key, control in self.controls.items():
            # Merge initial values with control props if available
            control_props = control.props.copy()
            if key in self._initial_control_values:
                control_props["value"] = self._initial_control_values[key]

            # Use col_props from Control, with fallback to defaults
            col_props = control.col_props or {"xs": 12, "md": "auto"}

            self.logger.debug(
                f"🎨 Building control '{key}' with col_props: {col_props}"
            )

            control_elements.append(
                dbc.Col(
                    control.component(id=self._generate_id(key), **control_props),
                    **col_props,
                )
            )

        # Build controls row props with style overrides
        controls_row_props = {
            "className": self.controls_row_className or "mb-3 align-items-center",
        }
        if self.controls_row_style:
            controls_row_props["style"] = self.controls_row_style

        return dbc.Row(control_elements, **controls_row_props)

    def list_control_inputs(self) -> list[tuple[str, str]]:
        """
        Returns empty list because ControlPanelBlock does not need block-centric callbacks.

        :hierarchy: [Architecture | Block-centric Callbacks | ControlPanelBlock]
        :relates-to:
         - motivated_by: "Bug Fix: ControlPanelBlock should not have block-centric callbacks"
         - implements: "method: 'list_control_inputs'"

        :rationale: "ControlPanelBlock only publishes values, it doesn't need to update from external controls.
                    Block-centric callbacks would create circular dependencies and break the UI."

        :contract:
         - pre: "Block is properly initialized."
         - post: "Returns empty list to prevent block-centric callback registration."

        Returns:
            Empty list to prevent block-centric callback registration.

        """
        # ControlPanelBlock only publishes values, it doesn't need block-centric callbacks
        # because it would create circular dependencies and break the UI
        return []

    def layout(self) -> Component:
        """
        Returns the Dash component layout for the ControlPanelBlock with theme-aware styling.

        :hierarchy: [Blocks | Controls | ControlPanelBlock | Layout]
        :relates-to:
         - motivated_by: "PRD: Automatic theme application to control panel blocks"
         - implements: "method: 'layout' with theme integration"
         - uses: ["method: '_get_themed_style'", "attribute: 'card_style'", "attribute: 'title_style'"]

        :rationale: "Uses theme system for consistent styling with user override capability."
        :contract:
         - pre: "Block is properly initialized, theme_config may be available."
         - post: "Returns a themed Card component with automatic styling and controls."

        Returns:
            Dash Card component containing the control panel.

        """
        # Build card props with theme-aware style
        themed_card_style = self._get_themed_style(
            "card", "background", self.card_style
        )
        card_props = {
            "className": self.card_className or "mb-4",
        }
        if themed_card_style:
            card_props["style"] = themed_card_style

        # Build title props with theme-aware style
        themed_title_style = self._get_themed_style("card", "title", self.title_style)
        title_props = {
            "className": self.title_className or "card-title",
        }
        if themed_title_style:
            title_props["style"] = themed_title_style

        # Build container props with style overrides
        container_props = {
            "id": self._generate_id("container"),
            "children": self._build_control_elements(),
        }
        if self.container_style:
            container_props["style"] = self.container_style
        if self.container_className:
            container_props["className"] = self.container_className

        return dbc.Card(
            dbc.CardBody(
                [
                    html.H4(self.title, **title_props),
                    html.Div(**container_props),
                ]
            ),
            **card_props,
        )
