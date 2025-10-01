"""
This module defines the abstract base class for all dashboard blocks.

"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

from dash.development.base_component import Component

# Use forward references for type hints to avoid circular imports
from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.core.state import StateManager
from dashboard_lego.utils.exceptions import BlockError, ConfigurationError
from dashboard_lego.utils.logger import get_logger


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

        self.logger.debug(
            f"Block initialized: publishes={bool(self.publishes)}, "
            f"subscribes={bool(self.subscribes)}"
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
                self.logger.debug(f"Registering {len(self.publishes)} publishers")
                for pub_info in self.publishes:
                    state_id = pub_info["state_id"]
                    component_prop = pub_info["component_prop"]
                    publisher_component_id = self._generate_id(state_id.split("-")[-1])
                    self.logger.debug(
                        f"Registering publisher: {state_id} -> "
                        f"{publisher_component_id}.{component_prop}"
                    )
                    state_manager.register_publisher(
                        state_id, publisher_component_id, component_prop
                    )

            # Register as a subscriber
            if self.subscribes:
                self.logger.debug(f"Registering {len(self.subscribes)} subscriptions")
                for state_id, callback_fn in self.subscribes.items():
                    subscriber_component_id = self._generate_id("container")
                    subscriber_component_prop = self._get_component_prop()
                    self.logger.debug(
                        f"Registering subscriber: {state_id} -> "
                        f"{subscriber_component_id}.{subscriber_component_prop}"
                    )
                    state_manager.register_subscriber(
                        state_id,
                        subscriber_component_id,
                        subscriber_component_prop,
                        callback_fn,
                    )

            self.logger.info(
                f"State interactions registered successfully for " f"{self.block_id}"
            )
        except Exception as e:
            self.logger.error(
                f"Error registering state interactions for " f"{self.block_id}: {e}",
                exc_info=True,
            )
            raise BlockError(
                f"Failed to register state interactions for " f"{self.block_id}: {e}"
            ) from e

    def _generate_id(self, component_name: str) -> str:
        """
        Generates a unique ID for a component within the block.

        """
        component_id = f"{self.block_id}-{component_name}"
        self.logger.debug(f"Generated component ID: {component_id}")
        return component_id

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
