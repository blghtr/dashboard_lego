"""
This module defines the abstract base class for all dashboard blocks.

"""
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Callable

from dash.development.base_component import Component

# Use forward references for type hints to avoid circular imports
from core.datasource import BaseDataSource
from core.state import StateManager

class BaseBlock(ABC):
    """
    An abstract base class that defines the contract for all dashboard blocks.

        :hierarchy: [Feature | Global Interactivity | BaseBlock Refactoring]
        :relates-to:
          - motivated_by: "Architectural Conclusion: Decouple block instantiation from state registration to solve chicken-and-egg problem with DashboardPage"
          - implements: "interface: 'BaseBlock'"
          - uses: ["interface: 'BaseDataSource'", "class: 'StateManager'"]

        :rationale: "Registration logic was moved from __init__ to a separate method to allow DashboardPage to inject the StateManager post-instantiation."
        :contract:
          - pre: "A unique block_id and a valid datasource must be provided."
          - post: "The block is ready for state registration and layout rendering."

    """

    def __init__(self, block_id: str, datasource: BaseDataSource, **kwargs):
        """
        Initializes the BaseBlock.

        Args:
            block_id: A unique identifier for this block instance.
            datasource: An instance of a class that implements the BaseDataSource interface.

        """
        if not isinstance(block_id, str) or not block_id:
            raise ValueError("block_id must be a non-empty string.")
        if not isinstance(datasource, BaseDataSource):
            raise TypeError("datasource must be an instance of BaseDataSource.")

        self.block_id = block_id
        self.datasource = datasource
        self.publishes: Optional[List[Dict[str, str]]] = kwargs.get("publishes")
        self.subscribes: Optional[Dict[str, Callable]] = kwargs.get("subscribes")

    def _register_state_interactions(self, state_manager: StateManager):
        """
        Registers the block's publications and subscriptions with the StateManager.
        This method is called by the DashboardPage after it has created the StateManager.

        Args:
            state_manager: The application's state manager instance.

        """
        # Register as a publisher
        if self.publishes:
            for pub_info in self.publishes:
                state_id = pub_info['state_id']
                component_prop = pub_info['component_prop']
                publisher_component_id = self._generate_id(state_id.split('-')[-1])
                state_manager.register_publisher(state_id, publisher_component_id, component_prop)

        # Register as a subscriber
        if self.subscribes:
            for state_id, callback_fn in self.subscribes.items():
                subscriber_component_id = self._generate_id("container")
                subscriber_component_prop = 'children'
                state_manager.register_subscriber(
                    state_id,
                    subscriber_component_id,
                    subscriber_component_prop,
                    callback_fn
                )

    def _generate_id(self, component_name: str) -> str:
        """
        Generates a unique ID for a component within the block.

        """
        return f"{self.block_id}-{component_name}"

    @abstractmethod
    def layout(self) -> Component:
        """
        Returns the Dash component layout for the block.

        """
        pass

    def register_callbacks(self, app: Any):
        """
        This method's role is now handled by the StateManager.

        """
        pass
