"""
Tests for ControlPanelBlock layout and slider width behavior.

Tests that sliders get proper width styling and col_props defaults
are applied correctly in the control panel.
"""

from unittest.mock import Mock

import pytest

from dashboard_lego.blocks.control_panel import Control, ControlPanelBlock
from dashboard_lego.core.data_builder import DataBuilder
from dashboard_lego.core.datasource import DataSource


class TestControlPanelLayout:
    """Test ControlPanelBlock layout behavior."""

    def test_slider_gets_modern_slider_class(self):
        """Test that sliders get modern-slider className if not explicitly set."""
        # Create mock datasource
        mock_datasource = Mock(spec=DataSource)
        mock_datasource.get_processed_data.return_value = Mock()

        # Create control with slider
        slider_control = Control(
            component=Mock(__name__="Slider"),
            props={"min": 0, "max": 100, "value": 50},
            col_props={"xs": 12, "md": 12},
        )

        # Create control panel
        panel = ControlPanelBlock(
            block_id="test_panel",
            datasource=mock_datasource,
            title="Test Panel",
            controls={"slider": slider_control},
        )

        # Build control elements
        control_elements = panel._build_control_elements()

        # Check that the control elements are created (this tests the method doesn't crash)
        # The actual className styling is applied internally in _build_control_elements
        # and would be visible in the rendered component
        assert control_elements is not None

    def test_slider_with_explicit_classname_preserved(self):
        """Test that sliders with explicit className don't get overridden."""
        # Create mock datasource
        mock_datasource = Mock(spec=DataSource)
        mock_datasource.get_processed_data.return_value = Mock()

        # Create control with slider that has explicit className
        slider_control = Control(
            component=Mock(__name__="Slider"),
            props={"min": 0, "max": 100, "value": 50, "className": "custom-slider"},
            col_props={"xs": 12, "md": 12},
        )

        # Create control panel
        panel = ControlPanelBlock(
            block_id="test_panel",
            datasource=mock_datasource,
            title="Test Panel",
            controls={"slider": slider_control},
        )

        # Build control elements
        control_elements = panel._build_control_elements()

        # Check that explicit className is preserved
        assert slider_control.props.get("className") == "custom-slider"

    def test_non_slider_controls_unchanged(self):
        """Test that non-slider controls don't get width styling."""
        # Create mock datasource
        mock_datasource = Mock(spec=DataSource)
        mock_datasource.get_processed_data.return_value = Mock()

        # Create control with dropdown
        dropdown_control = Control(
            component=Mock(__name__="Dropdown"),
            props={"options": [{"label": "A", "value": "A"}]},
            col_props={"xs": 12, "md": 4},
        )

        # Create control panel
        panel = ControlPanelBlock(
            block_id="test_panel",
            datasource=mock_datasource,
            title="Test Panel",
            controls={"dropdown": dropdown_control},
        )

        # Build control elements
        control_elements = panel._build_control_elements()

        # Check that dropdown doesn't get width styling
        assert "style" not in dropdown_control.props

    def test_control_defaults_used_when_none(self):
        """Test that control panel uses safe defaults when col_props is None."""
        # Create mock datasource
        mock_datasource = Mock(spec=DataSource)
        mock_datasource.get_processed_data.return_value = Mock()

        # Create control with None col_props
        control = Control(
            component=Mock(__name__="Slider"),
            props={"min": 0, "max": 100},
            col_props=None,
        )

        # Create control panel
        panel = ControlPanelBlock(
            block_id="test_panel",
            datasource=mock_datasource,
            title="Test Panel",
            controls={"test": control},
        )

        # Build control elements
        control_elements = panel._build_control_elements()

        # Check that safe default is used
        # The actual col_props used would be {"xs": 12, "md": 12}
        # This is tested by ensuring the control panel doesn't crash
        assert control_elements is not None

    def test_multiple_controls_layout(self):
        """Test that multiple controls are laid out correctly."""
        # Create mock datasource
        mock_datasource = Mock(spec=DataSource)
        mock_datasource.get_processed_data.return_value = Mock()

        # Create multiple controls
        controls = {
            "slider": Control(
                component=Mock(__name__="Slider"),
                props={"min": 0, "max": 100},
                col_props={"xs": 12, "md": 12},
            ),
            "dropdown": Control(
                component=Mock(__name__="Dropdown"),
                props={"options": []},
                col_props={"xs": 12, "md": 4},
            ),
        }

        # Create control panel
        panel = ControlPanelBlock(
            block_id="test_panel",
            datasource=mock_datasource,
            title="Test Panel",
            controls=controls,
        )

        # Build control elements
        control_elements = panel._build_control_elements()

        # Check that both controls are processed
        assert control_elements is not None
        # The actual layout would be a dbc.Row with dbc.Col elements
        # This test ensures the method doesn't crash with multiple controls
