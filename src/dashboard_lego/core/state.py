"""
This module defines the StateManager for handling interactivity between blocks.

"""

from typing import Any, Callable, Dict, List, Union

from dash.dependencies import MATCH, Input, Output, State

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
        # Track registered outputs for idempotency (navigation lazy-loading support)
        self._registered_outputs = set()  # Set of (component_id, component_prop) tuples

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

    @staticmethod
    def _make_hashable_key(component_id: Union[str, Dict], component_prop: str):
        """
        Convert component ID (string or dict) to hashable tuple for dict keys.

        :hierarchy: [Core | StateManager | Helper]
        :relates-to:
         - motivated_by: "Pattern matching IDs (dicts) cannot be dict keys"

        Args:
            component_id: String ID or pattern matching dict ID
            component_prop: Component property name

        Returns:
            Hashable tuple representation of the ID
        """
        if isinstance(component_id, dict):
            # Convert dict to sorted tuple of items for hashability
            id_tuple = tuple(sorted(component_id.items()))
            return (id_tuple, component_prop)
        return (component_id, component_prop)

    def generate_callbacks(self, app: Any, blocks: List[Any] = None):
        """
        Traverses the dependency graph and registers all necessary callbacks
        with the Dash app.

        Args:
            app: Dash app instance
            blocks: List of blocks (to check for controls)

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
        self.logger.info("Generating callbacks from dependency graph")
        callback_count = 0

        # Build block lookup by output target
        blocks_by_output = {}
        if blocks:
            for block in blocks:
                output_id, output_prop = block.output_target()
                output_key = self._make_hashable_key(output_id, output_prop)
                blocks_by_output[output_key] = block

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
                    output_key = self._make_hashable_key(
                        sub["component_id"], sub["component_prop"]
                    )

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
                # Decode hashable key back to component_id and prop
                if isinstance(output_key[0], tuple):
                    # Was a dict ID, reconstruct it
                    component_id = dict(output_key[0])
                    component_prop = output_key[1]
                else:
                    # Was a string ID
                    component_id, component_prop = output_key

                # CRITICAL: Skip blocks with controls - they will be handled by bind_callbacks
                # with combined Input(exact session controls) + Input(MATCH own controls)
                block = blocks_by_output.get(output_key)
                if block and block.list_control_inputs():
                    self.logger.debug(
                        f"⏭️  Block {block.block_id} has controls - "
                        f"will use combined callback (state-centric skipped)"
                    )
                    continue

                # NEW: Skip if already registered (idempotency for navigation lazy-loading)
                if output_key in self._registered_outputs:
                    self.logger.debug(
                        f"⏭️  Callback for {component_id}.{component_prop} already registered, skipping"
                    )
                    continue

                self.logger.info(
                    f"🔧 Creating callback for output: {component_id}.{component_prop} "
                    f"with {len(state_infos)} input state(s)"
                )

                # Create Input for each state this output subscribes to
                inputs = []
                for info in state_infos:
                    pub_id = info["publisher"]["component_id"]
                    # CRITICAL: Keep publisher IDs EXACT (no MATCH conversion)
                    # This allows cross-section subscriptions (section 0 → section 1+)
                    # Dash supports: Input(exact_id) → Output(MATCH_id)
                    inputs.append(Input(pub_id, info["publisher"]["component_prop"]))

                # Debug: log all inputs for this callback
                for idx, (input_obj, state_info) in enumerate(zip(inputs, state_infos)):
                    self.logger.debug(
                        f"  📥 Input[{idx}]: {input_obj.component_id}.{input_obj.component_property} "
                        f"(state_id: {state_info['state_id']})"
                    )

                # Create single Output for this subscriber
                # Pattern matching: replace section index with MATCH for dict IDs
                # CRITICAL: Maintain key order (section first, then type)
                output_id = component_id
                if isinstance(output_id, dict):
                    output_id = {"section": MATCH, "type": component_id.get("type")}

                output = Output(output_id, component_prop)
                self.logger.debug(
                    f"  📤 Output: {output.component_id}.{output.component_property}"
                )

                # Create callback that handles multiple inputs
                callback_func = self._create_multi_input_callback(state_infos)

                # Register callback with Dash
                # CRITICAL: State-centric callbacks should NOT use prevent_initial_call
                # (they need to trigger on session control changes)
                self.logger.debug("  🔗 Registering callback with Dash...")
                app.callback(output, inputs)(callback_func)
                callback_count += 1

                # Track this output as registered
                self._registered_outputs.add(output_key)

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
        self.logger.info("Binding block-centric callbacks")
        callback_count = 0

        try:
            # Validate for duplicate outputs at compile time with enhanced error handling
            self._validate_no_duplicate_outputs(blocks)

            for block in blocks:
                # Get the block's output target
                output_id, output_prop = block.output_target()
                output_key = self._make_hashable_key(output_id, output_prop)

                # Get own control inputs for this block
                own_controls = block.list_control_inputs()

                if not own_controls:
                    self.logger.debug(
                        f"⏭️  Block {block.block_id} has no control inputs, skipping callback"
                    )
                    continue

                # CRITICAL: Collect BOTH external states AND own controls for combined callback
                # External states use EXACT IDs (from section 0)
                # Own controls use MATCH IDs (within block's section)
                # Dash SUPPORTS mixing exact Input IDs with MATCH Input IDs!

                external_state_inputs = []
                for state_id, connections in self.dependency_graph.items():
                    subscribers = connections.get("subscribers", [])
                    for sub in subscribers:
                        sub_output_key = self._make_hashable_key(
                            sub["component_id"], sub["component_prop"]
                        )
                        if sub_output_key == output_key:
                            publisher = connections.get("publisher")
                            if publisher:
                                # Use EXACT publisher ID (no MATCH conversion)
                                external_state_inputs.append(
                                    (
                                        state_id,
                                        publisher["component_id"],
                                        publisher["component_prop"],
                                    )
                                )

                own_control_inputs = own_controls

                input_count_desc = (
                    f"{len(external_state_inputs)} external + {len(own_controls)} own"
                    if external_state_inputs
                    else f"{len(own_controls)} own"
                )
                self.logger.info(
                    f"🔧 Creating combined callback for: {block.block_id} "
                    f"({input_count_desc} inputs -> {output_id}.{output_prop})"
                )

                # Create Input/State objects
                # CRITICAL: External states must be State() not Input()
                # because they have EXACT IDs from other sections
                input_objects = []
                state_objects = []

                # 1. Add external states as State() (cross-section, read-only)
                for state_id, pub_component_id, pub_prop in external_state_inputs:
                    state_objects.append(State(pub_component_id, pub_prop))
                    self.logger.debug(
                        f"  🔍 External State[{len(state_objects)-1}]: {pub_component_id}.{pub_prop} "
                        f"(state_id: {state_id}, EXACT ID, read-only)"
                    )

                # 2. Add own control inputs with MATCH pattern
                for component_id, prop in own_control_inputs:
                    original_id = component_id
                    # Pattern matching: convert string IDs to dict IDs for navigation mode
                    # CRITICAL: Key order MUST match HTML rendering: section first, then type
                    if block.navigation_mode and isinstance(component_id, str):
                        component_id = {"section": MATCH, "type": component_id}
                    elif isinstance(component_id, dict):
                        # Rebuild dict with correct key order
                        component_id = {
                            "section": MATCH,
                            "type": component_id.get("type"),
                        }
                    input_objects.append(Input(component_id, prop))

                    # Debug: log transformation
                    self.logger.debug(
                        f"  📥 Own Control Input[{len(input_objects)-1}]: {original_id} → {component_id}.{prop}"
                    )

                # Create Output object with allow_duplicate and pattern matching support
                allow_duplicate = getattr(block, "allow_duplicate_output", False)
                # Pattern matching: replace section index with MATCH for dict IDs
                # CRITICAL: Maintain correct key order (section first, then type)
                output_id_pm = output_id
                if isinstance(output_id_pm, dict):
                    output_id_pm = {
                        "section": MATCH,
                        "type": output_id_pm.get("type", output_id_pm.get("type")),
                    }
                output_object = Output(
                    output_id_pm, output_prop, allow_duplicate=allow_duplicate
                )
                self.logger.debug(
                    f"  📤 Output: {output_id_pm}.{output_prop} "
                    f"(allow_duplicate={allow_duplicate})"
                )

                # Create callback function with enhanced error handling
                def create_block_callback(block_ref, ext_states_count, ext_states_list):
                    def block_callback(*args):
                        try:
                            # CRITICAL: Dash passes Input values first, then State values
                            # Our callback signature: *inputs, *states
                            own_control_count = len(block_ref.list_control_inputs())
                            own_control_values = args[:own_control_count]
                            external_values = args[own_control_count:]

                            self.logger.debug(
                                f"🎬 Block callback triggered for {block_ref.block_id} "
                                f"with {len(args)} values ({len(own_control_values)} own Input + {len(external_values)} external State)"
                            )

                            # Build control_values dict
                            control_values = {}

                            # 1. Add own control values (from Input objects)
                            for i, (component_id, prop) in enumerate(
                                block_ref.list_control_inputs()
                            ):
                                # Extract control name from component_id (last part after -)
                                # Handle both string IDs and pattern matching dict IDs
                                if isinstance(component_id, dict):
                                    id_str = component_id["type"]
                                else:
                                    id_str = component_id
                                control_name = id_str.split("-")[-1]
                                control_values[control_name] = own_control_values[i]
                                self.logger.debug(
                                    f"  🎛️  Own control {control_name} = {own_control_values[i]} "
                                    f"(from Input {component_id}.{prop})"
                                )

                            # 2. Add external state values (from State objects)
                            for i, (state_id, _, _) in enumerate(ext_states_list):
                                control_values[state_id] = external_values[i]
                                self.logger.debug(
                                    f"  🌐 External state {state_id} = {external_values[i]} "
                                    f"(from State, cross-section)"
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
                    self.logger.debug(
                        f"🔗 Registering combined callback with Dash "
                        f"({len(state_objects)} external State(EXACT) + {len(input_objects)} own Input(MATCH))..."
                    )

                    # CRITICAL: Pass state_objects + input_objects to callback
                    # State objects come first, then Input objects
                    app.callback(output_object, input_objects, state_objects)(
                        create_block_callback(
                            block, len(external_state_inputs), external_state_inputs
                        )
                    )
                    callback_count += 1

                    # Track this output as registered
                    self._registered_outputs.add(output_key)

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
                output_key = self._make_hashable_key(output_id, output_prop)
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
