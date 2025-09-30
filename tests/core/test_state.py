"""
Tests for the StateManager class.

"""
from unittest.mock import MagicMock, call
import pytest
from dash import Input, Output

from core.state import StateManager

@pytest.fixture
def state_manager() -> StateManager:
    """Returns a fresh StateManager instance for each test."""
    return StateManager()

@pytest.fixture
def mock_app() -> MagicMock:
    """Fixture to create a mock Dash app with a callback decorator."""
    app = MagicMock()
    # The decorator needs to return the function it decorates
    app.callback = MagicMock(return_value=lambda f: f)
    return app

class TestStateManager:
    """
    Test suite for the StateManager.

        :hierarchy: [Testing | Unit Tests | StateManager]
        :covers:
          - object: "class: StateManager"
          - requirement: "Architectural Conclusion: Decouple state management"

    """

    def test_register_publisher(self, state_manager: StateManager):
        """
            :scenario: Verifies that a publisher is correctly registered in the dependency graph.
            :strategy: Direct method call and assertion on the internal graph structure.
            :contract:
            :pre: A new state_id, component_id, and prop are provided.
            :post: The dependency_graph contains the new state with the correct publisher info.

        """
        state_manager.register_publisher(
            state_id='test_state',
            component_id='test_publisher',
            component_prop='value'
        )
        
        assert 'test_state' in state_manager.dependency_graph
        publisher_info = state_manager.dependency_graph['test_state']['publisher']
        assert publisher_info['component_id'] == 'test_publisher'
        assert publisher_info['component_prop'] == 'value'
        assert 'subscribers' in state_manager.dependency_graph['test_state']

    def test_register_subscriber_success(self, state_manager: StateManager):
        """
            :scenario: Verifies that a subscriber is correctly registered for a pre-existing state.
            :strategy: Register a publisher, then a subscriber, and assert on the graph.
            :contract:
            :pre: A publisher for 'test_state' exists. A subscriber is registered for it.
            :post: The 'subscribers' list for 'test_state' contains the new subscriber's info.

        """
        def dummy_callback(x): return x

        state_manager.register_publisher(
            state_id='test_state',
            component_id='test_publisher',
            component_prop='value'
        )
        state_manager.register_subscriber(
            state_id='test_state',
            component_id='test_subscriber',
            component_prop='figure',
            callback_fn=dummy_callback
        )

        subscribers = state_manager.dependency_graph['test_state']['subscribers']
        assert len(subscribers) == 1
        assert subscribers[0]['component_id'] == 'test_subscriber'
        assert subscribers[0]['callback_fn'] == dummy_callback

    def test_register_subscriber_auto_creates_dummy_state(self, state_manager: StateManager):
        """
            :scenario: Verifies that registering a subscriber without publisher auto-creates dummy state.
            :strategy: Register subscriber without publisher and validate state creation.
            :contract:
            :pre: No publisher is registered for 'test_state'.
            :post: State is auto-created and subscriber is registered successfully.

        """
        # Should not raise an error, but auto-create dummy state
        state_manager.register_subscriber(
            state_id='test_state',
            component_id='test_subscriber',
            component_prop='figure',
            callback_fn=lambda x: x
        )
        
        # Verify state was auto-created
        assert 'test_state' in state_manager.dependency_graph
        assert state_manager.dependency_graph['test_state']['publisher'] is None
        assert len(state_manager.dependency_graph['test_state']['subscribers']) == 1

    def test_generate_callbacks_single_subscriber(self, state_manager: StateManager, mock_app):
        """
            :scenario: Verify callback generation for a state with one subscriber.
            :strategy: Register one pub/sub, call generate_callbacks, and assert app.callback was called correctly.
            :contract:
            :pre: One publisher and one subscriber are registered for 'test_state'.
            :post: app.callback is called once with the correct Input and Output objects.

        """
        state_manager.register_publisher('test_state', 'pub-id', 'value')
        state_manager.register_subscriber('test_state', 'sub-id', 'children', lambda x: x)

        state_manager.generate_callbacks(mock_app)

        mock_app.callback.assert_called_once()
        args, _ = mock_app.callback.call_args
        assert args[0] == [Output('sub-id', 'children')]
        assert args[1] == [Input('pub-id', 'value')]

    def test_generate_callbacks_multiple_subscribers(self, state_manager: StateManager, mock_app):
        """
            :scenario: Verify callback generation for a state with multiple subscribers.
            :strategy: Register one pub and two subs, call generate_callbacks, and assert app.callback args.
            :contract:
            :pre: One publisher and two subscribers are registered.
            :post: app.callback is called with one Input and a list of two Output objects.

        """
        state_manager.register_publisher('test_state', 'pub-id', 'value')
        state_manager.register_subscriber('test_state', 'sub-id-1', 'children', lambda x: x)
        state_manager.register_subscriber('test_state', 'sub-id-2', 'figure', lambda x: x)

        state_manager.generate_callbacks(mock_app)

        mock_app.callback.assert_called_once()
        args, _ = mock_app.callback.call_args
        assert len(args[0]) == 2
        assert Output('sub-id-1', 'children') in args[0]
        assert Output('sub-id-2', 'figure') in args[0]
        assert args[1] == [Input('pub-id', 'value')]

    def test_callback_wrapper_logic(self, state_manager: StateManager):
        """
            :scenario: Directly test the logic of the created callback wrapper function.
            :strategy: Create subscribers with mock callbacks, get the wrapper, call it, and assert results.
            :contract:
            :pre: A list of subscribers is passed to _create_callback_wrapper.
            :post: The wrapper returns a single value for one subscriber and a tuple for multiple.

        """
        # Test with single subscriber
        mock_fn_1 = MagicMock(return_value="result 1")
        subscribers_1 = [{'callback_fn': mock_fn_1}]
        wrapper_1 = state_manager._create_callback_wrapper(subscribers_1)
        result_1 = wrapper_1('input_val')
        mock_fn_1.assert_called_once_with('input_val')
        assert result_1 == "result 1"

        # Test with multiple subscribers
        mock_fn_2 = MagicMock(return_value="result 2")
        subscribers_2 = [{'callback_fn': mock_fn_1}, {'callback_fn': mock_fn_2}]
        wrapper_2 = state_manager._create_callback_wrapper(subscribers_2)
        result_2 = wrapper_2('input_val_2')
        mock_fn_1.assert_called_with('input_val_2')
        mock_fn_2.assert_called_once_with('input_val_2')
        assert result_2 == ("result 1", "result 2")

    def test_generate_callbacks_no_op(self, state_manager: StateManager, mock_app):
        """
            :scenario: Verify no callback is generated if connections are incomplete.
            :strategy: Register only a publisher or only a subscriber and check that app.callback is not called.
            :contract:
            :pre: A state has a publisher but no subscribers (or vice-versa).
            :post: app.callback is not called.

        """
        # Publisher but no subscribers
        state_manager.register_publisher('test_state_1', 'pub-id', 'value')
        state_manager.generate_callbacks(mock_app)
        mock_app.callback.assert_not_called()

        # Clear graph for next test (not strictly necessary with fixture but good practice)
        state_manager.dependency_graph = {}
        mock_app.reset_mock()

        # Subscriber but no publisher (this case raises an error on registration, so it's implicitly tested)
        # Here we test a graph that was manipulated to have no publisher
        state_manager.dependency_graph['test_state_2'] = {'subscribers': [MagicMock()]}
        state_manager.generate_callbacks(mock_app)
        mock_app.callback.assert_not_called()