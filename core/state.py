"""
This module defines the StateManager for handling interactivity between blocks.

"""
from typing import Dict, List, Any, Callable

class StateManager:
    """
    Manages the state dependencies and generates callbacks for a dashboard page.

    This class acts as a central registry for components that provide state (publishers)
    and components that consume state (subscribers). It builds a dependency graph
    and will be responsible for generating the necessary Dash callbacks to link them.

        :hierarchy: [Feature | Global Interactivity | StateManager Design]
        :relates-to:
          - motivated_by: "Architectural Conclusion: Decouple state management from UI components using a Pub/Sub model"
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
        self.dependency_graph: Dict[str, Dict[str, Any]] = {}

    def register_publisher(self, state_id: str, component_id: str, component_prop: str):
        """
        Registers a component property as a provider of a certain state.

        Args:
            state_id: The unique identifier for the state (e.g., 'selected_date_range').
            component_id: The ID of the Dash component that publishes the state.
            component_prop: The property of the component that holds the state (e.g., 'value').

        """
        if state_id not in self.dependency_graph:
            self.dependency_graph[state_id] = {'subscribers': []}
        
        self.dependency_graph[state_id]['publisher'] = {
            'component_id': component_id,
            'component_prop': component_prop
        }

    def register_subscriber(self, state_id: str, component_id: str, component_prop: str, callback_fn: Callable):
        """
        Registers a component property as a consumer of a certain state.

        Args:
            state_id: The unique identifier for the state to subscribe to.
            component_id: The ID of the Dash component that consumes the state.
            component_prop: The property of the component to be updated (e.g., 'figure').
            callback_fn: The function to call to generate the new property value.

        """
        if state_id not in self.dependency_graph:
            raise KeyError(f"State '{state_id}' has no publisher. A publisher must be registered first.")
            
        self.dependency_graph[state_id]['subscribers'].append({
            'component_id': component_id,
            'component_prop': component_prop,
            'callback_fn': callback_fn
        })

    def generate_callbacks(self, app: Any):
        """
        Traverses the dependency graph and registers all necessary callbacks with the Dash app.

        Args:
            app: The Dash app instance.

        """
        from dash import Input, Output

        for state_id, connections in self.dependency_graph.items():
            publisher = connections.get('publisher')
            subscribers = connections.get('subscribers')

            if not publisher or not subscribers:
                continue

            outputs = [
                Output(sub['component_id'], sub['component_prop'])
                for sub in subscribers
            ]
            inputs = [Input(publisher['component_id'], publisher['component_prop'])]

            # Use the factory to create a unique callback function for this state
            callback_func = self._create_callback_wrapper(subscribers)

            # Dynamically register the callback with Dash
            app.callback(outputs, inputs)(callback_func)

    def _create_callback_wrapper(self, subscribers: List[Dict[str, Any]]) -> Callable:
        """
        A factory that creates a unique callback function for a list of subscribers.
        This approach is used to correctly handle closures in a loop.

        Args:
            subscribers: A list of subscriber dictionaries for a specific state.

        Returns:
            A new function that can be registered as a Dash callback.

        """
        def callback_wrapper(value: Any) -> tuple:
            """
            The actual function that Dash will execute when the state changes.
            It calls the original callback_fn for each subscriber.

            """
            # If there's only one output, Dash expects a single value, not a tuple
            if len(subscribers) == 1:
                return subscribers[0]['callback_fn'](value)
            
            # Otherwise, return a tuple of results
            return tuple(sub['callback_fn'](value) for sub in subscribers)

        return callback_wrapper
