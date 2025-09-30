"""
This module defines the KPIBlock for displaying key performance indicators.

"""
from typing import List, Dict, Any

import dash_bootstrap_components as dbc
from dash import html, dcc
from dash.development.base_component import Component

from blocks.base import BaseBlock
from utils.formatting import format_number

def _create_kpi_card(title: str, value: str, icon: str, color: str = "primary") -> dbc.Col:
    return dbc.Col(dbc.Card(dbc.CardBody([
        html.H4(value, className="card-title"),
        html.P(title, className="card-text"),
    ]), className=f"text-center text-white bg-{color} m-2"))

class KPIBlock(BaseBlock):
    """
    A block for displaying a row of Key Performance Indicators (KPIs).

    This block subscribes to a state and updates its KPI values when the state changes.

        :hierarchy: [Blocks | KPIs | KPIBlock]
        :relates-to:
          - motivated_by: "PRD: Need to display summary statistics that react to filters"
          - implements: "block: 'KPIBlock'"
          - uses: ["interface: 'BaseBlock'"]

        :contract:
          - pre: "A `subscribes_to` state ID and a list of `kpi_definitions` must be provided."
          - post: "The block renders a series of KPI cards that update on state change."

    """

    def __init__(self, block_id: str, datasource: Any, kpi_definitions: List[Dict[str, str]], subscribes_to: str):
        self.kpi_definitions = kpi_definitions
        super().__init__(block_id, datasource, subscribes={subscribes_to: self._update_kpi_cards})
        self.logger.debug(f"KPI block {block_id} with {len(kpi_definitions)} KPIs")

    def _update_kpi_cards(self, *args) -> Component:
        try:
            kpi_data = self.datasource.get_kpis()
            if not kpi_data: return dbc.Alert("Нет данных для KPI.", color="warning")
            cards = []
            for definition in self.kpi_definitions:
                key = definition['key']
                value = kpi_data.get(key, "N/A")
                formatted_value = format_number(value)
                cards.append(_create_kpi_card(
                    title=definition['title'], value=formatted_value,
                    icon=definition.get('icon', ''), color=definition.get('color', 'primary')
                ))
            return dbc.Row(cards)
        except Exception as e:
            return dbc.Alert(f"Ошибка загрузки KPI: {str(e)}", color="danger")

    def layout(self) -> Component:
        # Initialize with current data instead of empty container
        initial_content = self._update_kpi_cards()
        return dcc.Loading(id=self._generate_id("loading"), type="default",
                           children=html.Div(id=self._generate_id("container"), children=initial_content))