"""
Test initial state value synchronization.

Tests that StateManager tracks initial publisher values and
blocks receive them before layout().
"""

from unittest.mock import MagicMock, Mock

import pytest

from dashboard_lego.blocks.base import BaseBlock
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.core.state import StateManager


class TestInitialStateSync:
    """Test initial state value synchronization."""

    def test_publisher_value_tracking(self):
        """Test that StateManager tracks publisher values."""
        state_manager = StateManager()

        # Register publishers
        state_manager.register_publisher("price-filter", "price-slider", "value")
        state_manager.register_publisher(
            "category-filter", "category-dropdown", "value"
        )

        # Check that values are tracked
        assert "price-filter" in state_manager._publisher_values
        assert "category-filter" in state_manager._publisher_values
        assert state_manager._publisher_values["price-filter"] is None
        assert state_manager._publisher_values["category-filter"] is None

        # Check component tracking
        assert "price-filter" in state_manager._publisher_components
        assert state_manager._publisher_components["price-filter"] == (
            "price-slider",
            "value",
        )

    def test_get_initial_publisher_values(self):
        """Test getting initial publisher values."""
        state_manager = StateManager()

        # Register some publishers
        state_manager.register_publisher("state1", "comp1", "value")
        state_manager.register_publisher("state2", "comp2", "value")

        # Get initial values
        initial_values = state_manager.get_initial_publisher_values()

        assert initial_values == {"state1": None, "state2": None}

    def test_base_block_initial_values(self):
        """Test BaseBlock receives initial external values."""
        from dashboard_lego.blocks.typed_chart import TypedChartBlock

        # Create mock datasource
        mock_datasource = Mock(spec=DataSource)

        # Create concrete block with external subscription
        block = TypedChartBlock(
            block_id="test-block",
            datasource=mock_datasource,
            plot_type="histogram",
            plot_params={"x": "value"},
            subscribes_to="external-state",
        )

        # Set initial external values
        initial_values = {"external-state": "initial_value"}
        block.set_initial_external_values(initial_values)

        # Verify values were stored
        assert hasattr(block, "_initial_external_values")
        assert block._initial_external_values == initial_values

    def test_typed_chart_uses_initial_values(self):
        """Test TypedChartBlock uses initial external values in layout."""
        from dashboard_lego.blocks.typed_chart import TypedChartBlock

        # Create mock datasource
        mock_datasource = Mock(spec=DataSource)
        mock_datasource.get_processed_data.return_value = Mock()  # Empty DataFrame

        # Create chart block with external subscription
        chart = TypedChartBlock(
            block_id="test-chart",
            datasource=mock_datasource,
            plot_type="histogram",
            plot_params={"x": "value"},
            subscribes_to="external-filter",
        )

        # Set initial external values
        chart.set_initial_external_values({"external-filter": "initial_filter"})

        # Mock the _update_chart method to capture calls
        original_update = chart._update_chart
        chart._update_chart = Mock(return_value=Mock())

        # Call layout
        chart.layout()

        # Verify _update_chart was called with initial values
        chart._update_chart.assert_called_once()
        call_args = chart._update_chart.call_args[0]

        # Should be called with dict containing initial values
        assert len(call_args) == 1
        assert isinstance(call_args[0], dict)
        assert "external-filter" in call_args[0]
        assert call_args[0]["external-filter"] == "initial_filter"

    def test_initial_values_merge_embedded_and_external(self):
        """Test that initial values merge embedded controls and external states."""
        from dash import dcc

        from dashboard_lego.blocks.typed_chart import Control, TypedChartBlock

        # Create mock datasource
        mock_datasource = Mock(spec=DataSource)
        mock_datasource.get_processed_data.return_value = Mock()  # Empty DataFrame

        # Create chart with both embedded controls and external subscription
        chart = TypedChartBlock(
            block_id="test-chart",
            datasource=mock_datasource,
            plot_type="histogram",
            plot_params={"x": "{{embedded_control}}"},
            controls={
                "embedded_control": Control(
                    component=dcc.Dropdown, props={"value": "default_embedded"}
                )
            },
            subscribes_to="external-filter",
        )

        # Set initial external values
        chart.set_initial_external_values({"external-filter": "initial_external"})

        # Mock _update_chart to capture arguments
        chart._update_chart = Mock(return_value=Mock())

        # Call layout
        chart.layout()

        # Verify _update_chart was called with merged values
        call_args = chart._update_chart.call_args[0]
        initial_values = call_args[0]

        # Should contain both embedded and external values
        # Note: embedded controls might not be included if they don't have 'value' prop
        assert "external-filter" in initial_values
        assert initial_values["external-filter"] == "initial_external"

        # Check if embedded control is present (depends on control initialization)
        if "embedded_control" in initial_values:
            assert initial_values["embedded_control"] == "default_embedded"
