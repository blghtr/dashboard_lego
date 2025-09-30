"""
This module defines chart-related blocks.

"""
from typing import Callable, Any, Dict, Type, Optional, List
from dataclasses import dataclass, field

import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.development.base_component import Component
import plotly.graph_objects as go

from blocks.base import BaseBlock
from core.datasource import BaseDataSource
from core.chart_context import ChartContext
from core.state import StateManager
from utils.exceptions import BlockError


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
    changes.

        :hierarchy: [Blocks | Charts | StaticChartBlock]
        :relates-to:
         - motivated_by: "PRD: Need to display visualizations that react to
           global filters"
         - implements: "block: 'StaticChartBlock'"
         - uses: ["interface: 'BaseBlock'"]

        :contract:
         - pre: "A valid `subscribes_to` state ID and a `chart_generator`
           function must be provided."
         - post: "The block renders a chart that updates when the subscribed
           state changes."

    """

    def __init__(
        self, block_id: str, datasource: BaseDataSource, title: str,
        chart_generator: Callable, subscribes_to: str
    ):
        self.title = title
        self.chart_generator = chart_generator
        super().__init__(
            block_id, datasource,
            subscribes={subscribes_to: self._update_chart}
        )
        self.logger.debug(f"Static chart {block_id} with title: {title}")

    def _get_component_prop(self) -> str:
        """Override to use 'figure' property for Graph components."""
        return 'figure'

    def output_target(self) -> tuple[str, str]:
        """
        Returns the output target for chart blocks.
        
        :hierarchy: [Architecture | Output Targets | StaticChartBlock]
        :relates-to:
         - motivated_by: "ARCHITECTURE_REFACTOR_PLAN Step 2: Charts need 'figure' output"
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
            ctx = ChartContext(datasource=self.datasource, controls={}, logger=self.logger)
            
            # Use new ChartContext interface
            figure = self.chart_generator(df, ctx)
            
            self.logger.debug(f"Chart updated successfully for {self.block_id}")
            return figure
        except Exception as e:
            self.logger.error(
                f"Error updating StaticChartBlock [{self.block_id}]: {e}",
                exc_info=True
            )
            return go.Figure()

    def layout(self) -> Component:
        # Initialize with current chart instead of empty container
        initial_chart = self._update_chart()
        return dbc.Card(dbc.CardBody([
            html.H4(self.title, className="card-title"),
            dcc.Loading(id=self._generate_id("loading"), type="default",
                        children=dcc.Graph(id=self._generate_id("container"), figure=initial_chart))
        ]), className="mb-4")


class InteractiveChartBlock(BaseBlock):
    """
    A block for a chart that has its own interactive controls and can react
    to global state.

    This block is both a publisher (for its own controls) and a subscriber
    (to its own controls and optionally to external states).

        :hierarchy: [Blocks | Charts | InteractiveChartBlock]
        :relates-to:
         - motivated_by: "PRD: Need self-contained, interactive charts with
           their own controls"
         - implements: "block: 'InteractiveChartBlock'"
         - uses: ["interface: 'BaseBlock'", "dataclass: 'Control'"]

        :contract:
         - pre: "A `chart_generator` function and a dictionary of `controls`
           must be provided."
         - post: "The block renders a chart with UI controls that update the
           chart on interaction."

    """

    def __init__(
        self, block_id: str, datasource: BaseDataSource, title: str,
        chart_generator: Callable, controls: Dict[str, Control],
        subscribes_to: Optional[List[str]] = None
    ):
        self.title = title
        self.chart_generator = chart_generator
        self.controls = controls

        # Call super() FIRST to set self.block_id
        super().__init__(block_id, datasource)
        self.logger.debug(f"Interactive chart {block_id} with title: {title}, controls: {list(controls.keys())}")

        # Now that block_id is set, we can safely generate state interactions
        publishes = [
            {'state_id': self._generate_id(key), 'component_prop': 'value'}
            for key in self.controls
        ]
        all_subscriptions = (subscribes_to or []) + [p['state_id'] for p in publishes]

        # Set the state interaction attributes on the instance
        self.publishes = publishes
        self.subscribes = {
            state: self._update_chart for state in all_subscriptions
        }

    def _get_component_prop(self) -> str:
        """Override to use 'figure' property for Graph components."""
        return 'figure'

    def output_target(self) -> tuple[str, str]:
        """
        Returns the output target for interactive chart blocks.
        
        :hierarchy: [Architecture | Output Targets | InteractiveChartBlock]
        :relates-to:
         - motivated_by: "ARCHITECTURE_REFACTOR_PLAN Step 2: Charts need 'figure' output"
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
            f"Updating interactive chart for {self.block_id} "
            f"with kwargs: {kwargs}"
        )
        try:
            df = self.datasource.get_processed_data()
            if df.empty:
                self.logger.warning(f"Empty data for chart {self.block_id}")
                return go.Figure()

            control_values = {k.split('-')[-1]: v for k, v in kwargs.items()}
            self.logger.debug(f"Control values: {control_values}")

            # Create ChartContext for unified interface
            ctx = ChartContext(datasource=self.datasource, controls=control_values, logger=self.logger)
            
            # Use new ChartContext interface
            figure = self.chart_generator(df, ctx)
            
            self.logger.debug(
                f"Interactive chart updated successfully for {self.block_id}"
            )
            return figure
        except Exception as e:
            self.logger.error(
                f"Error updating InteractiveChartBlock [{self.block_id}]: {e}",
                exc_info=True
            )
            return go.Figure()

    def _register_state_interactions(self, state_manager: StateManager):
        """
        Registers only publishers for controls, not subscribers.
        Subscribers are handled by the new block-centric callback system.
        
        :hierarchy: [Architecture | Block-centric Callbacks | InteractiveChartBlock]
        :relates-to:
         - motivated_by: "ARCHITECTURE_REFACTOR_PLAN Step 4: Prevent duplicate callbacks"
         - implements: "method: '_register_state_interactions' override"
         - uses: ["method: '_generate_id'"]
         
        :rationale: "Only register publishers for controls, let bind_callbacks() handle subscribers."
        :contract:
         - pre: "StateManager is initialized and ready to accept registrations."
         - post: "Control publishers are registered, no duplicate subscribers."
        """
        self.logger.debug(f"Registering control publishers for {self.block_id}")
        
        try:
            # Register publishers for each control
            for key in self.controls.keys():
                state_id = self._generate_id(key)
                component_id = self._generate_id(key)
                component_prop = 'value'  # Most controls use 'value' property
                
                self.logger.debug(
                    f"Registering control publisher: {state_id} -> "
                    f"{component_id}.{component_prop}"
                )
                state_manager.register_publisher(
                    state_id, component_id, component_prop
                )
            
            self.logger.info(
                f"Control publishers registered successfully for {self.block_id}"
            )
        except Exception as e:
            self.logger.error(
                f"Error registering control publishers for {self.block_id}: {e}",
                exc_info=True
            )
            raise BlockError(
                f"Failed to register control publishers for {self.block_id}: {e}"
            ) from e

    def list_control_inputs(self) -> list[tuple[str, str]]:
        """
        Returns list of (component_id, property) tuples for all controls.
        
        :hierarchy: [Architecture | Block-centric Callbacks | InteractiveChartBlock]
        :relates-to:
         - motivated_by: "ARCHITECTURE_REFACTOR_PLAN Step 4: One callback per block"
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
            prop = 'value'
            inputs.append((component_id, prop))
        return inputs

    def update_from_controls(self, control_values: dict):
        """
        Updates the chart based on control values.
        
        :hierarchy: [Architecture | Block-centric Callbacks | InteractiveChartBlock]
        :relates-to:
         - motivated_by: "ARCHITECTURE_REFACTOR_PLAN Step 4: One callback per block"
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
        kwargs = {f"{self.block_id}-{key}": value 
                  for key, value in control_values.items()}
        return self._update_chart(**kwargs)

    def layout(self) -> Component:
        # Initialize with current chart data using default control values
        initial_control_values = {}
        for key, control in self.controls.items():
            # Extract initial value from control props
            if 'value' in control.props:
                initial_control_values[key] = control.props['value']
        
        initial_chart = self._update_chart(**initial_control_values)
        
        control_elements = [
            dbc.Col(
                control.component(
                    id=self._generate_id(key), **control.props
                ),
                width="auto"
            )
            for key, control in self.controls.items()
        ]
        return dbc.Card(dbc.CardBody([
            html.H4(self.title, className="card-title"),
            dbc.Row(control_elements, className="mb-3 align-items-center"),
            dcc.Loading(id=self._generate_id("loading"), type="default",
                        children=dcc.Graph(id=self._generate_id("container"), figure=initial_chart))
        ]), className="mb-4")

