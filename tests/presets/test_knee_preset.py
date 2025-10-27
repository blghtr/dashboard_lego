"""
Tests for KneePlotPreset.

:hierarchy: [Tests | Presets | KneePlotPreset]
:relates-to:
 - motivated_by: "Integration tests for KneePlotPreset functionality"
 - implements: "test module: 'test_knee_preset'"

:contract:
 - pre: "Test environment with dashboard_lego components available"
 - post: "All tests pass, KneePlotPreset works correctly"

:complexity: 2
"""

from typing import Any, Dict

import pandas as pd
import pytest

from dashboard_lego.core.datasource import DataSource
from dashboard_lego.presets.eda_presets import KneePlotPreset


class TestKneePlotPreset:
    """
    Test cases for KneePlotPreset class.

    :hierarchy: [Tests | Presets | KneePlotPreset | TestKneePlotPreset]
    :relates-to:
     - motivated_by: "Integration testing of KneePlotPreset with TypedChartBlock"
     - implements: "test class: 'TestKneePlotPreset'"

    :contract:
     - pre: "Valid test data and datasource available"
     - post: "All test cases pass"

    :complexity: 2
    """

    @pytest.fixture
    def sample_data(self):
        """Create sample data for knee plot preset testing."""
        # Create data that has a clear knee point
        k_values = list(range(1, 11))
        # Simulate inertia values with a clear elbow at k=3
        inertia_values = [100, 50, 20, 15, 12, 10, 9, 8, 7, 6]
        silhouette_values = [0.1, 0.3, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0]

        return pd.DataFrame(
            {
                "k": k_values,
                "inertia": inertia_values,
                "silhouette": silhouette_values,
                "category": ["A", "B", "C", "D", "E", "F", "G", "H", "I", "J"],
            }
        )

    @pytest.fixture
    def datasource(self, sample_data):
        """Create datasource for testing."""
        from dashboard_lego.core.data_builder import DataBuilder

        class TestDataBuilder(DataBuilder):
            def __init__(self, data, **kwargs):
                super().__init__(**kwargs)
                self.data = data

            def _build(self, **kwargs) -> pd.DataFrame:
                return self.data

        return DataSource(data_builder=TestDataBuilder(sample_data))

    def test_knee_plot_preset_initialization(self, datasource):
        """Test KneePlotPreset initialization."""
        preset = KneePlotPreset(
            block_id="test_knee", datasource=datasource, title="Test Knee Plot"
        )

        assert preset.block_id == "test_knee"
        assert preset._plot_type == "knee_plot"
        assert preset.title == "Test Knee Plot"
        assert len(preset.controls) == 0  # No controls by default (controls=False)

    def test_knee_plot_preset_controls(self, datasource):
        """Test that controls are properly configured when enabled."""
        preset = KneePlotPreset(
            block_id="test_knee",
            datasource=datasource,
            controls=True,  # Enable controls
        )

        # Check that all expected controls exist
        expected_controls = ["x_col", "y_col", "auto_knee", "curve", "direction", "S"]
        assert all(ctrl in preset.controls for ctrl in expected_controls)

        # Check that plot_params uses placeholders when controls are enabled
        assert preset.plot_params == {"x": "{{x_col}}", "y": "{{y_col}}"}

        # Check that plot_kwargs uses placeholders for knee detection parameters
        expected_kwargs = {
            "auto_knee": "{{auto_knee}}",
            "knee_curve": "{{curve}}",
            "knee_direction": "{{direction}}",
            "knee_S": "{{S}}",
        }
        assert preset.plot_kwargs == expected_kwargs

        # Check that plot_title is dynamic when controls are enabled
        assert preset.plot_title == "Knee Plot: {{x_col}} vs {{y_col}}"

        # Check x_col and y_col have numerical options
        x_col_control = preset.controls["x_col"]
        y_col_control = preset.controls["y_col"]
        assert "k" in x_col_control.props["options"]
        assert "inertia" in y_col_control.props["options"]

        assert (
            len(x_col_control.props["options"]) >= 2
        )  # At least k, inertia, silhouette
        assert len(y_col_control.props["options"]) >= 2

        # Check auto_knee is a switch with default False
        auto_knee_control = preset.controls["auto_knee"]
        assert auto_knee_control.props["value"] is False

    def test_knee_plot_preset_partial_controls(self, datasource):
        """Test partial control configuration using dict."""
        preset = KneePlotPreset(
            block_id="test_knee",
            datasource=datasource,
            controls={
                "x_col": True,  # Enable x_col control
                "y_col": True,  # Enable y_col control
                "auto_knee": False,  # Disable auto_knee control
                "curve": True,  # Enable curve control
                "direction": False,  # Disable direction control
                "S": True,  # Enable S control
            },
        )

        # Check that only enabled controls exist
        expected_controls = ["x_col", "y_col", "curve", "S"]
        assert all(ctrl in preset.controls for ctrl in expected_controls)
        assert "auto_knee" not in preset.controls
        assert "direction" not in preset.controls

        # Check that plot_params uses placeholders for enabled controls
        assert preset.plot_params == {"x": "{{x_col}}", "y": "{{y_col}}"}

        # Check that plot_kwargs uses placeholders for enabled controls, values for disabled
        expected_kwargs = {
            "auto_knee": False,  # Default value since control disabled
            "knee_curve": "{{curve}}",  # Placeholder since control enabled
            "knee_direction": "increasing",  # Default value since control disabled
            "knee_S": "{{S}}",  # Placeholder since control enabled
        }
        assert preset.plot_kwargs == expected_kwargs

        # Check that plot_title is dynamic when x_col and y_col controls are enabled
        assert preset.plot_title == "Knee Plot: {{x_col}} vs {{y_col}}"

    def test_knee_plot_preset_plot_params(self, datasource):
        """Test that plot parameters are correctly set."""
        preset = KneePlotPreset(
            block_id="test_knee",
            datasource=datasource,
            controls=True,  # Enable controls to get placeholders
        )

        # Check plot_params uses placeholders when controls are enabled
        assert preset.plot_params == {"x": "{{x_col}}", "y": "{{y_col}}"}

        # Check plot_kwargs includes knee detection parameters
        expected_kwargs = {
            "auto_knee": "{{auto_knee}}",
            "knee_curve": "{{curve}}",
            "knee_direction": "{{direction}}",
            "knee_S": "{{S}}",
        }
        assert preset.plot_kwargs == expected_kwargs

    def test_knee_plot_preset_insufficient_columns(self):
        """Test error handling for insufficient numerical columns."""
        from dashboard_lego.core.data_builder import DataBuilder

        # Create DataFrame with only one numerical column
        insufficient_data = pd.DataFrame(
            {"k": [1, 2, 3], "category": ["A", "B", "C"]}  # Only categorical
        )

        class TestDataBuilder(DataBuilder):
            def __init__(self, data, **kwargs):
                super().__init__(**kwargs)
                self.data = data

            def _build(self, **kwargs) -> pd.DataFrame:
                return self.data

        datasource = DataSource(data_builder=TestDataBuilder(insufficient_data))

        with pytest.raises(ValueError, match="requires at least two numerical columns"):
            KneePlotPreset(block_id="test_knee", datasource=datasource)

    def test_knee_plot_preset_layout(self, datasource):
        """Test that preset can generate layout."""
        preset = KneePlotPreset(block_id="test_knee", datasource=datasource)

        layout = preset.layout()

        # Should return a Dash component
        assert layout is not None
        # Should be a Card component (check by class name)
        assert layout.__class__.__name__ == "Card"

    def test_knee_plot_preset_get_figure(self, datasource):
        """Test that preset can generate standalone figure."""
        preset = KneePlotPreset(block_id="test_knee", datasource=datasource)

        # Test with default parameters
        fig = preset.get_figure()

        # Should return a Plotly figure
        assert fig is not None
        assert hasattr(fig, "data")
        assert hasattr(fig, "layout")

    def test_knee_plot_preset_with_parameters(self, datasource):
        """Test preset with custom parameters."""
        fig = KneePlotPreset(block_id="test_knee", datasource=datasource).get_figure(
            {
                "x_col": "k",
                "y_col": "inertia",
                "auto_knee": True,
                "curve": "convex",
                "direction": "decreasing",
                "S": 2.0,
            }
        )

        assert fig is not None
        assert hasattr(fig, "data")
        assert hasattr(fig, "layout")

    def test_knee_plot_preset_auto_size_controls(self, datasource):
        """Test that controls use auto-size by default."""
        preset = KneePlotPreset(
            block_id="test_knee", datasource=datasource, controls=True
        )

        # Check that dropdown controls have auto_size enabled by default
        x_col_control = preset.controls["x_col"]
        y_col_control = preset.controls["y_col"]
        curve_control = preset.controls["curve"]
        direction_control = preset.controls["direction"]

        # All dropdown controls should have auto_size=True by default
        assert x_col_control.auto_size is True
        assert y_col_control.auto_size is True
        assert curve_control.auto_size is True
        assert direction_control.auto_size is True

        # All dropdown controls should have max_ch=40 by default
        assert x_col_control.max_ch == 40
        assert y_col_control.max_ch == 40
        assert curve_control.max_ch == 40
        assert direction_control.max_ch == 40

        # All dropdown controls should have md="auto" in col_props by default
        assert x_col_control.col_props["md"] == "auto"
        assert y_col_control.col_props["md"] == "auto"
        assert curve_control.col_props["md"] == "auto"
        assert direction_control.col_props["md"] == "auto"
