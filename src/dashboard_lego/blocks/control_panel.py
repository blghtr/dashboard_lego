"""
This module defines ControlPanelBlock for standalone control panels.

StaticChartBlock and InteractiveChartBlock removed in v0.15.0.
Use TypedChartBlock instead.

:hierarchy: [Blocks | Controls | ControlPanelBlock]
:relates-to:
 - motivated_by: "v0.15.0: Simplified architecture with TypedChartBlock"
 - implements: "block: 'ControlPanelBlock'"

:contract:
 - pre: "controls dict provided"
 - post: "Block publishes control values to state"

:complexity: 4
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Type, Union

import dash_bootstrap_components as dbc
from dash import html
from dash.development.base_component import Component

from dashboard_lego.blocks.base import BaseBlock
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.core.state import StateManager


@dataclass
class Control:
    """
    UI control definition for ControlPanelBlock or TypedChartBlock.

    :hierarchy: [Blocks | Controls | Control]
    :relates-to:
     - motivated_by: "Need responsive control layouts with content-based sizing"
     - implements: "dataclass: 'Control' with col_props and auto-size support"
     - uses: ["component: 'Dash Component'"]

    :rationale: "col_props enables responsive Bootstrap column sizing for controls, auto_size enables content-based width."
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


class ControlPanelBlock(BaseBlock):
    """
    Standalone control panel block (no chart visualization).

    This block publishes control values to state that other blocks can subscribe to.

    :hierarchy: [Blocks | Controls | ControlPanelBlock]
    :relates-to:
     - motivated_by: "Need standalone control panels for dashboard settings"
     - implements: "block: 'ControlPanelBlock'"
     - uses: ["interface: 'BaseBlock'", "dataclass: 'Control'"]

    :rationale: "Separated control functionality from chart blocks for SRP"
    :contract:
     - pre: "controls dict provided"
     - post: "Block renders controls that publish values to state"

    :complexity: 4
    """

    def __init__(
        self,
        block_id: str,
        datasource: DataSource,
        title: str,
        controls: Dict[str, Control],
        subscribes_to: Union[str, List[str], None] = None,
        value_initializer: Optional[Callable] = None,
        # Style customization
        card_style: Optional[Dict[str, Any]] = None,
        card_className: Optional[str] = None,
        title_style: Optional[Dict[str, Any]] = None,
        title_className: Optional[str] = None,
        controls_row_style: Optional[Dict[str, Any]] = None,
        controls_row_className: Optional[str] = None,
        container_style: Optional[Dict[str, Any]] = None,
        container_className: Optional[str] = None,
    ):
        """
        Initialize ControlPanelBlock.

        :hierarchy: [Blocks | Controls | ControlPanelBlock | Init]
        :contract:
         - pre: "controls dict provided"
         - post: "Block ready to render and publish values"

        Args:
            block_id: Unique identifier
            datasource: DataSource instance
            title: Panel title
            controls: Dict of control_name → Control
            value_initializer: Optional function (df) → {control_name: value}
        """
        self.title = title
        self.controls = controls
        self.value_initializer = value_initializer
        self._external_subscribes_to = subscribes_to

        # Store styling
        self.card_style = card_style
        self.card_className = card_className
        self.title_style = title_style
        self.title_className = title_className
        self.controls_row_style = controls_row_style
        self.controls_row_className = controls_row_className
        self.container_style = container_style
        self.container_className = container_className

        super().__init__(block_id, datasource)

        self.logger.info(
            f"[ControlPanelBlock|Init] {block_id} | controls={list(controls.keys())}"
        )

        # Initialize control values
        self._initial_control_values = self._initialize_control_values()

    def _register_state_interactions(self, state_manager: StateManager):
        """
        Register state interactions for control panel.

        :hierarchy: [Blocks | Controls | ControlPanelBlock | StateRegistration]
        :contract:
         - pre: "state_manager valid"
         - post: "Control publishes registered"

        Args:
            state_manager: StateManager instance
        """
        # Publish each control value
        self.publishes = [
            {
                "state_id": f"{self.block_id}-{key}",
                "component_prop": "value",
                "dep_param_name": control.dep_param_name,
            }
            for key, control in self.controls.items()
        ]

        # Subscribe to external states if provided
        subscribes_dict = {}
        if self._external_subscribes_to:
            external_subs = self._normalize_subscribes_to(self._external_subscribes_to)
            subscribes_dict = {state: self._update_controls for state in external_subs}

        self.subscribes = subscribes_dict

        super()._register_state_interactions(state_manager)

    def _initialize_control_values(self) -> Dict[str, Any]:
        """
        Initialize control values from datasource.

        :hierarchy: [Blocks | Controls | ControlPanelBlock | Initialization]
        :contract:
         - pre: "Datasource available, value_initializer optional"
         - post: "Returns dict of control_name → value or empty dict"

        Returns:
            Dictionary mapping control names to initial values
        """
        if not self.value_initializer:
            return {}

        try:
            # Get data without filtering
            df = self.datasource.get_processed_data({})
            if df.empty:
                self.logger.warning(f"Empty data for control panel {self.block_id}")
                return {}

            initialized_values = self.value_initializer(df)
            self.logger.debug(
                f"[ControlPanelBlock|Init] Initialized values: {initialized_values}"
            )
            return initialized_values

        except Exception as e:
            self.logger.error(
                f"Error initializing control values for {self.block_id}: {e}",
                exc_info=True,
            )
            return {}

    def _update_controls(self, *args, **kwargs) -> Component:
        """
        Update control panel in response to external state changes.

        :hierarchy: [Blocks | Controls | ControlPanelBlock | Update]
        :contract:
         - pre: "Block initialized"
         - post: "Returns updated control panel layout"

        Returns:
            Updated Dash component
        """
        self.logger.debug(f"Updating control panel for {self.block_id}")
        try:
            # Re-initialize if needed
            self._initial_control_values = self._initialize_control_values()
            return self._build_control_elements()
        except Exception as e:
            self.logger.error(
                f"Error updating ControlPanelBlock [{self.block_id}]: {e}",
                exc_info=True,
            )
            return html.Div("Error updating controls")

    def _build_control_elements(self) -> Component:
        """
        Build control elements row with responsive sizing.

        :hierarchy: [Blocks | Controls | ControlPanelBlock | LayoutHelper]
        :contract:
         - pre: "Controls defined, block_id set"
         - post: "Returns Row component with controls"

        Returns:
            dbc.Row with all controls
        """
        control_elements = []

        for key, control in self.controls.items():
            # Merge initial values with control props
            control_props = control.props.copy()
            if key in self._initial_control_values:
                control_props["value"] = self._initial_control_values[key]

            # Apply auto-size logic if enabled
            if control.auto_size:
                col_props = (control.col_props or {}).copy()

                # Ensure column uses md="auto" if not explicitly set
                if "md" not in col_props:
                    col_props["md"] = "auto"

                # Apply auto-size styling based on component type
                if control.component.__name__ == "Dropdown":  # dcc.Dropdown
                    # Compute longest label for min-width
                    longest_label_ch = self._compute_longest_label_ch(
                        control_props.get("options", [])
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
                    existing_style = control_props.get("style", {})
                    if isinstance(existing_style, dict):
                        auto_style.update(existing_style)
                    control_props["style"] = auto_style

                    self.logger.debug(
                        f"[ControlPanelBlock|AutoSize] Applied dcc.Dropdown auto-size | "
                        f"longest_label={longest_label_ch}ch | min_width={min_width_ch}ch | max_width={cap}ch"
                    )

                elif control.component.__name__ in [
                    "Select",
                    "Input",
                    "Switch",
                ]:  # dbc components
                    # Add Bootstrap w-auto class
                    existing_class = control_props.get("className", "")
                    if "w-auto" not in existing_class:
                        control_props["className"] = f"{existing_class} w-auto".strip()

                    # Add character-based width constraints
                    cap = control.max_ch or 40
                    auto_style = {"minWidth": "10ch", "maxWidth": f"{cap}ch"}

                    # Merge with existing style
                    existing_style = control_props.get("style", {})
                    if isinstance(existing_style, dict):
                        auto_style.update(existing_style)
                    control_props["style"] = auto_style

                    self.logger.debug(
                        f"[ControlPanelBlock|AutoSize] Applied dbc.{control.component.__name__} auto-size | "
                        f"max_width={cap}ch"
                    )

                # For sliders, ensure modern-slider class is applied for width styling
                elif (
                    control.component.__name__ == "Slider"
                    and "className" not in control_props
                ):
                    control_props["className"] = "modern-slider"
            else:
                # Standard rendering without auto-size
                col_props = control.col_props or {"xs": 12, "md": 12}

                # For sliders, ensure modern-slider class is applied for width styling
                if (
                    control.component.__name__ == "Slider"
                    and "className" not in control_props
                ):
                    control_props["className"] = "modern-slider"

            control_elements.append(
                dbc.Col(
                    control.component(id=self._generate_id(key), **control_props),
                    **col_props,
                )
            )

        # Build controls row
        controls_row_props = {
            "className": self.controls_row_className or "mb-3 align-items-center",
        }
        if self.controls_row_style:
            controls_row_props["style"] = self.controls_row_style

        return dbc.Row(control_elements, **controls_row_props)

    def list_control_inputs(self) -> list[tuple[str, str]]:
        """
        Returns empty list - ControlPanelBlock only publishes, no callbacks needed.

        :hierarchy: [Blocks | Controls | ControlPanelBlock | NoCallbacks]
        :contract:
         - pre: "Block initialized"
         - post: "Returns empty list"

        Returns:
            Empty list (no block-centric callbacks)
        """
        return []

    def layout(self) -> Component:
        """
        Render control panel layout with theme-aware styling.

        :hierarchy: [Blocks | Controls | ControlPanelBlock | Layout]
        :contract:
         - pre: "Block initialized, theme may be available"
         - post: "Returns themed Card with controls"

        Returns:
            Dash Card component
        """
        # Apply theme-aware styling
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

        themed_title_style = self._get_themed_style("card", "title", self.title_style)
        title_props = {"className": self.title_className or "card-title"}
        if themed_title_style:
            title_props["style"] = themed_title_style

        # Build container
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

    def _compute_longest_label_ch(self, options: List[Any]) -> int:
        """
        Compute the longest label length in characters from dropdown options.

        :hierarchy: [Blocks | Controls | ControlPanelBlock | AutoSize]
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
