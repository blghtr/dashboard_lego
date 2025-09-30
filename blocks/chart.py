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

@dataclass
class Control:
    """
    A dataclass to define a UI control for an InteractiveChartBlock.

    """
    component: Type[Component]
    props: Dict[str, Any] = field(default_factory=dict)

class StaticChartBlock(BaseBlock):
    """
    A block for displaying a single chart that is updated by external state changes.

        :hierarchy: [Blocks | Charts | StaticChartBlock]
        :relates-to:
          - motivated_by: "PRD: Need to display visualizations that react to global filters"
          - implements: "block: 'StaticChartBlock'"
          - uses: ["interface: 'BaseBlock'"]

        :contract:
          - pre: "A valid `subscribes_to` state ID and a `chart_generator` function must be provided."
          - post: "The block renders a chart that updates when the subscribed state changes."

    """

    def __init__(self, block_id: str, datasource: BaseDataSource, title: str,
                 chart_generator: Callable, subscribes_to: str):
        self.title = title
        self.chart_generator = chart_generator
        super().__init__(block_id, datasource, subscribes={subscribes_to: self._update_chart})

    def _update_chart(self, *args) -> go.Figure:
        try:
            df = self.datasource.get_processed_data()
            return self.chart_generator(df) if not df.empty else go.Figure()
        except Exception as e:
            print(f"Error updating StaticChartBlock [{self.block_id}]: {e}")
            return go.Figure()

    def layout(self) -> Component:
        return dbc.Card(dbc.CardBody([
            html.H4(self.title, className="card-title"),
            dcc.Loading(id=self._generate_id("loading"), type="default",
                        children=html.Div(id=self._generate_id("container")))
        ]), className="mb-4")

class InteractiveChartBlock(BaseBlock):
    """
    A block for a chart that has its own interactive controls and can react to global state.

    This block is both a publisher (for its own controls) and a subscriber (to its own
    controls and optionally to external states).

        :hierarchy: [Blocks | Charts | InteractiveChartBlock]
        :relates-to:
          - motivated_by: "PRD: Need self-contained, interactive charts with their own controls"
          - implements: "block: 'InteractiveChartBlock'"
          - uses: ["interface: 'BaseBlock'", "dataclass: 'Control'"]

        :contract:
          - pre: "A `chart_generator` function and a dictionary of `controls` must be provided."
          - post: "The block renders a chart with UI controls that update the chart on interaction."

    """

    def __init__(self, block_id: str, datasource: BaseDataSource, title: str,
                 chart_generator: Callable, controls: Dict[str, Control],
                 subscribes_to: Optional[List[str]] = None):
        self.title = title
        self.chart_generator = chart_generator
        self.controls = controls

        # Call super() FIRST to set self.block_id
        super().__init__(block_id, datasource)

        # Now that block_id is set, we can safely generate state interactions
        publishes = [
            {'state_id': self._generate_id(key), 'component_prop': 'value'}
            for key in self.controls
        ]
        all_subscriptions = (subscribes_to or []) + [p['state_id'] for p in publishes]

        # Set the state interaction attributes on the instance
        self.publishes = publishes
        self.subscribes = {state: self._update_chart for state in all_subscriptions}

    def _update_chart(self, **kwargs) -> go.Figure:
        try:
            df = self.datasource.get_processed_data()
            if df.empty: return go.Figure()
            control_values = {k.split('-')[-1]: v for k, v in kwargs.items()}
            return self.chart_generator(df, self.datasource, **control_values)
        except Exception as e:
            print(f"Error updating InteractiveChartBlock [{self.block_id}]: {e}")
            return go.Figure()

    def layout(self) -> Component:
        control_elements = [
            dbc.Col(control.component(id=self._generate_id(key), **control.props), width="auto")
            for key, control in self.controls.items()
        ]
        return dbc.Card(dbc.CardBody([
            html.H4(self.title, className="card-title"),
            dbc.Row(control_elements, className="mb-3 align-items-center"),
            dcc.Loading(id=self._generate_id("loading"), type="default",
                        children=dcc.Graph(id=self._generate_id("container")))
        ]), className="mb-4")
