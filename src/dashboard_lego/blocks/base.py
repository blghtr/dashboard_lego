"""
This module defines the abstract base class for all dashboard blocks.

"""

import asyncio
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional, Union

import pandas as pd
import plotly.graph_objects as go
from dash.development.base_component import Component

from dashboard_lego.core.async_api import AsyncDataSource

# Use forward references for type hints to avoid circular imports
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.core.exceptions import BlockError, ConfigurationError
from dashboard_lego.core.state import StateManager
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
         - uses: ["interface: 'DataSource'", "class: 'StateManager'"]

        :rationale: "Registration logic was moved from __init__ to a
         separate method to allow DashboardPage to inject the
         StateManager post-instantiation."
        :contract:
         - pre: "A unique block_id and a valid datasource must be provided."
         - post: "The block is ready for state registration and layout
           rendering."

    """

    def __init__(self, block_id: str, datasource: DataSource, **kwargs):
        """
        Initializes the BaseBlock.

        Args:
            block_id: A unique identifier for this block instance.
            datasource: An instance of a class that implements the
                       DataSource interface.
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
        if not isinstance(datasource, DataSource):
            error_msg = "datasource must be an instance of DataSource."
            self.logger.error(error_msg)
            raise ConfigurationError(error_msg)

        self.block_id = block_id
        self.datasource = datasource
        self.publishes: List[Dict[str, str]] = kwargs.get("publishes") or []
        self.subscribes: Dict[str, Callable] = kwargs.get("subscribes") or {}
        # Don't override controls if already set by subclass
        if not hasattr(self, "controls"):
            self.controls: Dict = {}
        self.allow_duplicate_output: bool = kwargs.get("allow_duplicate_output", False)

        # Navigation context for pattern matching callbacks
        self.navigation_mode: bool = kwargs.get("navigation_mode", False)
        self.section_index: Optional[int] = kwargs.get("section_index", None)

        # Sidebar context for fixed ID generation
        self.is_sidebar_block: bool = kwargs.get("is_sidebar_block", False)

        # Theme configuration - will be set by DashboardPage
        self.theme_config: Optional["ThemeConfig"] = None

        # <semantic_block: block_transform>
        # Block-specific data transformation
        # If a transform function is provided, create a specialized datasource clone for this block
        self.transform_fn: Optional[Callable] = kwargs.get("transform_fn")
        if self.transform_fn:
            self.logger.info(
                f"[BaseBlock|Init] Block {block_id} has transform_fn, creating specialized datasource"
            )
            self.datasource = self.datasource.with_transform_fn(self.transform_fn)
            self.logger.debug(
                f"[BaseBlock|Init] Specialized datasource created for {block_id}"
            )
        # </semantic_block: block_transform>

        self.logger.debug(
            f"Block initialized: publishes={bool(self.publishes)}, "
            f"subscribes={bool(self.subscribes)}, "
            f"allow_duplicate_output={self.allow_duplicate_output}, "
            f"has_transform={bool(self.transform_fn)}"
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
                        state_id,
                        publisher_component_id,
                        component_prop,
                        dep_param_name=pub_info.get("dep_param_name"),
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

    def set_initial_external_values(self, initial_values: Dict[str, Any]) -> None:
        """
        Receive initial values for externally subscribed states.

        Called by DashboardPage before layout() to provide initial state values.

        :hierarchy: [Feature | Initial State Sync | BaseBlock]
        :relates-to:
         - motivated_by: "Blocks need initial external state values before rendering"
         - implements: "method: 'set_initial_external_values'"

        :contract:
         - pre: "initial_values contains {state_id: value} for external states"
         - post: "Block has initial external state values available for layout()"

        Args:
            initial_values: Dict mapping state_id to initial value
        """
        self.logger.debug(
            f"Received initial values for {self.block_id}: "
            f"{list(initial_values.keys())}"
        )
        self._initial_external_values = initial_values

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
            self.logger.debug(f"Applied theme style: {component_type}.{element}")
        else:
            base_style = {}
            self.logger.debug(
                f"Theme not available for {component_type}.{element}, "
                f"using fallback"
            )

        # Merge with user overrides (overrides take precedence)
        if overrides:
            merged_style = {**base_style, **overrides}
            self.logger.debug(
                f"Applied themed style for {component_type}.{element} with {len(overrides)} overrides"
            )
            return merged_style

        return base_style

    def _generate_id(self, component_name: str) -> Union[str, Dict[str, Any]]:
        """
        Generates a unique ID for a component within the block.

        For sidebar blocks: returns fixed string ID (no section dict).
        For navigation mode: returns dict ID for pattern matching.
        For standard mode: returns simple string ID.

        :hierarchy: [Blocks | Base | ID Generation]
        :relates-to:
         - motivated_by: "Fix lazy-loaded section callbacks using Dash pattern matching"
         - motivated_by: "Sidebar blocks need fixed IDs for cross-section State() subscriptions"
         - implements: "method: '_generate_id' with sidebar + pattern matching support"

        :contract:
         - pre: "component_name is valid string"
         - post: "Returns ID appropriate for block context"
         - invariant: "Sidebar blocks ALWAYS get fixed string IDs"

        Returns:
            str: Fixed ID for sidebar blocks (e.g., "block_id-component")
            str: Simple ID for standard blocks (e.g., "block_id-component")
            Dict: Pattern-matching ID for navigation blocks (e.g., {'section': 0, 'type': 'block_id-component'})
        """
        # <semantic_block: sidebar_fixed_id>
        # CRITICAL: Sidebar blocks MUST use fixed string IDs
        # This enables cross-section State() subscriptions in pattern-matching callbacks
        if self.is_sidebar_block:
            component_id = f"{self.block_id}-{component_name}"
            self.logger.debug(
                f"[Sidebar|FixedID] Generated fixed component ID: {component_id}"
            )
            return component_id
        # </semantic_block: sidebar_fixed_id>

        # <semantic_block: navigation_pattern_matching>
        if self.navigation_mode and self.section_index is not None:
            # CRITICAL: Key order must match HTML rendering order
            # Dash/React renders as {"section": N, "type": "..."}
            component_id = {
                "section": self.section_index,
                "type": f"{self.block_id}-{component_name}",
            }
            self.logger.debug(
                f"Generated pattern-matching component ID: {component_id}"
            )
            return component_id
        # </semantic_block: navigation_pattern_matching>

        # <semantic_block: standard_fixed_id>
        component_id = f"{self.block_id}-{component_name}"
        self.logger.debug(f"Generated component ID: {component_id}")
        return component_id
        # </semantic_block: standard_fixed_id>

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

        CRITICAL: Passes control_values dict directly to callback, NOT as **kwargs.
        Python doesn't allow dict objects as keyword argument names.

        :hierarchy: [Architecture | Block-centric Callbacks | BaseBlock]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Block-centric callbacks improve
           performance and maintainability by reducing callback complexity"
         - implements: "method: 'update_from_controls'"
         - uses: ["attribute: 'subscribes'"]

        :contract:
         - pre: "Block has at least one subscription callback"
         - post: "Returns result of subscription callback"
         - spec_compliance: "Passes control_values as single dict argument"

        :complexity: 3
        :decision_cache: "Find callback matching changed states instead of using first one"

        Args:
            control_values: Dictionary of control name -> value mappings (e.g. {'x_col': 'Price'})

        Returns:
            The result of the subscription callback
        """
        if not self.subscribes and not self.controls:
            return None

        # Find callback that matches one of the changed states
        # If multiple states changed, use any matching callback (they should be equivalent)
        callback_fn = None
        for state_name in control_values.keys():
            if state_name in self.subscribes:
                callback_fn = self.subscribes[state_name]
                break

        # Fallback to first callback if no exact match found
        if callback_fn is None:
            callback_fn = next(iter(self.subscribes.values()))

        # CRITICAL: Pass control_values dict directly, not as **kwargs
        # TypedChartBlock callbacks expect: callback(control_values_dict)
        return callback_fn(control_values)

    @abstractmethod
    def layout(self) -> Component:
        """
        Returns the Dash component layout for the block.

        """
        self.logger.debug(f"Rendering layout for block {self.block_id}")
        pass

    def get_figure(
        self, params: Optional[Dict[str, Any]] = None
    ) -> Optional[go.Figure]:
        """
        Export standalone Plotly figure (chart blocks only).

        Returns:
            Plotly Figure for chart blocks, None for non-chart blocks.
        """
        return None  # Default implementation for non-chart blocks

    def register_callbacks(self, app: Any):
        """
        This method's role is now handled by the StateManager.

        """
        pass

    def _get_data_sync(self, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Get data from datasource, handling both sync and async datasources.

        For AsyncDataSource, runs async method in sync context using asyncio.run().
        For DataSource, calls sync method directly.

        :hierarchy: [Blocks | Base | DataAccess]
        :relates-to:
         - motivated_by: "Support both sync and async datasources in blocks"
         - implements: "method: '_get_data_sync'"

        :contract:
         - pre: "datasource is DataSource or AsyncDataSource instance"
         - post: "Returns DataFrame synchronously (async datasource wrapped)"

        Args:
            params: Parameters for data retrieval

        Returns:
            DataFrame from datasource
        """
        if isinstance(self.datasource, AsyncDataSource):
            # Async datasource - run in sync context
            self.logger.debug(
                "[BaseBlock|_GetDataSync] Using AsyncDataSource, running async method"
            )
            try:
                # Check if there's already an event loop running
                asyncio.get_running_loop()
                # If we're in an async context (event loop running), we can't use asyncio.run()
                # This shouldn't happen in Dash callbacks (they're sync), but handle gracefully
                self.logger.warning(
                    "[BaseBlock|_GetDataSync] Event loop already running, "
                    "this should not happen in Dash callbacks. Using executor."
                )
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        asyncio.run,
                        self.datasource.get_processed_data_async(params or {}),
                    )
                    return future.result()
            except RuntimeError:
                # No event loop running, safe to use asyncio.run()
                # This is the normal case for Dash callbacks (sync context)
                return asyncio.run(
                    self.datasource.get_processed_data_async(params or {})
                )
        else:
            # Sync datasource - call directly
            self.logger.debug("[BaseBlock|_GetDataSync] Using sync DataSource")
            return self.datasource.get_processed_data(params)
