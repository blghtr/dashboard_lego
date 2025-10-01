"""
This module defines chart-related blocks.

"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type

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
    A dataclass to define a UI control for an InteractiveChartBlock.

    """

    component: Type[Component]
    props: Dict[str, Any] = field(default_factory=dict)


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
        subscribes_to: str,
        # Style customization parameters
        card_style: Optional[Dict[str, Any]] = None,
        card_className: Optional[str] = None,
        title_style: Optional[Dict[str, Any]] = None,
        title_className: Optional[str] = None,
        loading_type: str = "default",
        graph_config: Optional[Dict[str, Any]] = None,
        graph_style: Optional[Dict[str, Any]] = None,
        figure_layout: Optional[Dict[str, Any]] = None,
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

        super().__init__(
            block_id, datasource, subscribes={subscribes_to: self._update_chart}
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

    def _update_chart(self, *args) -> go.Figure:
        self.logger.debug(f"Updating chart for {self.block_id}")
        try:
            df = self.datasource.get_processed_data()
            if df.empty:
                self.logger.warning(f"Empty data for chart {self.block_id}")
                return go.Figure()

            # Create ChartContext for unified interface
            ctx = ChartContext(
                datasource=self.datasource, controls={}, logger=self.logger
            )

            # Use new ChartContext interface
            figure = self.chart_generator(df, ctx)

            # Apply figure layout overrides if provided
            if self.figure_layout:
                figure.update_layout(**self.figure_layout)

            self.logger.debug(f"Chart updated successfully for {self.block_id}")
            return figure
        except Exception as e:
            self.logger.error(
                f"Error updating StaticChartBlock [{self.block_id}]: {e}", exc_info=True
            )
            return go.Figure()

    def layout(self) -> Component:
        """
        Returns the Dash component layout for the StaticChartBlock with customizable styling.

        :hierarchy: [Blocks | Charts | StaticChartBlock | Layout]
        :relates-to:
         - motivated_by: "PRD: Need customizable styling for chart blocks"
         - implements: "method: 'layout' with style overrides"
         - uses: ["attribute: 'card_style'", "attribute: 'title_style'", "attribute: 'graph_config'"]

        :rationale: "Applied style customization parameters to all major UI elements."
        :contract:
         - pre: "Block is properly initialized with style parameters."
         - post: "Returns a styled Card component with customizable appearance."

        """
        # Initialize with current chart instead of empty container
        initial_chart = self._update_chart()

        # Build card props with style overrides
        card_props = {
            "className": self.card_className or "mb-4",
        }
        if self.card_style:
            card_props["style"] = self.card_style

        # Build title props with style overrides
        title_props = {
            "className": self.title_className or "card-title",
        }
        if self.title_style:
            title_props["style"] = self.title_style

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
        subscribes_to: Optional[List[str]] = None,
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

        # Call super() FIRST to set self.block_id
        super().__init__(block_id, datasource)
        self.logger.debug(
            f"Interactive chart {block_id} with title: {title}, controls: {list(controls.keys())}"
        )

        # Now that block_id is set, we can safely generate state interactions
        publishes = [
            {"state_id": self._generate_id(key), "component_prop": "value"}
            for key in self.controls
        ]
        all_subscriptions = (subscribes_to or []) + [p["state_id"] for p in publishes]

        # Set the state interaction attributes on the instance
        self.publishes = publishes
        self.subscribes = {state: self._update_chart for state in all_subscriptions}

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
        self.logger.debug(
            f"Updating interactive chart for {self.block_id} " f"with kwargs: {kwargs}"
        )
        try:
            df = self.datasource.get_processed_data()
            if df.empty:
                self.logger.warning(f"Empty data for chart {self.block_id}")
                return go.Figure()

            control_values = {k.split("-")[-1]: v for k, v in kwargs.items()}
            self.logger.debug(f"Control values: {control_values}")

            # Create ChartContext for unified interface
            ctx = ChartContext(
                datasource=self.datasource, controls=control_values, logger=self.logger
            )

            # Use new ChartContext interface
            figure = self.chart_generator(df, ctx)

            # Apply figure layout overrides if provided
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
        Registers publishers and subscribers for interactive chart controls.
        Uses the base class implementation to handle both publishers and subscribers.

        :hierarchy: [Architecture | State Management | InteractiveChartBlock]
        :relates-to:
         - motivated_by: "PRD: Interactive charts need to respond to their own controls"
         - implements: "method: '_register_state_interactions' override"
         - uses: ["method: 'BaseBlock._register_state_interactions'"]

        :rationale: "Use base class implementation to register both publishers and subscribers."
        :contract:
         - pre: "StateManager is initialized and ready to accept registrations."
         - post: "Both control publishers and subscribers are registered."
        """
        # Use the base class implementation which handles both publishers and subscribers
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
        Returns the Dash component layout for the InteractiveChartBlock with customizable styling.

        :hierarchy: [Blocks | Charts | InteractiveChartBlock | Layout]
        :relates-to:
         - motivated_by: "PRD: Need customizable styling for interactive chart blocks"
         - implements: "method: 'layout' with style overrides"
         - uses: ["attribute: 'card_style'", "attribute: 'title_style'", "attribute: 'controls_row_style'"]

        :rationale: "Applied style customization parameters to all major UI elements including controls."
        :contract:
         - pre: "Block is properly initialized with style parameters."
         - post: "Returns a styled Card component with customizable appearance and controls."

        """
        # Initialize with current chart data using default control values
        initial_control_values = {}
        for key, control in self.controls.items():
            # Extract initial value from control props
            if "value" in control.props:
                initial_control_values[key] = control.props["value"]

        initial_chart = self._update_chart(**initial_control_values)

        # Build card props with style overrides
        card_props = {
            "className": self.card_className or "mb-4",
        }
        if self.card_style:
            card_props["style"] = self.card_style

        # Build title props with style overrides
        title_props = {
            "className": self.title_className or "card-title",
        }
        if self.title_style:
            title_props["style"] = self.title_style

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

        control_elements = [
            dbc.Col(
                control.component(id=self._generate_id(key), **control.props),
                width="auto",
            )
            for key, control in self.controls.items()
        ]

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
