"""
This module defines the abstract base class for all dashboard blocks.

"""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

from dash.development.base_component import Component

# Use forward references for type hints to avoid circular imports
from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.core.state import StateManager
from dashboard_lego.utils.exceptions import BlockError, ConfigurationError
from dashboard_lego.utils.logger import get_logger

if TYPE_CHECKING:
    from dashboard_lego.core.theme import ThemeConfig


class BaseBlock(ABC):
    """
    An abstract base class that defines the contract for all dashboard blocks.

        :hierarchy: [Feature | Global Interactivity | BaseBlock Refactoring]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Decouple block
           instantiation from state registration to solve chicken-and-egg
           problem with DashboardPage"
         - implements: "interface: 'BaseBlock'"
         - uses: ["interface: 'BaseDataSource'", "class: 'StateManager'"]

        :rationale: "Registration logic was moved from __init__ to a
         separate method to allow DashboardPage to inject the
         StateManager post-instantiation."
        :contract:
         - pre: "A unique block_id and a valid datasource must be provided."
         - post: "The block is ready for state registration and layout
           rendering."

    """

    def __init__(self, block_id: str, datasource: BaseDataSource, **kwargs):
        """
        Initializes the BaseBlock.

        Args:
            block_id: A unique identifier for this block instance.
            datasource: An instance of a class that implements the
                       BaseDataSource interface.
            allow_duplicate_output: If True, allows this block to share output targets
                                  with other blocks (useful for overlay scenarios).

        """
        self.logger = get_logger(__name__, BaseBlock)
        self.logger.info(f"Initializing block: {block_id}")
        self.logger.debug(
            f"Block {block_id} instantiated with datasource: {type(datasource).__name__}"
        )

        if not isinstance(block_id, str) or not block_id:
            error_msg = "block_id must be a non-empty string."
            self.logger.error(error_msg)
            raise ConfigurationError(error_msg)
        if not isinstance(datasource, BaseDataSource):
            error_msg = "datasource must be an instance of BaseDataSource."
            self.logger.error(error_msg)
            raise ConfigurationError(error_msg)

        self.block_id = block_id
        self.datasource = datasource
        self.publishes: Optional[List[Dict[str, str]]] = kwargs.get("publishes")
        self.subscribes: Optional[Dict[str, Callable]] = kwargs.get("subscribes")
        self.allow_duplicate_output: bool = kwargs.get("allow_duplicate_output", False)

        # Theme configuration - will be set by DashboardPage
        self.theme_config: Optional["ThemeConfig"] = None

        self.logger.debug(
            f"Block initialized: publishes={bool(self.publishes)}, "
            f"subscribes={bool(self.subscribes)}, "
            f"allow_duplicate_output={self.allow_duplicate_output}"
        )

    def _register_state_interactions(self, state_manager: StateManager):
        """
        Registers the block's publications and subscriptions with the
        StateManager. This method is called by the DashboardPage after it
        has created the StateManager.

        Args:
            state_manager: The application's state manager instance.

        """
        self.logger.debug(f"Registering state interactions for {self.block_id}")

        try:
            # Register as a publisher
            if self.publishes:
                self.logger.info(
                    f"📢 Block {self.block_id} publishing {len(self.publishes)} state(s)"
                )
                for pub_info in self.publishes:
                    state_id = pub_info["state_id"]
                    component_prop = pub_info["component_prop"]
                    publisher_component_id = self._generate_id(state_id.split("-")[-1])
                    self.logger.debug(
                        f"  📡 Publisher: {state_id} -> "
                        f"{publisher_component_id}.{component_prop}"
                    )
                    state_manager.register_publisher(
                        state_id, publisher_component_id, component_prop
                    )

            # Register as a subscriber
            if self.subscribes:
                self.logger.info(
                    f"📻 Block {self.block_id} subscribing to {len(self.subscribes)} state(s)"
                )
                for state_id, callback_fn in self.subscribes.items():
                    subscriber_component_id = self._generate_id("container")
                    subscriber_component_prop = self._get_component_prop()
                    self.logger.debug(
                        f"  📥 Subscriber: {state_id} -> "
                        f"{subscriber_component_id}.{subscriber_component_prop} "
                        f"(callback: {callback_fn.__name__})"
                    )
                    state_manager.register_subscriber(
                        state_id,
                        subscriber_component_id,
                        subscriber_component_prop,
                        callback_fn,
                    )

            self.logger.info(
                f"✅ State interactions registered successfully for {self.block_id}"
            )
        except Exception as e:
            self.logger.error(
                f"Error registering state interactions for " f"{self.block_id}: {e}",
                exc_info=True,
            )
            raise BlockError(
                f"Failed to register state interactions for " f"{self.block_id}: {e}"
            ) from e

    def _set_theme_config(self, theme_config: "ThemeConfig") -> None:
        """
        Sets the theme configuration for this block.

            :hierarchy: [Feature | Theme System | Block Theme Integration]
            :relates-to:
             - motivated_by: "PRD: Blocks must access theme for automatic styling"
             - implements: "method: '_set_theme_config'"
             - uses: ["class: 'ThemeConfig'"]

            :rationale: "Called by DashboardPage to inject theme into all blocks."
            :contract:
             - pre: "theme_config is a valid ThemeConfig instance"
             - post: "Block can access theme for styling decisions"

        Args:
            theme_config: ThemeConfig instance to use for styling
        """
        self.theme_config = theme_config
        self.logger.debug(
            f"Theme '{theme_config.name}' applied to block {self.block_id}"
        )

    def _get_themed_style(
        self,
        component_type: str,
        element: str,
        overrides: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Gets theme-based styling with optional user overrides.

            :hierarchy: [Feature | Theme System | Styled Component Helper]
            :relates-to:
             - motivated_by: "PRD: Merge theme styles with user customizations"
             - implements: "method: '_get_themed_style'"
             - uses: ["method: 'get_component_style'"]

            :rationale: "Provides consistent theme application with override capability."
            :contract:
             - pre: "component_type and element are valid style keys"
             - post: "Returns merged style dict with overrides taking precedence"

        Args:
            component_type: Type of component (e.g., 'card', 'kpi', 'navigation')
            element: Specific element within component (e.g., 'background', 'title')
            overrides: Optional user-provided style overrides

        Returns:
            Dictionary with merged theme styles and overrides
        """
        # Start with theme styles if available
        if self.theme_config:
            base_style = self.theme_config.get_component_style(component_type, element)
        else:
            base_style = {}

        # Merge with user overrides (overrides take precedence)
        if overrides:
            merged_style = {**base_style, **overrides}
            self.logger.debug(
                f"Applied themed style for {component_type}.{element} with {len(overrides)} overrides"
            )
            return merged_style

        return base_style

    def _generate_id(self, component_name: str) -> str:
        """
        Generates a unique ID for a component within the block.

        """
        component_id = f"{self.block_id}-{component_name}"
        self.logger.debug(f"Generated component ID: {component_id}")
        return component_id

    @staticmethod
    def _normalize_subscribes_to(
        subscribes_to: Union[str, List[str], None],
    ) -> List[str]:
        """
        Normalizes the subscribes_to parameter to a list of state IDs.

        :hierarchy: [Blocks | Base | Multi-State Subscription Support]
        :relates-to:
         - motivated_by: "Bug Fix: Support subscribing to multiple states to
           enable complex dashboard patterns with multi-filter dependencies"
         - implements: "method: '_normalize_subscribes_to'"

        :rationale: "Provides consistent handling of subscribes_to parameter
         across all block types, accepting both single strings and lists."
        :contract:
         - pre: "subscribes_to can be a string, list of strings, or None."
         - post: "Returns a list of state IDs (empty list if None)."

        Args:
            subscribes_to: Can be a single state ID (str), a list of state IDs,
                          or None.

        Returns:
            A list of state IDs. Returns empty list if input is None.

        """
        if subscribes_to is None:
            return []
        if isinstance(subscribes_to, str):
            return [subscribes_to]
        if isinstance(subscribes_to, list):
            return subscribes_to
        # Fallback for unexpected types
        return []

    def _get_component_prop(self) -> str:
        """
        Get the component property to update for this block type.

        :hierarchy: [Blocks | Base | Component Property]
        :relates-to:
         - motivated_by: "Different block types need different update properties"
         - implements: "method: '_get_component_prop'"

        :rationale: "Default to 'children' for most blocks, override for special cases."
        :contract:
         - pre: "Block is properly initialized."
         - post: "Returns the appropriate component property name."

        Returns:
            The component property name for updates.
        """
        return "children"

    def output_target(self) -> tuple[str, str]:
        """
        Returns the output target for this block's callback.

        :hierarchy: [Architecture | Output Targets | BaseBlock]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Explicit output targets enable
           proper callback binding and component property updates"
         - implements: "method: 'output_target'"
         - uses: ["method: '_generate_id'", "method: '_get_component_prop'"]

        :rationale: "Default implementation returns container with 'children' property."
        :contract:
         - pre: "Block is properly initialized."
         - post: "Returns tuple of (component_id, property_name) for callback output."

        Returns:
            Tuple of (component_id, property_name) for the block's output target.
        """
        component_id = self._generate_id("container")
        property_name = self._get_component_prop()
        return (component_id, property_name)

    def list_control_inputs(self) -> List[tuple[str, str]]:
        """
        Returns list of control inputs for this block.

        :hierarchy: [Architecture | Block-centric Callbacks | BaseBlock]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Block-centric callbacks improve
           performance and maintainability by reducing callback complexity"
         - implements: "method: 'list_control_inputs'"
         - uses: ["attribute: 'publishes'"]

        :rationale: "Default implementation extracts inputs from publishes attribute."
        :contract:
         - pre: "Block is properly initialized."
         - post: "Returns list of (component_id, property_name) tuples for inputs."

        Returns:
            List of (component_id, property_name) tuples for control inputs.
        """
        if not self.publishes:
            return []

        return [(pub["state_id"], pub["component_prop"]) for pub in self.publishes]

    def update_from_controls(self, control_values: Dict[str, Any]) -> Any:
        """
        Updates the block based on control values.

        :hierarchy: [Architecture | Block-centric Callbacks | BaseBlock]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Block-centric callbacks improve
           performance and maintainability by reducing callback complexity"
         - implements: "method: 'update_from_controls'"
         - uses: ["attribute: 'subscribes'"]

        :rationale: "Default implementation calls the first subscription callback."
        :contract:
         - pre: "Block has at least one subscription callback."
         - post: "Returns the result of the subscription callback."

        Args:
            control_values: Dictionary of control name -> value mappings.

        Returns:
            The result of the subscription callback.
        """
        if not self.subscribes:
            return None

        # Get the first subscription callback
        callback_fn = next(iter(self.subscribes.values()))

        # Convert control_values to kwargs format expected by callbacks
        kwargs = {}
        for control_name, value in control_values.items():
            # Create the full component ID for the control
            component_id = self._generate_id(control_name)
            kwargs[component_id] = value

        return callback_fn(**kwargs)

    @abstractmethod
    def layout(self) -> Component:
        """
        Returns the Dash component layout for the block.

        """
        self.logger.debug(f"Rendering layout for block {self.block_id}")
        pass

    def register_callbacks(self, app: Any):
        """
        This method's role is now handled by the StateManager.

        """
        pass
