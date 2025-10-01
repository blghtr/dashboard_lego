"""
Tests for ThemeConfig system.

:hierarchy: [Tests | Core | Theme Config]
:covers:
 - object: "ThemeConfig with predefined themes and customization"
 - requirement: "Phase 4: Theme system should provide consistent styling"

:scenario: "Verifies that ThemeConfig provides consistent theming across components."
:strategy: "Uses pytest to test ThemeConfig creation, predefined themes, and component styling."
:contract:
 - pre: "ThemeConfig is created with theme parameters"
 - post: "Theme provides consistent styling for all components"

"""

import pytest

from dashboard_lego.core.theme import ColorScheme, Spacing, ThemeConfig, Typography


class TestColorScheme:
    """Test ColorScheme dataclass."""

    def test_color_scheme_default_values(self):
        """Test ColorScheme with default values."""
        colors = ColorScheme()

        assert colors.primary == "#007bff"
        assert colors.secondary == "#6c757d"
        assert colors.success == "#28a745"
        assert colors.danger == "#dc3545"
        assert colors.warning == "#ffc107"
        assert colors.info == "#17a2b8"
        assert colors.background == "#ffffff"
        assert colors.text_primary == "#212529"

    def test_color_scheme_custom_values(self):
        """Test ColorScheme with custom values."""
        colors = ColorScheme(
            primary="#ff0000",
            secondary="#00ff00",
            background="#000000",
            text_primary="#ffffff",
        )

        assert colors.primary == "#ff0000"
        assert colors.secondary == "#00ff00"
        assert colors.background == "#000000"
        assert colors.text_primary == "#ffffff"
        # Other values should remain default
        assert colors.success == "#28a745"


class TestTypography:
    """Test Typography dataclass."""

    def test_typography_default_values(self):
        """Test Typography with default values."""
        typography = Typography()

        assert (
            typography.font_family == "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
        )
        assert typography.font_size_base == "14px"
        assert typography.font_size_h1 == "2.5rem"
        assert typography.font_weight_normal == "400"
        assert typography.line_height_base == "1.5"

    def test_typography_custom_values(self):
        """Test Typography with custom values."""
        typography = Typography(
            font_family="Arial, sans-serif",
            font_size_base="16px",
            font_weight_bold="600",
        )

        assert typography.font_family == "Arial, sans-serif"
        assert typography.font_size_base == "16px"
        assert typography.font_weight_bold == "600"
        # Other values should remain default
        assert typography.font_size_h1 == "2.5rem"


class TestSpacing:
    """Test Spacing dataclass."""

    def test_spacing_default_values(self):
        """Test Spacing with default values."""
        spacing = Spacing()

        assert spacing.base_unit == "0.25rem"
        assert spacing.xs == "0.25rem"
        assert spacing.sm == "0.5rem"
        assert spacing.md == "1rem"
        assert spacing.lg == "1.5rem"
        assert spacing.xl == "3rem"
        assert spacing.border_radius == "0.375rem"

    def test_spacing_custom_values(self):
        """Test Spacing with custom values."""
        spacing = Spacing(base_unit="0.5rem", md="2rem", border_radius="1rem")

        assert spacing.base_unit == "0.5rem"
        assert spacing.md == "2rem"
        assert spacing.border_radius == "1rem"
        # Other values should remain default
        assert spacing.xs == "0.25rem"


class TestThemeConfig:
    """Test ThemeConfig class."""

    def test_theme_config_default_initialization(self):
        """Test ThemeConfig with default initialization."""
        theme = ThemeConfig()

        assert theme.name == "default"
        assert isinstance(theme.colors, ColorScheme)
        assert isinstance(theme.typography, Typography)
        assert isinstance(theme.spacing, Spacing)

    def test_theme_config_custom_initialization(self):
        """Test ThemeConfig with custom components."""
        colors = ColorScheme(primary="#ff0000")
        typography = Typography(font_size_base="16px")
        spacing = Spacing(md="2rem")

        theme = ThemeConfig(
            name="custom", colors=colors, typography=typography, spacing=spacing
        )

        assert theme.name == "custom"
        assert theme.colors.primary == "#ff0000"
        assert theme.typography.font_size_base == "16px"
        assert theme.spacing.md == "2rem"

    def test_light_theme_creation(self):
        """Test light theme creation."""
        theme = ThemeConfig.light_theme()

        assert theme.name == "light"
        assert theme.colors.background == "#ffffff"
        assert theme.colors.text_primary == "#212529"
        assert theme.colors.primary == "#007bff"

    def test_dark_theme_creation(self):
        """Test dark theme creation."""
        theme = ThemeConfig.dark_theme()

        assert theme.name == "dark"
        assert theme.colors.background == "#212529"
        assert theme.colors.text_primary == "#ffffff"
        assert theme.colors.primary == "#0d6efd"

    def test_custom_theme_creation(self):
        """Test custom theme creation."""
        colors = ColorScheme(primary="#purple")
        typography = Typography(font_family="monospace")

        theme = ThemeConfig.custom_theme(
            name="purple_mono", colors=colors, typography=typography
        )

        assert theme.name == "purple_mono"
        assert theme.colors.primary == "#purple"
        assert theme.typography.font_family == "monospace"
        # Spacing should use defaults
        assert isinstance(theme.spacing, Spacing)

    def test_get_component_style_card(self):
        """Test getting card component styles."""
        theme = ThemeConfig.light_theme()

        background_style = theme.get_component_style("card", "background")
        title_style = theme.get_component_style("card", "title")

        assert "backgroundColor" in background_style
        assert "border" in background_style
        assert "borderRadius" in background_style
        assert "padding" in background_style

        assert "color" in title_style
        assert "fontSize" in title_style
        assert "fontWeight" in title_style

    def test_get_component_style_kpi(self):
        """Test getting KPI component styles."""
        theme = ThemeConfig.light_theme()

        container_style = theme.get_component_style("kpi", "container")
        card_style = theme.get_component_style("kpi", "card")
        value_style = theme.get_component_style("kpi", "value")
        title_style = theme.get_component_style("kpi", "title")

        assert "backgroundColor" in container_style
        assert "backgroundColor" in card_style
        assert "color" in value_style
        assert "fontSize" in value_style
        assert "color" in title_style

    def test_get_component_style_navigation(self):
        """Test getting navigation component styles."""
        theme = ThemeConfig.light_theme()

        sidebar_style = theme.get_component_style("navigation", "sidebar")
        content_style = theme.get_component_style("navigation", "content")
        link_style = theme.get_component_style("navigation", "link")
        link_active_style = theme.get_component_style("navigation", "link_active")

        assert "backgroundColor" in sidebar_style
        assert "color" in sidebar_style
        assert "backgroundColor" in content_style
        assert "color" in link_style
        assert "backgroundColor" in link_active_style

    def test_get_component_style_unknown(self):
        """Test getting styles for unknown component/element."""
        theme = ThemeConfig.light_theme()

        unknown_style = theme.get_component_style("unknown", "element")
        assert unknown_style == {}

    def test_to_css_variables(self):
        """Test conversion to CSS variables."""
        theme = ThemeConfig.light_theme()

        css_vars = theme.to_css_variables()

        assert "--theme-primary" in css_vars
        assert "--theme-secondary" in css_vars
        assert "--theme-background" in css_vars
        assert "--theme-text-primary" in css_vars
        assert "--theme-font-family" in css_vars
        assert "--theme-font-size-base" in css_vars
        assert "--theme-spacing-md" in css_vars
        assert "--theme-border-radius" in css_vars

        # Check that values match theme
        assert css_vars["--theme-primary"] == theme.colors.primary
        assert css_vars["--theme-background"] == theme.colors.background
        assert css_vars["--theme-font-family"] == theme.typography.font_family

    def test_theme_consistency(self):
        """Test that theme provides consistent styling."""
        light_theme = ThemeConfig.light_theme()
        dark_theme = ThemeConfig.dark_theme()

        # Light theme should have light background
        assert light_theme.colors.background == "#ffffff"
        assert light_theme.colors.text_primary == "#212529"

        # Dark theme should have dark background
        assert dark_theme.colors.background == "#212529"
        assert dark_theme.colors.text_primary == "#ffffff"

        # Both should have same structure
        assert hasattr(light_theme.colors, "primary")
        assert hasattr(dark_theme.colors, "primary")
        assert hasattr(light_theme.typography, "font_family")
        assert hasattr(dark_theme.typography, "font_family")
        assert hasattr(light_theme.spacing, "md")
        assert hasattr(dark_theme.spacing, "md")
