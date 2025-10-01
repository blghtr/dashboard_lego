"""
This module defines the StateManager for handling interactivity between blocks.

"""

from typing import Any, Callable, Dict, List

from dashboard_lego.utils.exceptions import StateError
from dashboard_lego.utils.logger import get_logger


class StateManager:
    """
    Manages the state dependencies and generates callbacks for a
    dashboard page.

    This class acts as a central registry for components that provide
    state (publishers) and components that consume state (subscribers).
    It builds a dependency graph and will be responsible for generating
    the necessary Dash callbacks to link them.

        :hierarchy: [Feature | Global Interactivity | StateManager Design]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Decouple state
           management from UI components using a Pub/Sub model"
         - implements: "class: 'StateManager'"
         - uses: []

        :rationale: "Chosen a graph-like dictionary structure to store
         state dependencies. This provides a good balance of
         implementation simplicity and ease of traversal for callback
         generation."
        :contract:
         - pre: "All state IDs must be unique across the application."
         - post: "The manager holds a complete dependency graph of the
          page's interactive components."

    """

    def __init__(self):
        """
        Initializes the StateManager.

        The internal `dependency_graph` will store the relationships.
        Example:
        {
            'selected_date_range': {
                'publisher': {
                    'component_id': 'global-date-picker',
                    'component_prop': 'value'
                },
                'subscribers': [
                    {
                        'component_id': 'sales-trend-graph',
                        'component_prop': 'figure',
                        'callback_fn': <function_ref>
                    },
                    {
                        'component_id': 'kpi-block-container',
                        'component_prop': 'children',
                        'callback_fn': <function_ref>
                    }
                ]
            }
        }

        """
        self.logger = get_logger(__name__, StateManager)
        self.logger.info("Initializing StateManager")
        self.dependency_graph: Dict[str, Dict[str, Any]] = {}

    def register_publisher(self, state_id: str, component_id: str, component_prop: str):
        """
        Registers a component property as a provider of a certain state.

        Args:
            state_id: The unique identifier for the state
                     (e.g., 'selected_date_range').
            component_id: The ID of the Dash component that publishes
                         the state.
            component_prop: The property of the component that holds the state
                           (e.g., 'value').

        """
        self.logger.debug(
            f"Registering publisher: state_id={state_id}, "
            f"component_id={component_id}, prop={component_prop}"
        )

        if state_id not in self.dependency_graph:
            self.dependency_graph[state_id] = {"subscribers": []}

        self.dependency_graph[state_id]["publisher"] = {
            "component_id": component_id,
            "component_prop": component_prop,
        }

        self.logger.info(f"Publisher registered for state: {state_id}")

    def register_subscriber(
        self,
        state_id: str,
        component_id: str,
        component_prop: str,
        callback_fn: Callable,
    ):
        """
        Registers a component property as a consumer of a certain state.

        Args:
            state_id: The unique identifier for the state to subscribe to.
            component_id: The ID of the Dash component that consumes
                         the state.
            component_prop: The property of the component to be updated
                           (e.g., 'figure').
            callback_fn: The function to call to generate the new property
                         value.

        """
        self.logger.debug(
            f"Registering subscriber: state_id={state_id}, "
            f"component_id={component_id}, prop={component_prop}"
        )

        # Auto-create dummy state if it doesn't exist (for static dashboards)
        if state_id not in self.dependency_graph:
            self.dependency_graph[state_id] = {
                "publisher": None,
                "publisher_prop": None,
                "subscribers": [],
            }
            self.logger.debug(f"Created new state entry for: {state_id}")

        self.dependency_graph[state_id]["subscribers"].append(
            {
                "component_id": component_id,
                "component_prop": component_prop,
                "callback_fn": callback_fn,
            }
        )

        self.logger.info(
            f"Subscriber registered for state: {state_id} "
            f"(total subscribers: "
            f"{len(self.dependency_graph[state_id]['subscribers'])})"
        )

    def generate_callbacks(self, app: Any):
        """
        Traverses the dependency graph and registers all necessary callbacks
        with the Dash app.

        Args:
            app: The Dash app instance.

        """
        from dash import Input, Output

        self.logger.info("Generating callbacks from dependency graph")
        callback_count = 0

        try:
            for state_id, connections in self.dependency_graph.items():
                publisher = connections.get("publisher")
                subscribers = connections.get("subscribers")

                if not publisher or not subscribers:
                    self.logger.debug(
                        f"Skipping state {state_id}: missing publisher or "
                        f"subscribers (publisher={bool(publisher)}, "
                        f"subscribers="
                        f"{len(subscribers) if subscribers else 0})"
                    )
                    continue

                self.logger.debug(
                    f"Creating callback for state: {state_id} "
                    f"({len(subscribers)} subscribers)"
                )

                outputs = [
                    Output(sub["component_id"], sub["component_prop"])
                    for sub in subscribers
                ]
                inputs = [Input(publisher["component_id"], publisher["component_prop"])]

                # Use the factory to create a unique callback function
                # for this state
                callback_func = self._create_callback_wrapper(subscribers)

                # Dynamically register the callback with Dash
                app.callback(outputs, inputs)(callback_func)
                callback_count += 1

            self.logger.info(f"Successfully registered {callback_count} callbacks")

        except Exception as e:
            self.logger.error(f"Error generating callbacks: {e}", exc_info=True)
            raise StateError(f"Failed to generate callbacks: {e}") from e

    def bind_callbacks(self, app: Any, blocks: List[Any]):
        """
        Registers one callback per block instead of per state.

        :hierarchy: [Architecture | Block-centric Callbacks | StateManager]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Block-centric callbacks improve
           performance and maintainability by reducing callback complexity"
         - implements: "method: 'bind_callbacks'"
         - uses: ["method: 'output_target'", "method: 'list_control_inputs'"]

        :rationale: "Each block gets exactly one callback that updates its output target."
        :contract:
         - pre: "Blocks must have output_target() and list_control_inputs() methods."
         - post: "Each block has exactly one callback registered with Dash."

        Args:
            app: The Dash app instance.
            blocks: List of blocks to register callbacks for.
        """
        from dash import Input, Output

        self.logger.info("Binding block-centric callbacks")
        callback_count = 0

        try:
            # Validate for duplicate outputs at compile time
            self._validate_no_duplicate_outputs(blocks)

            for block in blocks:
                # Get the block's output target
                output_id, output_prop = block.output_target()

                # Get all control inputs for this block
                inputs = block.list_control_inputs()

                if not inputs:
                    self.logger.debug(
                        f"Block {block.block_id} has no control inputs, skipping callback"
                    )
                    continue

                self.logger.debug(
                    f"Creating callback for block: {block.block_id} "
                    f"({len(inputs)} inputs -> {output_id}.{output_prop})"
                )

                # Create Input objects
                input_objects = [
                    Input(component_id, prop) for component_id, prop in inputs
                ]

                # Create Output object
                output_object = Output(output_id, output_prop)

                # Create callback function
                def create_block_callback(block_ref):
                    def block_callback(*values):
                        # Convert input values to control values dict
                        control_values = {}
                        for i, (component_id, prop) in enumerate(
                            block_ref.list_control_inputs()
                        ):
                            # Extract control name from component_id (last part after -)
                            control_name = component_id.split("-")[-1]
                            control_values[control_name] = values[i]

                        # Call the block's update method
                        return block_ref.update_from_controls(control_values)

                    return block_callback

                # Register the callback
                app.callback(output_object, input_objects)(create_block_callback(block))
                callback_count += 1

            self.logger.info(
                f"Successfully registered {callback_count} block callbacks"
            )

        except Exception as e:
            self.logger.error(f"Error binding block callbacks: {e}", exc_info=True)
            raise StateError(f"Failed to bind block callbacks: {e}") from e

    def _validate_no_duplicate_outputs(self, blocks: List[Any]):
        """
        Validates that no blocks have duplicate output targets.

        :hierarchy: [Architecture | Validation | StateManager]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Prevent callback conflicts by
           ensuring unique output targets across all blocks"
         - implements: "method: '_validate_no_duplicate_outputs'"
         - uses: ["method: 'output_target'"]

        :rationale: "Prevents Dash errors about duplicate Outputs at compile time."
        :contract:
         - pre: "Blocks must have output_target() method."
         - post: "Raises StateError if duplicate outputs are found."

        Args:
            blocks: List of blocks to validate.

        Raises:
            StateError: If duplicate output targets are found.
        """
        output_targets = {}

        for block in blocks:
            try:
                output_id, output_prop = block.output_target()
                output_key = (output_id, output_prop)

                if output_key in output_targets:
                    existing_block = output_targets[output_key]
                    raise StateError(
                        f"Duplicate output target detected: {output_id}.{output_prop} "
                        f"is used by both blocks '{existing_block.block_id}' and '{block.block_id}'. "
                        f"Each block must have a unique output target."
                    )

                output_targets[output_key] = block

            except AttributeError as e:
                raise StateError(
                    f"Block '{block.block_id}' does not have required output_target() method: {e}"
                ) from e

        self.logger.debug(
            f"Output validation passed: {len(output_targets)} unique targets"
        )

    def _create_callback_wrapper(self, subscribers: List[Dict[str, Any]]) -> Callable:
        """
        A factory that creates a unique callback function for a list
        of subscribers. This approach is used to correctly handle
        closures in a loop.

        Args:
            subscribers: A list of subscriber dictionaries for a
                         specific state.

        Returns:
            A new function that can be registered as a Dash callback.

        """

        def callback_wrapper(value: Any) -> tuple:
            """
            The actual function that Dash will execute when the state changes.
            It calls the original callback_fn for each subscriber.

            """
            self.logger.debug(
                f"Callback triggered with value: {value} "
                f"for {len(subscribers)} subscribers"
            )

            try:
                # If there's only one output, Dash expects a single value,
                # not a tuple
                if len(subscribers) == 1:
                    result = subscribers[0]["callback_fn"](value)
                    self.logger.debug("Single subscriber callback completed")
                    return result

                # Otherwise, return a tuple of results
                results = tuple(sub["callback_fn"](value) for sub in subscribers)
                self.logger.debug(
                    f"Multi-subscriber callback completed: " f"{len(results)} results"
                )
                return results

            except Exception as e:
                self.logger.error(f"Error in callback execution: {e}", exc_info=True)
                # Return empty results to prevent Dash crashes
                if len(subscribers) == 1:
                    return None
                return tuple(None for _ in subscribers)

        return callback_wrapper
