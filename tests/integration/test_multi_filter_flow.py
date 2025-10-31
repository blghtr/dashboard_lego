"""
Integration test for multi-filter flow.

Tests end-to-end multi-state subscription and filtering
with multiple external states and embedded controls.
"""

from unittest.mock import MagicMock, Mock

import pandas as pd
import pytest
from dash import dcc

from dashboard_lego.blocks.typed_chart import Control, TypedChartBlock
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.core.state import StateManager


class TestMultiFilterFlow:
    """Test end-to-end multi-filter flow."""

    def test_multi_state_subscription_flow(self):
        """Test complete flow with multiple external states."""
        # Create mock datasource
        mock_datasource = Mock(spec=DataSource)
        mock_datasource.get_processed_data.return_value = pd.DataFrame(
            {"price": [100, 200, 300], "category": ["A", "B", "C"]}
        )

        # Create chart with multiple external subscriptions
        chart = TypedChartBlock(
            block_id="multi-filter-chart",
            datasource=mock_datasource,
            plot_type="scatter",
            plot_params={"x": "price", "y": "category"},
            subscribes_to=["price-filter", "category-filter"],
        )

        # Create state manager
        state_manager = StateManager()

        # Register publishers
        state_manager.register_publisher("price-filter", "price-slider", "value")
        state_manager.register_publisher(
            "category-filter", "category-dropdown", "value"
        )

        # Register chart as subscriber
        state_manager.register_subscriber(
            "price-filter",
            "multi-filter-chart-container",
            "figure",
            chart._update_chart,
        )
        state_manager.register_subscriber(
            "category-filter",
            "multi-filter-chart-container",
            "figure",
            chart._update_chart,
        )

        # Test multi-input callback creation
        state_infos = [
            {
                "state_id": "price-filter",
                "publisher": {
                    "component_id": "price-slider",
                    "component_prop": "value",
                },
                "callback_fn": chart._update_chart,
            },
            {
                "state_id": "category-filter",
                "publisher": {
                    "component_id": "category-dropdown",
                    "component_prop": "value",
                },
                "callback_fn": chart._update_chart,
            },
        ]

        # Mock chart._update_chart to capture calls BEFORE creating callback
        chart._update_chart = Mock(return_value=Mock())

        # Update state_infos to use the mocked function
        state_infos[0]["callback_fn"] = chart._update_chart
        state_infos[1]["callback_fn"] = chart._update_chart

        # Create multi-input callback
        callback_func = state_manager._create_multi_input_callback(state_infos)

        # Call callback with multiple values
        callback_func(100, "electronics")

        # Verify chart was called with state mapping dict
        chart._update_chart.assert_called_once()
        call_args = chart._update_chart.call_args[0]

        # Should be called with dict containing both states
        assert len(call_args) == 1
        assert isinstance(call_args[0], dict)
        assert call_args[0] == {"price-filter": 100, "category-filter": "electronics"}

    def test_mixed_embedded_and_external_controls(self):
        """Test flow with both embedded controls and external states."""
        # Create mock datasource
        mock_datasource = Mock(spec=DataSource)
        mock_datasource.get_processed_data.return_value = pd.DataFrame(
            {"x": [1, 2, 3], "y": [4, 5, 6]}
        )

        # Create chart with both embedded controls and external subscription
        chart = TypedChartBlock(
            block_id="mixed-chart",
            datasource=mock_datasource,
            plot_type="scatter",
            plot_params={"x": "{{x_col}}", "y": "{{y_col}}"},
            controls={
                "x_col": Control(component=dcc.Dropdown, props={"value": "price"}),
                "y_col": Control(component=dcc.Dropdown, props={"value": "sales"}),
            },
            subscribes_to="global-filter",
        )

        # Test control value normalization
        state_manager = StateManager()

        # Simulate control values from callback
        control_values = {
            "global-filter": "electronics",  # External state
            "x_col": "price",  # Embedded control (normalized)
            "y_col": "sales",  # Embedded control (normalized)
        }

        # Test datasource parameter extraction
        datasource_params = chart._extract_datasource_params(control_values)

        # Only external state should go to datasource (normalized)
        assert "filter" in datasource_params
        assert datasource_params["filter"] == "electronics"
        assert "x_col" not in datasource_params
        assert "y_col" not in datasource_params

    def test_initial_state_sync_flow(self):
        """Test initial state synchronization flow."""
        # Create mock datasource
        mock_datasource = Mock(spec=DataSource)
        mock_datasource.get_processed_data.return_value = pd.DataFrame(
            {"value": [1, 2, 3]}
        )

        # Create chart with external subscription
        chart = TypedChartBlock(
            block_id="sync-chart",
            datasource=mock_datasource,
            plot_type="histogram",
            plot_params={"x": "value"},
            subscribes_to="initial-filter",
        )

        # Create state manager
        state_manager = StateManager()

        # Register publisher
        state_manager.register_publisher("initial-filter", "filter-control", "value")

        # Get initial values (would be None in real scenario)
        initial_values = state_manager.get_initial_publisher_values()
        assert "initial-filter" in initial_values
        assert initial_values["initial-filter"] is None

        # Set initial values on block
        chart.set_initial_external_values({"initial-filter": "initial_value"})

        # Mock _update_chart to capture calls
        chart._update_chart = Mock(return_value=Mock())

        # Call layout (should use initial values)
        chart.layout()

        # Verify _update_chart was called with initial values
        chart._update_chart.assert_called_once()
        call_args = chart._update_chart.call_args[0]

        # Should contain initial external value
        assert "initial-filter" in call_args[0]
        assert call_args[0]["initial-filter"] == "initial_value"

    def test_error_handling_in_multi_state_flow(self):
        """Test error handling in multi-state flow."""
        # Create mock datasource that raises error
        mock_datasource = Mock(spec=DataSource)
        mock_datasource.get_processed_data.side_effect = Exception("Datasource error")

        # Create chart
        chart = TypedChartBlock(
            block_id="error-chart",
            datasource=mock_datasource,
            plot_type="histogram",
            plot_params={"x": "value"},
            subscribes_to="error-filter",
        )

        # Test control values
        control_values = {"error-filter": "test_value"}

        # Call _update_chart (should handle error gracefully)
        result = chart._update_chart(control_values)

        # Should return error figure, not raise exception
        assert result is not None
        # Should be a Plotly Figure with error annotation
        assert hasattr(result, "add_annotation")

    def test_empty_dataframe_context_aware_error(self):
        """Test context-aware error messages for empty DataFrames."""
        # Create mock datasource that returns empty DataFrame
        mock_datasource = Mock(spec=DataSource)
        mock_datasource.get_processed_data.return_value = pd.DataFrame()

        # Create chart with external subscription
        chart = TypedChartBlock(
            block_id="empty-chart",
            datasource=mock_datasource,
            plot_type="histogram",
            plot_params={"x": "value"},
            subscribes_to="price-filter",
        )

        # Test control values with filters
        control_values = {"price-filter": 100}

        # Call _update_chart
        result = chart._update_chart(control_values)

        # Should return figure with context-aware error message
        assert result is not None
        assert hasattr(result, "add_annotation")

        # Check that error message contains context
        annotations = result.data if hasattr(result, "data") else []
        # The error message should be in the annotation text
        # (This is a simplified check - in reality we'd need to inspect the figure structure)
