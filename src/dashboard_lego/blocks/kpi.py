"""
This module defines the KPIBlock for displaying key performance indicators.

"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional, Union

import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.development.base_component import Component

from dashboard_lego.blocks.base import BaseBlock
from dashboard_lego.utils.formatting import format_number

if TYPE_CHECKING:
    from dashboard_lego.core.theme import ThemeConfig


def _create_kpi_card(
    title: str,
    value: str,
    icon: str,
    color: str = "primary",
    # Style customization parameters
    kpi_card_style: Optional[Dict[str, Any]] = None,
    kpi_card_className: Optional[str] = None,
    value_style: Optional[Dict[str, Any]] = None,
    value_className: Optional[str] = None,
    title_style: Optional[Dict[str, Any]] = None,
    title_className: Optional[str] = None,
    # Theme integration
    theme_config: Optional["ThemeConfig"] = None,
) -> dbc.Col:
    """
    Creates a KPI card with theme-aware styling.

    :hierarchy: [Blocks | KPIs | KPIBlock | Card Creation]
    :relates-to:
     - motivated_by: "PRD: Automatic theme application to KPI cards"
     - implements: "function: '_create_kpi_card' with theme integration"
     - uses: ["component: 'dbc.Card'", "component: 'html.H4'", "component: 'html.P'"]

    :rationale: "Uses theme system for colors and typography while maintaining user override capability."
    :contract:
     - pre: "Title, value, and icon strings are provided, theme_config may be available."
     - post: "Returns a themed KPI card component with automatic styling."

    """
    # Get theme-aware styles for KPI
    if theme_config:
        # Get theme colors for the specified color name
        color_map = {
            "primary": theme_config.colors.primary,
            "secondary": theme_config.colors.secondary,
            "success": theme_config.colors.success,
            "danger": theme_config.colors.danger,
            "warning": theme_config.colors.warning,
            "info": theme_config.colors.info,
        }
        bg_color = color_map.get(color, theme_config.colors.primary)

        # Build themed card style
        default_card_style = {
            "backgroundColor": bg_color,
            "color": theme_config.colors.white,
            "textAlign": "center",
            "border": f"1px solid {theme_config.colors.border}",
            "borderRadius": theme_config.spacing.border_radius,
            "padding": theme_config.spacing.card_padding,
            "margin": theme_config.spacing.sm,
        }
        card_style = {**default_card_style, **(kpi_card_style or {})}

        # Build themed value style
        default_value_style = {
            "fontSize": theme_config.typography.font_size_h2,
            "fontWeight": theme_config.typography.font_weight_bold,
        }
        themed_value_style = {**default_value_style, **(value_style or {})}

        # Build themed title style
        default_title_style = {
            "fontSize": theme_config.typography.font_size_sm,
        }
        themed_title_style = {**default_title_style, **(title_style or {})}
    else:
        # Fallback to Bootstrap classes if no theme available
        card_style = kpi_card_style
        themed_value_style = value_style
        themed_title_style = title_style

    # Build card props
    if theme_config:
        card_props = {
            "className": kpi_card_className or "text-center m-2",
            "style": card_style,
        }
    else:
        default_card_class = f"text-center text-white bg-{color} m-2"
        card_props = {
            "className": kpi_card_className or default_card_class,
        }
        if kpi_card_style:
            card_props["style"] = kpi_card_style

    # Build value props
    value_props = {
        "className": value_className or "card-title",
    }
    if themed_value_style:
        value_props["style"] = themed_value_style

    # Build title props
    title_props = {
        "className": title_className or "card-text",
    }
    if themed_title_style:
        title_props["style"] = themed_title_style

    return dbc.Col(
        dbc.Card(
            dbc.CardBody(
                [
                    html.H4(value, **value_props),
                    html.P(title, **title_props),
                ]
            ),
            **card_props,
        )
    )


class KPIBlock(BaseBlock):
    """
    A block for displaying a row of Key Performance Indicators (KPIs) with
    customizable styling.

    This block subscribes to a state and updates its KPI values when the state
    changes.

        :hierarchy: [Blocks | KPIs | KPIBlock]
        :relates-to:
          - motivated_by: "PRD: Need to display summary statistics that react
            to filters with customizable styling"
          - implements: "block: 'KPIBlock'"
          - uses: ["interface: 'BaseBlock'"]

        :rationale: "Enhanced with style customization parameters to allow
         fine-grained control over KPI appearance while maintaining backward
         compatibility."
        :contract:
          - pre: "A `subscribes_to` state ID and a list of `kpi_definitions`
            must be provided."
          - post: "The block renders a series of KPI cards that update on
            state change with customizable styling applied."

    """

    def __init__(
        self,
        block_id: str,
        datasource: Any,
        kpi_definitions: List[Dict[str, str]],
        subscribes_to: Union[str, List[str]],
        # Style customization parameters
        container_style: Optional[Dict[str, Any]] = None,
        container_className: Optional[str] = None,
        loading_type: str = "default",
        # KPI card styling parameters
        kpi_card_style: Optional[Dict[str, Any]] = None,
        kpi_card_className: Optional[str] = None,
        value_style: Optional[Dict[str, Any]] = None,
        value_className: Optional[str] = None,
        title_style: Optional[Dict[str, Any]] = None,
        title_className: Optional[str] = None,
    ):
        self.kpi_definitions = kpi_definitions

        # Store style customization parameters
        self.container_style = container_style
        self.container_className = container_className
        self.loading_type = loading_type
        self.kpi_card_style = kpi_card_style
        self.kpi_card_className = kpi_card_className
        self.value_style = value_style
        self.value_className = value_className
        self.title_style = title_style
        self.title_className = title_className

        # Normalize subscribes_to to list and build subscribes dict
        state_ids = self._normalize_subscribes_to(subscribes_to)
        subscribes_dict = {state_id: self._update_kpi_cards for state_id in state_ids}

        super().__init__(block_id, datasource, subscribes=subscribes_dict)
        self.logger.debug(f"KPI block {block_id} with {len(kpi_definitions)} KPIs")

    def _update_kpi_cards(self, *args) -> Component:
        """
        Updates KPI cards with current data and applies style customization.

        :hierarchy: [Blocks | KPIs | KPIBlock | Update Logic]
        :relates-to:
         - motivated_by: "PRD: Need to display summary statistics that react
           to filters"
         - implements: "method: '_update_kpi_cards' with style overrides"
         - uses: ["function: '_create_kpi_card'", "method: 'format_number'"]

        :rationale: "Enhanced to pass style customization parameters to
         individual KPI cards."
        :contract:
         - pre: "Datasource is available and KPI definitions are set."
         - post: "Returns a Row of styled KPI cards with current data."

        """
        try:
            kpi_data = self.datasource.get_kpis()
            if not kpi_data:
                return dbc.Alert("Нет данных для KPI.", color="warning")
            cards = []
            for definition in self.kpi_definitions:
                key = definition["key"]
                value = kpi_data.get(key, "N/A")
                formatted_value = format_number(value)
                cards.append(
                    _create_kpi_card(
                        title=definition["title"],
                        value=formatted_value,
                        icon=definition.get("icon", ""),
                        color=definition.get("color", "primary"),
                        # Pass style customization parameters
                        kpi_card_style=self.kpi_card_style,
                        kpi_card_className=self.kpi_card_className,
                        value_style=self.value_style,
                        value_className=self.value_className,
                        title_style=self.title_style,
                        title_className=self.title_className,
                        # Pass theme configuration
                        theme_config=self.theme_config,
                    )
                )
            return dbc.Row(cards)
        except Exception as e:
            return dbc.Alert(f"Ошибка загрузки KPI: {str(e)}", color="danger")

    def layout(self) -> Component:
        """
        Returns the Dash component layout for the KPIBlock with customizable
        styling.

        :hierarchy: [Blocks | KPIs | KPIBlock | Layout]
        :relates-to:
         - motivated_by: "PRD: Need customizable styling for KPI blocks"
         - implements: "method: 'layout' with style overrides"
         - uses: ["attribute: 'container_style'", "attribute: 'loading_type'"]

        :rationale: "Applied style customization parameters to container and
         loading components."
        :contract:
         - pre: "Block is properly initialized with style parameters."
         - post: "Returns a styled Loading component with customizable
           appearance."

        """
        # Initialize with current data instead of empty container
        initial_content = self._update_kpi_cards()

        # Build container props with style overrides
        container_props = {
            "id": self._generate_id("container"),
            "children": initial_content,
        }
        if self.container_style:
            container_props["style"] = self.container_style
        if self.container_className:
            container_props["className"] = self.container_className

        return dcc.Loading(
            id=self._generate_id("loading"),
            type=self.loading_type,
            children=html.Div(**container_props),
        )
