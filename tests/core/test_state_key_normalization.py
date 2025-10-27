"""
Test control value key normalization.

Tests that StateManager normalizes control value keys for
consistent handling between external states and embedded controls.
"""

from unittest.mock import Mock

import pytest

from dashboard_lego.core.state import StateManager


class TestKeyNormalization:
    """Test control value key normalization."""

    def test_normalize_control_keys_external_states(self):
        """Test that external states keep their state_id as key."""
        state_manager = StateManager()

        # Create mock block with external subscription
        mock_block = Mock()
        mock_block.subscribes = {"external-filter": Mock()}
        mock_block.controls = {"embedded_control": Mock()}

        # Test control values with mixed keys
        control_values = {
            "external-filter": "filter_value",
            "embedded_control": "control_value",
        }

        # Normalize keys
        normalized = state_manager._normalize_control_keys(control_values, mock_block)

        # External state should keep original key
        assert "external-filter" in normalized
        assert normalized["external-filter"] == "filter_value"

        # Embedded control should keep short name
        assert "embedded_control" in normalized
        assert normalized["embedded_control"] == "control_value"

    def test_normalize_control_keys_embedded_controls(self):
        """Test that embedded controls use short names."""
        state_manager = StateManager()

        # Create mock block with embedded controls
        mock_block = Mock()
        mock_block.subscribes = {}
        mock_x_control = Mock()
        mock_x_control.dep_param_name = "x_col"
        mock_y_control = Mock()
        mock_y_control.dep_param_name = "y_col"
        mock_block.controls = {"x_col": mock_x_control, "y_col": mock_y_control}

        # Test control values with component IDs
        control_values = {"chart-block-x_col": "price", "chart-block-y_col": "sales"}

        # Normalize keys
        normalized = state_manager._normalize_control_keys(control_values, mock_block)

        # Should extract short names
        assert "x_col" in normalized
        assert normalized["x_col"] == "price"
        assert "y_col" in normalized
        assert normalized["y_col"] == "sales"

    def test_normalize_control_keys_mixed_scenario(self):
        """Test normalization with both external states and embedded controls."""
        state_manager = StateManager()

        # Create mock block with both types
        mock_block = Mock()
        mock_block.subscribes = {"global-filter": Mock()}
        mock_chart_control = Mock()
        mock_chart_control.dep_param_name = "chart_type"
        mock_block.controls = {"chart_type": mock_chart_control}

        # Mixed control values
        control_values = {
            "global-filter": "electronics",  # External state
            "chart-block-chart_type": "bar",  # Embedded control
            "unknown_param": "value",  # Unknown
        }

        # Normalize keys
        normalized = state_manager._normalize_control_keys(control_values, mock_block)

        # External state keeps original key
        assert "global-filter" in normalized
        assert normalized["global-filter"] == "electronics"

        # Embedded control gets short name
        assert "chart_type" in normalized
        assert normalized["chart_type"] == "bar"

        # Unknown param passes through
        assert "unknown_param" in normalized
        assert normalized["unknown_param"] == "value"

    def test_normalize_control_keys_empty_controls(self):
        """Test normalization with empty controls."""
        state_manager = StateManager()

        # Create mock block with no controls
        mock_block = Mock()
        mock_block.subscribes = {}
        mock_block.controls = {}

        # Empty control values
        control_values = {}

        # Normalize keys
        normalized = state_manager._normalize_control_keys(control_values, mock_block)

        # Should return empty dict
        assert normalized == {}

    def test_normalize_control_keys_unknown_format(self):
        """Test normalization handles unknown key formats."""
        state_manager = StateManager()

        # Create mock block
        mock_block = Mock()
        mock_block.subscribes = {}
        mock_block.controls = {}

        # Control values with unknown format
        control_values = {
            "simple_key": "value1",
            "complex-key-with-dashes": "value2",
            "no_dash_key": "value3",
        }

        # Normalize keys
        normalized = state_manager._normalize_control_keys(control_values, mock_block)

        # Unknown formats should pass through
        assert normalized == control_values

    def test_normalize_control_keys_logging(self):
        """Test that normalization logs key transformations."""
        state_manager = StateManager()

        # Create mock block
        mock_block = Mock()
        mock_block.subscribes = {"external-state": Mock()}
        mock_block.controls = {"control": Mock()}

        # Control values
        control_values = {"external-state": "value1", "block-control": "value2"}

        # Mock logger to capture debug calls
        with pytest.MonkeyPatch().context() as m:
            mock_logger = Mock()
            m.setattr(state_manager, "logger", mock_logger)

            # Normalize keys
            state_manager._normalize_control_keys(control_values, mock_block)

            # Verify debug logging occurred
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            assert any("External state" in call for call in debug_calls)
            assert any("Embedded control" in call for call in debug_calls)

    def test_normalize_control_keys_with_dep_param_name_external(self):
        """Test that external states with dep_param_name get transformed."""
        state_manager = StateManager()

        # Set up dep_param_name mapping
        state_manager._dep_param_names["external-filter"] = "transform__window_step"

        # Create mock block with external subscription
        mock_block = Mock()
        mock_block.subscribes = {"external-filter": Mock()}
        mock_block.controls = {}

        # Control values
        control_values = {"external-filter": "filter_value"}

        # Normalize keys
        normalized = state_manager._normalize_control_keys(control_values, mock_block)

        # Should transform to dep_param_name
        assert "transform__window_step" in normalized
        assert normalized["transform__window_step"] == "filter_value"
        assert "external-filter" not in normalized

    def test_normalize_control_keys_with_dep_param_name_embedded(self):
        """Test that embedded controls with dep_param_name get transformed."""
        state_manager = StateManager()

        # Create mock control with dep_param_name
        mock_control = Mock()
        mock_control.dep_param_name = "build__category"

        # Create mock block with embedded control
        mock_block = Mock()
        mock_block.subscribes = {}
        mock_block.controls = {"category_selector": mock_control}

        # Control values
        control_values = {"chart-block-category_selector": "electronics"}

        # Normalize keys
        normalized = state_manager._normalize_control_keys(control_values, mock_block)

        # Should transform to dep_param_name
        assert "build__category" in normalized
        assert normalized["build__category"] == "electronics"
        assert "category_selector" not in normalized

    def test_normalize_control_keys_without_dep_param_name(self):
        """Test that controls without dep_param_name keep original behavior."""
        state_manager = StateManager()

        # Create mock control without dep_param_name
        mock_control = Mock()
        mock_control.dep_param_name = None

        # Create mock block
        mock_block = Mock()
        mock_block.subscribes = {}
        mock_block.controls = {"simple_control": mock_control}

        # Control values
        control_values = {"chart-block-simple_control": "value"}

        # Normalize keys
        normalized = state_manager._normalize_control_keys(control_values, mock_block)

        # Should use short name (original behavior)
        assert "simple_control" in normalized
        assert normalized["simple_control"] == "value"
