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

        :rationale: "Chosen a graph-like dictionary structure to store state dependencies. This provides a good balance of implementation simplicity and ease of traversal for callback generation."
        :contract:
         - pre: "All state IDs must be unique across the application."
         - post: "The manager holds a complete dependency graph of the page's interactive components."


    """

    def __init__(self):
        """
        Initializes the StateManager.

        The internal ``dependency_graph`` will store the relationships.

        Example::

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
                            'callback_fn': '<function_ref>'
                        },
                        {
                            'component_id': 'kpi-block-container',
                            'component_prop': 'children',
                            'callback_fn': '<function_ref>'
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

        This method now supports multi-state subscriptions by grouping
        subscribers by their output target and creating callbacks with
        multiple Input sources.

        :hierarchy: [Feature | Multi-State Subscription | StateManager]
        :relates-to:
         - motivated_by: "Bug Fix: Support subscribing to multiple states"
         - implements: "method: 'generate_callbacks' with multi-input support"

        :rationale: "Group subscriptions by output target to create one callback
         per subscriber with multiple inputs, avoiding duplicate output errors."
        :contract:
         - pre: "Dependency graph is populated with publishers and subscribers."
         - post: "One callback per unique output target with all its input states."

        Args:
            app: The Dash app instance.

        """
        from dash import Input, Output

        self.logger.info("Generating callbacks from dependency graph")
        callback_count = 0

        try:
            # Group subscriptions by output target (component_id, component_prop)
            # to support multi-state subscriptions
            output_subscriptions = {}  # {(comp_id, comp_prop): [state_info]}

            for state_id, connections in self.dependency_graph.items():
                publisher = connections.get("publisher")
                subscribers = connections.get("subscribers")

                if not publisher:
                    self.logger.debug(
                        f"Skipping state {state_id}: no publisher registered"
                    )
                    continue

                if not subscribers:
                    self.logger.debug(
                        f"Skipping state {state_id}: no subscribers registered"
                    )
                    continue

                # Add each subscriber to the grouped structure
                for sub in subscribers:
                    output_key = (sub["component_id"], sub["component_prop"])

                    if output_key not in output_subscriptions:
                        output_subscriptions[output_key] = []

                    output_subscriptions[output_key].append(
                        {
                            "state_id": state_id,
                            "publisher": publisher,
                            "callback_fn": sub["callback_fn"],
                        }
                    )

            # Create one callback per unique output target
            for output_key, state_infos in output_subscriptions.items():
                component_id, component_prop = output_key

                self.logger.info(
                    f"🔧 Creating callback for output: {component_id}.{component_prop} "
                    f"with {len(state_infos)} input state(s)"
                )

                # Create Input for each state this output subscribes to
                inputs = [
                    Input(
                        info["publisher"]["component_id"],
                        info["publisher"]["component_prop"],
                    )
                    for info in state_infos
                ]

                # Debug: log all inputs for this callback
                for idx, (input_obj, state_info) in enumerate(zip(inputs, state_infos)):
                    self.logger.debug(
                        f"  📥 Input[{idx}]: {input_obj.component_id}.{input_obj.component_property} "
                        f"(state_id: {state_info['state_id']})"
                    )

                # Create single Output for this subscriber
                output = Output(component_id, component_prop)
                self.logger.debug(
                    f"  📤 Output: {output.component_id}.{output.component_property}"
                )

                # Create callback that handles multiple inputs
                callback_func = self._create_multi_input_callback(state_infos)

                # Register callback with Dash
                self.logger.debug("  🔗 Registering callback with Dash...")
                app.callback(output, inputs)(callback_func)
                callback_count += 1

                self.logger.info(
                    f"✅ Registered callback #{callback_count}: {len(inputs)} inputs -> "
                    f"{component_id}.{component_prop}"
                )

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
            # Validate for duplicate outputs at compile time with enhanced error handling
            self._validate_no_duplicate_outputs(blocks)

            for block in blocks:
                # Get the block's output target
                output_id, output_prop = block.output_target()

                # Get all control inputs for this block
                inputs = block.list_control_inputs()

                if not inputs:
                    self.logger.debug(
                        f"⏭️  Block {block.block_id} has no control inputs, skipping callback"
                    )
                    continue

                self.logger.info(
                    f"🔧 Creating block-centric callback for: {block.block_id} "
                    f"({len(inputs)} inputs -> {output_id}.{output_prop})"
                )

                # Create Input objects
                input_objects = [
                    Input(component_id, prop) for component_id, prop in inputs
                ]

                # Debug: log all inputs for this block
                for idx, (comp_id, prop) in enumerate(inputs):
                    self.logger.debug(f"  📥 Input[{idx}]: {comp_id}.{prop}")

                # Create Output object with allow_duplicate support
                allow_duplicate = getattr(block, "allow_duplicate_output", False)
                output_object = Output(
                    output_id, output_prop, allow_duplicate=allow_duplicate
                )
                self.logger.debug(
                    f"  📤 Output: {output_id}.{output_prop} "
                    f"(allow_duplicate={allow_duplicate})"
                )

                # Create callback function with enhanced error handling
                def create_block_callback(block_ref):
                    def block_callback(*values):
                        try:
                            self.logger.debug(
                                f"🎬 Block callback triggered for {block_ref.block_id} "
                                f"with {len(values)} input values"
                            )

                            # Convert input values to control values dict
                            control_values = {}
                            for i, (component_id, prop) in enumerate(
                                block_ref.list_control_inputs()
                            ):
                                # Extract control name from component_id (last part after -)
                                control_name = component_id.split("-")[-1]
                                control_values[control_name] = values[i]
                                self.logger.debug(
                                    f"  🎛️  Control {control_name} = {values[i]} "
                                    f"(from {component_id}.{prop})"
                                )

                            # Call the block's update method
                            return block_ref.update_from_controls(control_values)
                        except Exception as e:
                            self.logger.error(
                                f"Error in callback for block {block_ref.block_id}: {e}",
                                exc_info=True,
                            )
                            # Return a safe fallback to prevent UI crashes
                            return self._get_fallback_output(block_ref)

                    return block_callback

                # Register the callback with enhanced error handling
                try:
                    self.logger.debug("🔗 Registering block callback with Dash...")
                    app.callback(output_object, input_objects)(
                        create_block_callback(block)
                    )
                    callback_count += 1
                    self.logger.info(
                        f"✅ Registered block callback #{callback_count} for: {block.block_id}"
                    )
                except Exception as callback_error:
                    self.logger.error(
                        f"Failed to register callback for block {block.block_id}: {callback_error}",
                        exc_info=True,
                    )
                    # Continue with other blocks instead of failing completely
                    continue

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
        duplicate_blocks = []

        for block in blocks:
            try:
                output_id, output_prop = block.output_target()
                output_key = (output_id, output_prop)
                allow_duplicate = getattr(block, "allow_duplicate_output", False)

                if output_key in output_targets:
                    existing_block = output_targets[output_key]
                    existing_allow_duplicate = getattr(
                        existing_block, "allow_duplicate_output", False
                    )

                    # Check if either block allows duplicates
                    if not (allow_duplicate or existing_allow_duplicate):
                        duplicate_blocks.append(
                            {
                                "output": f"{output_id}.{output_prop}",
                                "block1": existing_block.block_id,
                                "block2": block.block_id,
                                "allow_duplicate1": existing_allow_duplicate,
                                "allow_duplicate2": allow_duplicate,
                            }
                        )

                        self.logger.error(
                            f"Duplicate output target detected: {output_id}.{output_prop} "
                            f"is used by both blocks '{existing_block.block_id}' and '{block.block_id}'. "
                            f"Set allow_duplicate_output=True on one or both blocks to resolve this conflict."
                        )
                    else:
                        self.logger.warning(
                            f"Duplicate output target allowed: {output_id}.{output_prop} "
                            f"used by blocks '{existing_block.block_id}' and '{block.block_id}' "
                            f"(allow_duplicate_output=True)"
                        )

                output_targets[output_key] = block

            except AttributeError as e:
                raise StateError(
                    f"Block '{block.block_id}' does not have required output_target() method: {e}"
                ) from e

        # Raise error if there are unresolved duplicates
        if duplicate_blocks:
            error_msg = "Duplicate output targets detected:\n"
            for dup in duplicate_blocks:
                error_msg += f"  - {dup['output']}: blocks '{dup['block1']}' and '{dup['block2']}'\n"
            error_msg += "\nTo resolve this, set allow_duplicate_output=True on one or both blocks."
            raise StateError(error_msg)

        self.logger.debug(
            f"Output validation passed: {len(output_targets)} unique targets"
        )

    def _get_fallback_output(self, block: Any) -> Any:
        """
        Provides a safe fallback output when a callback fails.

        :hierarchy: [Architecture | Error Handling | StateManager]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Prevent UI crashes by providing
           safe fallbacks when callbacks fail"
         - implements: "method: '_get_fallback_output'"
         - uses: ["method: 'output_target'"]

        :rationale: "Returns appropriate fallback based on output type to prevent UI crashes."
        :contract:
         - pre: "Block has output_target() method."
         - post: "Returns a safe fallback value for the output type."

        Args:
            block: The block that failed.

        Returns:
            A safe fallback value appropriate for the output type.
        """
        try:
            output_id, output_prop = block.output_target()

            # Return appropriate fallback based on property type
            if output_prop == "figure":
                # For Plotly figures, return empty figure
                import plotly.graph_objects as go

                return go.Figure().update_layout(
                    title="Error loading chart",
                    annotations=[
                        dict(
                            text="An error occurred while loading this chart",
                            xref="paper",
                            yref="paper",
                            x=0.5,
                            y=0.5,
                            showarrow=False,
                            font=dict(size=16, color="red"),
                        )
                    ],
                )
            elif output_prop == "children":
                # For text/HTML content, return error message
                return "Error loading content"
            else:
                # Generic fallback
                return None

        except Exception as e:
            self.logger.error(f"Error creating fallback output: {e}", exc_info=True)
            return None

    def _create_multi_input_callback(
        self, state_infos: List[Dict[str, Any]]
    ) -> Callable:
        """
        Creates a callback function that handles multiple input states.

        :hierarchy: [Feature | Multi-State Subscription | Callback Creation]
        :relates-to:
         - motivated_by: "Bug Fix: Support blocks subscribing to multiple states"
         - implements: "method: '_create_multi_input_callback'"

        :rationale: "When a block subscribes to multiple states, the callback
         receives multiple input values and must call the block's update function."
        :contract:
         - pre: "state_infos contains callback_fn and state metadata for each input."
         - post: "Returns a function that processes all input values."

        Args:
            state_infos: List of dicts with 'state_id', 'publisher', 'callback_fn'.

        Returns:
            A callback function that accepts multiple input values.

        """

        def multi_input_callback(*values: Any) -> Any:
            """
            Callback that receives multiple input values from different states.

            Since all state_infos point to the same callback_fn (same subscriber),
            we just call it once with the first value that triggered the callback.

            """
            self.logger.info(
                f"🔔 Multi-input callback triggered with {len(values)} values"
            )
            self.logger.debug(f"Values: {values}")
            self.logger.debug(f"Value types: {[type(v) for v in values]}")

            # Log state_ids and values mapping for debugging
            state_mapping = {}
            for idx, info in enumerate(state_infos):
                if idx < len(values):
                    state_id = info["state_id"]
                    value = values[idx]
                    state_mapping[state_id] = value
                    self.logger.info(
                        f"🎯 State mapping: {state_id} = {value} (type: {type(value).__name__})"
                    )
                else:
                    self.logger.warning(f"⚠️ No value for state_id: {info['state_id']}")

            self.logger.info(f"📋 Complete state mapping: {state_mapping}")

            try:
                # All state_infos have the same callback_fn (same subscriber block)
                # Just call it with the first triggering value
                # Dash's callback context can be used if block needs to know which input triggered
                callback_fn = state_infos[0]["callback_fn"]
                self.logger.debug(f"📞 Calling callback_fn: {callback_fn.__name__}")
                result = callback_fn(*values)

                self.logger.info("✅ Multi-input callback completed successfully")
                return result

            except Exception as e:
                self.logger.error(
                    f"❌ Error in multi-input callback execution: {e}", exc_info=True
                )
                return None

        return multi_input_callback

    def _create_callback_wrapper(self, subscribers: List[Dict[str, Any]]) -> Callable:
        """
        A factory that creates a unique callback function for a list
        of subscribers. This approach is used to correctly handle
        closures in a loop.

        NOTE: This is the old method used when multiple subscribers react to
        one state. Now deprecated in favor of _create_multi_input_callback.

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
