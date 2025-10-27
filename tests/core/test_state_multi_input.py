"""
Test multi-state input handling in StateManager.

Tests the fix for multi-state data loss where blocks receive
{state_id: value} dict instead of tuple.
"""

from unittest.mock import MagicMock, Mock

import pytest

from dashboard_lego.core.state import StateManager


class TestMultiStateInput:
    """Test multi-state input callback creation."""

    def test_create_multi_input_callback_passes_dict(self):
        """Test that multi-input callback passes state mapping dict."""
        state_manager = StateManager()

        # Mock state infos with different state IDs
        state_infos = [
            {
                "state_id": "price-filter",
                "publisher": {
                    "component_id": "price-slider",
                    "component_prop": "value",
                },
                "callback_fn": Mock(),
            },
            {
                "state_id": "category-filter",
                "publisher": {
                    "component_id": "category-dropdown",
                    "component_prop": "value",
                },
                "callback_fn": Mock(),
            },
        ]

        # Create callback function
        callback_func = state_manager._create_multi_input_callback(state_infos)

        # Mock callback function to capture arguments
        mock_callback = Mock()
        state_infos[0]["callback_fn"] = mock_callback

        # Call with multiple values
        test_values = [100, "electronics"]
        callback_func(*test_values)

        # Verify callback was called with state mapping dict
        mock_callback.assert_called_once()
        call_args = mock_callback.call_args[0]

        # Should be called with dict, not tuple
        assert len(call_args) == 1
        assert isinstance(call_args[0], dict)
        assert call_args[0] == {"price-filter": 100, "category-filter": "electronics"}

    def test_multi_input_callback_handles_missing_values(self):
        """Test callback handles cases where some values are missing."""
        state_manager = StateManager()

        state_infos = [
            {"state_id": "state1", "publisher": {}, "callback_fn": Mock()},
            {"state_id": "state2", "publisher": {}, "callback_fn": Mock()},
            {"state_id": "state3", "publisher": {}, "callback_fn": Mock()},
        ]

        callback_func = state_manager._create_multi_input_callback(state_infos)
        mock_callback = Mock()
        state_infos[0]["callback_fn"] = mock_callback

        # Call with fewer values than states
        callback_func("value1", "value2")  # Only 2 values for 3 states

        # Should still work, missing values logged as warning
        mock_callback.assert_called_once()
        call_args = mock_callback.call_args[0]
        assert call_args[0] == {
            "state1": "value1",
            "state2": "value2",
            # state3 missing - should be handled gracefully
        }

    def test_multi_input_callback_error_handling(self):
        """Test callback handles errors gracefully."""
        state_manager = StateManager()

        state_infos = [
            {
                "state_id": "test-state",
                "publisher": {"component_id": "test", "component_prop": "value"},
                "callback_fn": Mock(side_effect=Exception("Test error")),
            }
        ]

        callback_func = state_manager._create_multi_input_callback(state_infos)

        # Should not raise exception, should return None
        result = callback_func("test_value")
        assert result is None

    def test_state_mapping_logging(self):
        """Test that state mapping is properly logged."""
        state_manager = StateManager()

        state_infos = [
            {
                "state_id": "filter-1",
                "publisher": {"component_id": "comp1", "component_prop": "value"},
                "callback_fn": Mock(),
            }
        ]

        callback_func = state_manager._create_multi_input_callback(state_infos)

        # Call and verify logging occurs
        with pytest.MonkeyPatch().context() as m:
            # Mock logger to capture calls
            mock_logger = Mock()
            m.setattr(state_manager, "logger", mock_logger)

            callback_func("test_value")

            # Verify state mapping was logged
            log_calls = [call[0][0] for call in mock_logger.info.call_args_list]
            assert any("Complete state mapping" in call for call in log_calls)
