"""
Test datasource parameter extraction in TypedChartBlock.

Tests the explicit routing of control values to datasource
parameters.
"""

from unittest.mock import MagicMock, Mock

import pandas as pd
import pytest

from dashboard_lego.blocks.typed_chart import TypedChartBlock
from dashboard_lego.core.datasource import DataSource


class TestDatasourceParameterExtraction:
    """Test datasource parameter extraction logic."""

    def test_extract_datasource_params_external_states(self):
        """Test that external subscribed states become datasource params."""
        # Create mock datasource
        mock_datasource = Mock(spec=DataSource)

        # Create chart with external subscription and embedded controls
        from dash import dcc

        from dashboard_lego.blocks.typed_chart import Control

        chart = TypedChartBlock(
            block_id="test-chart",
            datasource=mock_datasource,
            plot_type="histogram",
            plot_params={"x": "value"},
            subscribes_to="price-filter",
            controls={
                "x_col": Control(component=dcc.Dropdown, props={"value": "price"})
            },
        )

        # Test control values with external state
        control_values = {
            "price-filter": 100,  # External state
            "x_col": "price",  # Embedded control
        }

        # Extract datasource parameters
        datasource_params = chart._extract_datasource_params(control_values)

        # External state should become datasource param (normalized)
        assert "filter" in datasource_params
        assert datasource_params["filter"] == 100

        # Embedded control should NOT be in datasource params
        assert "x_col" not in datasource_params

    def test_extract_datasource_params_embedded_controls_skipped(self):
        """Test that embedded controls are not sent to datasource."""
        # Create mock datasource
        mock_datasource = Mock(spec=DataSource)

        # Create chart with embedded controls
        from dash import dcc

        from dashboard_lego.blocks.typed_chart import Control

        chart = TypedChartBlock(
            block_id="test-chart",
            datasource=mock_datasource,
            plot_type="histogram",
            plot_params={"x": "{{x_col}}"},
            controls={
                "x_col": Control(component=dcc.Dropdown, props={"value": "price"}),
                "y_col": Control(component=dcc.Dropdown, props={"value": "sales"}),
            },
        )

        # Test control values with only embedded controls
        control_values = {"x_col": "price", "y_col": "sales"}

        # Extract datasource parameters
        datasource_params = chart._extract_datasource_params(control_values)

        # Embedded controls should be skipped
        assert datasource_params == {}

    def test_extract_datasource_params_mixed_scenario(self):
        """Test extraction with both external states and embedded controls."""
        # Create mock datasource
        mock_datasource = Mock(spec=DataSource)

        # Create chart with both types
        from dash import dcc

        from dashboard_lego.blocks.typed_chart import Control

        chart = TypedChartBlock(
            block_id="test-chart",
            datasource=mock_datasource,
            plot_type="scatter",
            plot_params={"x": "{{x_col}}", "y": "{{y_col}}"},
            controls={
                "x_col": Control(component=dcc.Dropdown, props={"value": "price"}),
                "y_col": Control(component=dcc.Dropdown, props={"value": "sales"}),
            },
            subscribes_to=["price-filter", "category-filter"],
        )

        # Test control values
        control_values = {
            "price-filter": 100,  # External state
            "category-filter": "electronics",  # External state
            "x_col": "price",  # Embedded control
            "y_col": "sales",  # Embedded control
        }

        # Extract datasource parameters
        datasource_params = chart._extract_datasource_params(control_values)

        # Only external states should be in datasource params (normalized)
        assert "filter" in datasource_params
        assert datasource_params["filter"] == "electronics"  # Last value wins

        # Embedded controls should be skipped
        assert "x_col" not in datasource_params
        assert "y_col" not in datasource_params

    def test_extract_datasource_params_unknown_params(self):
        """Test that unknown parameters are passed through to datasource."""
        # Create mock datasource
        mock_datasource = Mock(spec=DataSource)

        # Create chart with no controls or subscriptions
        chart = TypedChartBlock(
            block_id="test-chart",
            datasource=mock_datasource,
            plot_type="histogram",
            plot_params={"x": "value"},
        )

        # Test control values with unknown parameters
        control_values = {"unknown_param": "value1", "another_param": "value2"}

        # Extract datasource parameters
        datasource_params = chart._extract_datasource_params(control_values)

        # Unknown parameters should pass through
        assert "unknown_param" in datasource_params
        assert datasource_params["unknown_param"] == "value1"
        assert "another_param" in datasource_params
        assert datasource_params["another_param"] == "value2"

    def test_extract_datasource_params_system_keys_skipped(self):
        """Test that system keys like 'section' and 'type' are skipped."""
        # Create mock datasource
        mock_datasource = Mock(spec=DataSource)

        # Create chart
        chart = TypedChartBlock(
            block_id="test-chart",
            datasource=mock_datasource,
            plot_type="histogram",
            plot_params={"x": "value"},
        )

        # Test control values with system keys
        control_values = {"section": 1, "type": "chart", "valid_param": "value"}

        # Extract datasource parameters
        datasource_params = chart._extract_datasource_params(control_values)

        # System keys should be skipped
        assert "section" not in datasource_params
        assert "type" not in datasource_params

        # Valid param should pass through
        assert "valid_param" in datasource_params
        assert datasource_params["valid_param"] == "value"

    def test_extract_datasource_params_logging(self):
        """Test that parameter extraction is properly logged."""
        # Create mock datasource
        mock_datasource = Mock(spec=DataSource)

        # Create chart with external subscription and embedded controls
        from dash import dcc

        from dashboard_lego.blocks.typed_chart import Control

        chart = TypedChartBlock(
            block_id="test-chart",
            datasource=mock_datasource,
            plot_type="histogram",
            plot_params={"x": "value"},
            subscribes_to="price-filter",
            controls={
                "x_col": Control(component=dcc.Dropdown, props={"value": "price"})
            },
        )

        # Test control values
        control_values = {"price-filter": 100, "x_col": "price"}

        # Mock logger to capture debug calls
        with pytest.MonkeyPatch().context() as m:
            mock_logger = Mock()
            m.setattr(chart, "logger", mock_logger)

            # Extract datasource parameters
            chart._extract_datasource_params(control_values)

            # Verify logging occurred
            debug_calls = [call[0][0] for call in mock_logger.debug.call_args_list]
            assert any("external state" in call for call in debug_calls)
            assert any("embedded control" in call for call in debug_calls)

    def test_update_chart_uses_extract_datasource_params(self):
        """Test that _update_chart uses the new parameter extraction method."""
        # Create mock datasource
        mock_datasource = Mock(spec=DataSource)
        mock_datasource.get_processed_data.return_value = pd.DataFrame(
            {"value": [1, 2, 3]}
        )

        # Create chart with external subscription
        chart = TypedChartBlock(
            block_id="test-chart",
            datasource=mock_datasource,
            plot_type="histogram",
            plot_params={"x": "value"},
            subscribes_to="price-filter",
        )

        # Mock the extract method to verify it's called
        chart._extract_datasource_params = Mock(return_value={"price_filter": 100})

        # Test control values
        control_values = {"price-filter": 100, "x_col": "price"}

        # Call _update_chart
        chart._update_chart(control_values)

        # Verify extract method was called
        chart._extract_datasource_params.assert_called_once_with(control_values)

        # Verify datasource was called with extracted params
        mock_datasource.get_processed_data.assert_called_once_with(
            {"price_filter": 100}
        )
