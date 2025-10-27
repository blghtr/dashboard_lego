"""
Tests for control building helpers.

Tests the build_controls_from_spec function to ensure proper defaults
and CSS class assignment for different control types.
"""

import pytest

from dashboard_lego.blocks.control_helpers import build_controls_from_spec


class TestControlHelpers:
    """Test control helper functions."""

    def test_slider_defaults(self):
        """Test that sliders get proper defaults and CSS class."""
        controls_spec = [
            {"name": "test_slider", "type": "slider", "min": 0, "max": 100, "value": 50}
        ]

        controls = build_controls_from_spec(controls_spec)

        assert "test_slider" in controls
        control = controls["test_slider"]

        # Check col_props default for slider
        assert control.col_props == {"xs": 12, "md": 12}

        # Check CSS class is added
        assert control.props["className"] == "modern-slider"

        # Check other props are preserved
        assert control.props["min"] == 0
        assert control.props["max"] == 100
        assert control.props["value"] == 50

    def test_dropdown_defaults(self):
        """Test that dropdowns get proper defaults and CSS class."""
        controls_spec = [
            {"name": "test_dropdown", "type": "dropdown", "options": ["A", "B", "C"]}
        ]

        controls = build_controls_from_spec(controls_spec)

        assert "test_dropdown" in controls
        control = controls["test_dropdown"]

        # Check col_props default for dropdown
        assert control.col_props == {"xs": 12, "md": 4}

        # Check CSS class is added
        assert control.props["className"] == "compact-dropdown"

        # Check options are normalized
        expected_options = [
            {"label": "A", "value": "A"},
            {"label": "B", "value": "B"},
            {"label": "C", "value": "C"},
        ]
        assert control.props["options"] == expected_options

    def test_input_defaults(self):
        """Test that inputs get proper defaults."""
        controls_spec = [
            {"name": "test_input", "type": "input", "placeholder": "Enter value"}
        ]

        controls = build_controls_from_spec(controls_spec)

        assert "test_input" in controls
        control = controls["test_input"]

        # Check col_props default for input (should be auto)
        assert control.col_props == {"xs": 12, "md": "auto"}

        # Check no CSS class is added for input
        assert "className" not in control.props

    def test_explicit_col_props_override(self):
        """Test that explicit col_props override defaults."""
        controls_spec = [
            {"name": "test_slider", "type": "slider", "col_props": {"xs": 6, "md": 8}}
        ]

        controls = build_controls_from_spec(controls_spec)

        control = controls["test_slider"]
        assert control.col_props == {"xs": 6, "md": 8}

    def test_explicit_classname_override(self):
        """Test that explicit className overrides default CSS class."""
        controls_spec = [
            {"name": "test_slider", "type": "slider", "className": "custom-slider"}
        ]

        controls = build_controls_from_spec(controls_spec)

        control = controls["test_slider"]
        assert control.props["className"] == "custom-slider"

    def test_empty_spec_returns_empty_dict(self):
        """Test that empty or None spec returns empty dict."""
        assert build_controls_from_spec([]) == {}
        assert build_controls_from_spec(None) == {}

    def test_missing_required_fields_raises_error(self):
        """Test that missing required fields raise ValueError."""
        with pytest.raises(ValueError, match="'name' is required"):
            build_controls_from_spec([{"type": "slider"}])

        with pytest.raises(ValueError, match="'type' is required"):
            build_controls_from_spec([{"name": "test"}])

    def test_unknown_control_type_raises_error(self):
        """Test that unknown control types raise ValueError."""
        with pytest.raises(ValueError, match="unknown type 'unknown'"):
            build_controls_from_spec([{"name": "test", "type": "unknown"}])

    def test_dep_param_name_extraction(self):
        """Test that dep_param_name is correctly extracted and stored in Control objects."""
        controls_spec = [
            {
                "name": "test_slider",
                "type": "slider",
                "dep_param_name": "transform__window_step",
            },
            {
                "name": "test_dropdown",
                "type": "dropdown",
                "options": ["A", "B"],
                "dep_param_name": "build__category",
            },
            {
                "name": "test_input",
                "type": "input",
                "dep_param_name": None,  # Explicit None
            },
        ]

        controls = build_controls_from_spec(controls_spec)

        # Check slider
        slider = controls["test_slider"]
        assert slider.dep_param_name == "transform__window_step"

        # Check dropdown
        dropdown = controls["test_dropdown"]
        assert dropdown.dep_param_name == "build__category"

        # Check input (None should be stored as None)
        input_control = controls["test_input"]
        assert input_control.dep_param_name is None

    def test_dep_param_name_optional(self):
        """Test that dep_param_name is optional and defaults to None."""
        controls_spec = [
            {
                "name": "test_slider",
                "type": "slider",
                # No dep_param_name specified
            }
        ]

        controls = build_controls_from_spec(controls_spec)
        control = controls["test_slider"]
        assert control.dep_param_name is None
