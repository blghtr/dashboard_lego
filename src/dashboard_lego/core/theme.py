"""
Theme configuration system for Dashboard Lego.

This module provides ThemeConfig for global styling customization across
all dashboard components.

:hierarchy: [Feature | Theme System | ThemeConfig]
:relates-to:
 - motivated_by: "PRD: Provide consistent theming across all dashboard components"
 - implements: "class: 'ThemeConfig' with predefined themes"
 - uses: ["dataclass: 'ThemeConfig'"]

:rationale: "Uses dataclass approach for simplicity and type safety while providing
 comprehensive theming capabilities."
:contract:
 - pre: "ThemeConfig is initialized with theme parameters"
 - post: "All dashboard components can access consistent styling"

"""

from dataclasses import dataclass
from typing import Any, Dict, Optional

try:
    import dash_bootstrap_components as dbc
    import plotly.graph_objects as go
except ImportError:
    dbc = None
    go = None


@dataclass
class ColorScheme:
    """
    Color scheme definition for a theme.

        :hierarchy: [Feature | Theme System | ColorScheme]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Consistent color schemes improve UX"
         - implements: "dataclass: 'ColorScheme'"
         - uses: ["dataclass: 'ColorScheme'"]

        :rationale: "Encapsulates all color definitions in a structured way."
        :contract:
         - pre: "Color values are provided as hex strings or CSS color names"
         - post: "Color scheme provides consistent colors across components"

    """

    # Primary colors
    primary: str = "#007bff"
    secondary: str = "#6c757d"
    success: str = "#28a745"
    danger: str = "#dc3545"
    warning: str = "#ffc107"
    info: str = "#17a2b8"

    # Neutral colors
    light: str = "#f8f9fa"
    dark: str = "#343a40"
    white: str = "#ffffff"
    black: str = "#000000"

    # Background colors
    background: str = "#ffffff"
    surface: str = "#f8f9fa"
    card_background: str = "#ffffff"

    # Text colors
    text_primary: str = "#212529"
    text_secondary: str = "#6c757d"
    text_muted: str = "#6c757d"

    # Border colors
    border: str = "#dee2e6"
    border_light: str = "#e9ecef"

    # Navigation colors
    nav_background: str = "#2c3e50"
    nav_text: str = "#ecf0f1"
    nav_active: str = "#3498db"
    nav_hover: str = "#34495e"


@dataclass
class Typography:
    """
    Typography settings for a theme.

        :hierarchy: [Feature | Theme System | Typography]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Consistent typography improves readability"
         - implements: "dataclass: 'Typography'"
         - uses: ["dataclass: 'Typography'"]

        :rationale: "Centralizes all typography settings for consistency."
        :contract:
         - pre: "Font families and sizes are provided as CSS values"
         - post: "Typography provides consistent text styling across components"

    """

    # Font families
    font_family: str = "'Segoe UI', Tahoma, Geneva, Verdana, sans-serif"
    font_family_mono: str = "'Courier New', Courier, monospace"

    # Font sizes
    font_size_base: str = "14px"
    font_size_sm: str = "12px"
    font_size_lg: str = "16px"
    font_size_xl: str = "18px"
    font_size_h1: str = "2.5rem"
    font_size_h2: str = "2rem"
    font_size_h3: str = "1.75rem"
    font_size_h4: str = "1.5rem"
    font_size_h5: str = "1.25rem"
    font_size_h6: str = "1rem"

    # Font weights
    font_weight_normal: str = "400"
    font_weight_bold: str = "700"
    font_weight_light: str = "300"

    # Line heights
    line_height_base: str = "1.5"
    line_height_sm: str = "1.25"
    line_height_lg: str = "2"


@dataclass
class Spacing:
    """
    Spacing settings for a theme.

        :hierarchy: [Feature | Theme System | Spacing]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Consistent spacing improves visual hierarchy"
         - implements: "dataclass: 'Spacing'"
         - uses: ["dataclass: 'Spacing'"]

        :rationale: "Provides consistent spacing values across all components."
        :contract:
         - pre: "Spacing values are provided as CSS units"
         - post: "Spacing provides consistent layout spacing"

    """

    # Base spacing unit
    base_unit: str = "0.25rem"  # 4px

    # Spacing scale
    xs: str = "0.25rem"  # 4px
    sm: str = "0.5rem"  # 8px
    md: str = "1rem"  # 16px
    lg: str = "1.5rem"  # 24px
    xl: str = "3rem"  # 48px

    # Component-specific spacing
    card_padding: str = "1.5rem"
    button_padding: str = "0.75rem 1.5rem"
    input_padding: str = "0.5rem 0.75rem"

    # Border radius
    border_radius: str = "0.375rem"
    border_radius_sm: str = "0.25rem"
    border_radius_lg: str = "0.5rem"
    border_radius_xl: str = "1rem"


@dataclass
class ThemeConfig:
    """
    Complete theme configuration for Dashboard Lego.

        :hierarchy: [Feature | Theme System | ThemeConfig]
        :relates-to:
         - motivated_by: "PRD: Provide comprehensive theming system for dashboard customization"
         - implements: "dataclass: 'ThemeConfig' with predefined themes"
         - uses: ["dataclass: 'ColorScheme'", "dataclass: 'Typography'", "dataclass: 'Spacing'"]

        :rationale: "Combines color schemes, typography, and spacing into a cohesive theme system."
        :contract:
         - pre: "Theme components are provided or defaults are used"
         - post: "Theme provides complete styling configuration for all components"

    """

    name: str = "default"
    colors: ColorScheme = None
    typography: Typography = None
    spacing: Spacing = None

    def __post_init__(self):
        """Initialize default values if not provided."""
        if self.colors is None:
            self.colors = ColorScheme()
        if self.typography is None:
            self.typography = Typography()
        if self.spacing is None:
            self.spacing = Spacing()

    @classmethod
    def light_theme(cls) -> "ThemeConfig":
        """
        Create a light theme configuration.

            :hierarchy: [Feature | Theme System | Light Theme]
            :relates-to:
             - motivated_by: "PRD: Provide light theme for standard dashboards"
             - implements: "classmethod: 'light_theme'"
             - uses: ["class: 'ThemeConfig'"]

            :rationale: "Provides a clean, professional light theme suitable for most use cases."
            :contract:
             - pre: "No parameters required"
             - post: "Returns ThemeConfig with light color scheme"

        """
        colors = ColorScheme(
            primary="#007bff",
            secondary="#6c757d",
            success="#28a745",
            danger="#dc3545",
            warning="#ffc107",
            info="#17a2b8",
            background="#ffffff",
            surface="#f8f9fa",
            card_background="#ffffff",
            text_primary="#212529",
            text_secondary="#6c757d",
            text_muted="#6c757d",
            border="#dee2e6",
            border_light="#e9ecef",
            nav_background="#2c3e50",
            nav_text="#ecf0f1",
            nav_active="#3498db",
            nav_hover="#34495e",
        )

        return cls(
            name="light", colors=colors, typography=Typography(), spacing=Spacing()
        )

    @classmethod
    def dark_theme(cls) -> "ThemeConfig":
        """
        Create a dark theme configuration.

            :hierarchy: [Feature | Theme System | Dark Theme]
            :relates-to:
             - motivated_by: "PRD: Provide dark theme for modern dashboards"
             - implements: "classmethod: 'dark_theme'"
             - uses: ["class: 'ThemeConfig'"]

            :rationale: "Provides a modern dark theme suitable for data-heavy dashboards."
            :contract:
             - pre: "No parameters required"
             - post: "Returns ThemeConfig with dark color scheme"

        """
        colors = ColorScheme(
            primary="#0d6efd",
            secondary="#6c757d",
            success="#198754",
            danger="#dc3545",
            warning="#ffc107",
            info="#0dcaf0",
            background="#212529",
            surface="#343a40",
            card_background="#495057",
            text_primary="#ffffff",
            text_secondary="#adb5bd",
            text_muted="#6c757d",
            border="#495057",
            border_light="#6c757d",
            nav_background="#1a1a1a",
            nav_text="#ffffff",
            nav_active="#0d6efd",
            nav_hover="#2d2d2d",
        )

        return cls(
            name="dark", colors=colors, typography=Typography(), spacing=Spacing()
        )

    @classmethod
    def custom_theme(
        cls,
        name: str,
        colors: Optional[ColorScheme] = None,
        typography: Optional[Typography] = None,
        spacing: Optional[Spacing] = None,
    ) -> "ThemeConfig":
        """
        Create a custom theme configuration.

            :hierarchy: [Feature | Theme System | Custom Theme]
            :relates-to:
             - motivated_by: "PRD: Allow users to create custom themes"
             - implements: "classmethod: 'custom_theme'"
             - uses: ["class: 'ThemeConfig'"]

            :rationale: "Provides flexibility for users to create their own themes."
            :contract:
             - pre: "Theme name is provided, other parameters are optional"
             - post: "Returns ThemeConfig with custom or default values"

        """
        return cls(
            name=name,
            colors=colors or ColorScheme(),
            typography=typography or Typography(),
            spacing=spacing or Spacing(),
        )

    def get_component_style(self, component_type: str, element: str) -> Dict[str, Any]:
        """
        Get style dictionary for a specific component and element.

            :hierarchy: [Feature | Theme System | Component Style]
            :relates-to:
             - motivated_by: "Architectural Conclusion: Components need theme-based styling"
             - implements: "method: 'get_component_style'"
             - uses: ["dataclass: 'ThemeConfig'"]

            :rationale: "Provides centralized access to component-specific styling."
            :contract:
             - pre: "Component type and element are specified"
             - post: "Returns style dictionary with theme values"

        """
        styles = {
            "card": {
                "background": {
                    "backgroundColor": self.colors.card_background,
                    "border": f"1px solid {self.colors.border}",
                    "borderRadius": self.spacing.border_radius,
                    "padding": self.spacing.card_padding,
                    "boxShadow": "0 2px 4px rgba(0,0,0,0.1)",
                },
                "title": {
                    "color": self.colors.text_primary,
                    "fontSize": self.typography.font_size_h4,
                    "fontWeight": self.typography.font_weight_bold,
                    "marginBottom": self.spacing.md,
                },
            },
            "kpi": {
                "container": {
                    "backgroundColor": self.colors.background,
                    "padding": self.spacing.md,
                },
                "card": {
                    "backgroundColor": self.colors.card_background,
                    "border": f"1px solid {self.colors.border}",
                    "borderRadius": self.spacing.border_radius,
                    "padding": self.spacing.card_padding,
                    "textAlign": "center",
                },
                "value": {
                    "color": self.colors.primary,
                    "fontSize": self.typography.font_size_h2,
                    "fontWeight": self.typography.font_weight_bold,
                },
                "title": {
                    "color": self.colors.text_secondary,
                    "fontSize": self.typography.font_size_sm,
                    "marginTop": self.spacing.sm,
                },
            },
            "navigation": {
                "sidebar": {
                    "backgroundColor": self.colors.nav_background,
                    "color": self.colors.nav_text,
                    "padding": self.spacing.lg,
                },
                "content": {
                    "backgroundColor": self.colors.surface,
                    "padding": self.spacing.lg,
                },
                "link": {
                    "color": self.colors.nav_text,
                    "padding": self.spacing.md,
                    "borderRadius": self.spacing.border_radius,
                    "textDecoration": "none",
                },
                "link_active": {
                    "backgroundColor": self.colors.nav_active,
                    "color": self.colors.white,
                },
            },
            "body": {
                "main": {
                    "backgroundColor": self.colors.background,
                    "color": self.colors.text_primary,
                    "fontFamily": self.typography.font_family,
                    "margin": "0",
                    "padding": "0",
                },
            },
        }

        return styles.get(component_type, {}).get(element, {})

    def to_css_variables(self) -> Dict[str, str]:
        """
        Convert theme to CSS custom properties.

            :hierarchy: [Feature | Theme System | CSS Variables]
            :relates-to:
             - motivated_by: "Architectural Conclusion: CSS variables enable dynamic theming"
             - implements: "method: 'to_css_variables'"
             - uses: ["dataclass: 'ThemeConfig'"]

            :rationale: "Provides CSS variables for dynamic theme switching."
            :contract:
             - pre: "Theme is fully configured"
             - post: "Returns dictionary of CSS custom properties"

        """
        return {
            # Colors
            "--theme-primary": self.colors.primary,
            "--theme-secondary": self.colors.secondary,
            "--theme-success": self.colors.success,
            "--theme-danger": self.colors.danger,
            "--theme-warning": self.colors.warning,
            "--theme-info": self.colors.info,
            "--theme-background": self.colors.background,
            "--theme-surface": self.colors.surface,
            "--theme-card-background": self.colors.card_background,
            "--theme-text-primary": self.colors.text_primary,
            "--theme-text-secondary": self.colors.text_secondary,
            "--theme-border": self.colors.border,
            "--theme-white": self.colors.white,
            # Navigation colors
            "--theme-nav-text": self.colors.nav_text,
            "--theme-nav-background": self.colors.nav_background,
            "--theme-nav-active": self.colors.nav_active,
            "--theme-nav-hover": self.colors.nav_hover,
            # Typography
            "--theme-font-family": self.typography.font_family,
            "--theme-font-size-base": self.typography.font_size_base,
            "--theme-font-weight-normal": self.typography.font_weight_normal,
            "--theme-line-height-base": self.typography.line_height_base,
            # Spacing
            "--theme-spacing-xs": self.spacing.xs,
            "--theme-spacing-sm": self.spacing.sm,
            "--theme-spacing-md": self.spacing.md,
            "--theme-spacing-lg": self.spacing.lg,
            "--theme-border-radius": self.spacing.border_radius,
        }

    def get_plotly_template(self) -> Dict[str, Any]:
        """
        Returns Plotly template dict with theme colors.

            :hierarchy: [Feature | Theme System | Plotly Template]
            :relates-to:
             - motivated_by: "PRD: Apply theme colors to Plotly figures automatically"
             - implements: "method: 'get_plotly_template'"
             - uses: ["dataclass: 'ThemeConfig'"]

            :rationale: "Provides Plotly template that matches theme colors."
            :contract:
             - pre: "Theme is fully configured"
             - post: "Returns Plotly template dictionary"

        Returns:
            Dictionary with Plotly template configuration
        """
        return {
            "layout": {
                "colorway": [
                    self.colors.primary,
                    self.colors.secondary,
                    self.colors.success,
                    self.colors.info,
                    self.colors.warning,
                    self.colors.danger,
                ],
                "font": {
                    "color": self.colors.text_primary,
                    "family": self.typography.font_family,
                },
                "paper_bgcolor": self.colors.background,
                "plot_bgcolor": self.colors.surface,
            }
        }

    def get_figure_layout(self) -> Dict[str, Any]:
        """
        Returns default figure layout with theme styling.

            :hierarchy: [Feature | Theme System | Figure Layout]
            :relates-to:
             - motivated_by: "PRD: Consistent figure styling across all charts"
             - implements: "method: 'get_figure_layout'"
             - uses: ["dataclass: 'ThemeConfig'"]

            :rationale: "Provides default layout settings that match theme."
            :contract:
             - pre: "Theme is fully configured"
             - post: "Returns layout dictionary for Plotly figures"

        Returns:
            Dictionary with default layout settings
        """
        return {
            "font": {
                "color": self.colors.text_primary,
                "family": self.typography.font_family,
            },
            "paper_bgcolor": self.colors.background,
            "plot_bgcolor": self.colors.surface,
            "xaxis": {
                "gridcolor": self.colors.border_light,
                "linecolor": self.colors.border,
                "tickcolor": self.colors.border,
            },
            "yaxis": {
                "gridcolor": self.colors.border_light,
                "linecolor": self.colors.border,
                "tickcolor": self.colors.border,
            },
        }

    def apply_to_figure(self, fig) -> Any:
        """
        Applies theme to existing Plotly figure.

            :hierarchy: [Feature | Theme System | Apply Theme to Figure]
            :relates-to:
             - motivated_by: "PRD: Easy theme application to existing figures"
             - implements: "method: 'apply_to_figure'"
             - uses: ["dataclass: 'ThemeConfig'"]

            :rationale: "Provides method to apply theme styling to any figure."
            :contract:
             - pre: "fig is a valid Plotly Figure object"
             - post: "Returns figure with theme styling applied"

        Args:
            fig: Plotly Figure object to apply theme to

        Returns:
            The same figure with theme styling applied
        """
        if go is None:
            return fig

        layout_updates = self.get_figure_layout()
        fig.update_layout(**layout_updates)
        return fig

    @classmethod
    def from_dbc_theme(cls, theme_url: str) -> "ThemeConfig":
        """
        Create ThemeConfig automatically from dash-bootstrap-components theme URL.

            :hierarchy: [Feature | Theme System | DBC Theme Mapping]
            :relates-to:
             - motivated_by: "PRD: Automatically derive ThemeConfig from dbc.themes"
             - implements: "classmethod: 'from_dbc_theme'"
             - uses: ["dict: 'DBC_THEME_MAPPING'"]

            :rationale: "Maps dbc theme URLs to appropriate ColorScheme configurations."
            :contract:
             - pre: "theme_url is a valid dbc.themes URL or None"
             - post: "Returns ThemeConfig matching the dbc theme"

        Args:
            theme_url: URL of the dbc theme (e.g., dbc.themes.CYBORG)

        Returns:
            ThemeConfig configured to match the dbc theme
        """
        # Get the mapping, fallback to light theme if not found
        theme_mapping = _get_dbc_theme_mapping()

        if theme_url in theme_mapping:
            colors = theme_mapping[theme_url]
            # Extract theme name from URL
            theme_name = theme_url.split("/")[-1].replace(".min.css", "").lower()
            return cls(
                name=theme_name,
                colors=colors,
                typography=Typography(),
                spacing=Spacing(),
            )
        else:
            # Default to light theme for unknown themes
            return cls.light_theme()


def _get_dbc_theme_mapping() -> Dict[str, ColorScheme]:
    """
    Returns mapping of dbc.themes URLs to ColorScheme configurations.

        :hierarchy: [Feature | Theme System | DBC Theme Mapping]
        :relates-to:
         - motivated_by: "PRD: Map all popular dbc themes to color schemes"
         - implements: "function: '_get_dbc_theme_mapping'"
         - uses: ["dataclass: 'ColorScheme'"]

        :rationale: "Centralizes theme mapping for maintainability."
        :contract:
         - pre: "dbc is imported"
         - post: "Returns dictionary mapping theme URLs to ColorSchemes"

    Returns:
        Dictionary mapping dbc theme URLs to ColorScheme objects
    """
    if dbc is None:
        return {}

    return {
        # BOOTSTRAP - Default Bootstrap 5 theme (light)
        dbc.themes.BOOTSTRAP: ColorScheme(
            primary="#0d6efd",
            secondary="#6c757d",
            success="#198754",
            danger="#dc3545",
            warning="#ffc107",
            info="#0dcaf0",
            background="#ffffff",
            surface="#f8f9fa",
            card_background="#ffffff",
            text_primary="#212529",
            text_secondary="#6c757d",
            text_muted="#6c757d",
            border="#dee2e6",
            border_light="#e9ecef",
            nav_background="#2c3e50",
            nav_text="#ecf0f1",
            nav_active="#0d6efd",
            nav_hover="#34495e",
        ),
        # CYBORG - Dark cyberpunk theme
        dbc.themes.CYBORG: ColorScheme(
            primary="#2a9fd6",
            secondary="#555555",
            success="#77b300",
            danger="#cc0000",
            warning="#ff8800",
            info="#9933cc",
            background="#060606",
            surface="#222222",
            card_background="#222222",
            text_primary="#ffffff",
            text_secondary="#adafae",
            text_muted="#888888",
            border="#282828",
            border_light="#3f3f3f",
            nav_background="#111111",
            nav_text="#ffffff",
            nav_active="#2a9fd6",
            nav_hover="#1a1a1a",
        ),
        # DARKLY - Dark theme
        dbc.themes.DARKLY: ColorScheme(
            primary="#375a7f",
            secondary="#444444",
            success="#00bc8c",
            danger="#e74c3c",
            warning="#f39c12",
            info="#3498db",
            background="#222222",
            surface="#303030",
            card_background="#303030",
            text_primary="#ffffff",
            text_secondary="#adb5bd",
            text_muted="#888888",
            border="#444444",
            border_light="#555555",
            nav_background="#1a1a1a",
            nav_text="#ffffff",
            nav_active="#375a7f",
            nav_hover="#2d2d2d",
        ),
        # FLATLY - Flat and modern (light)
        dbc.themes.FLATLY: ColorScheme(
            primary="#2c3e50",
            secondary="#95a5a6",
            success="#18bc9c",
            danger="#e74c3c",
            warning="#f39c12",
            info="#3498db",
            background="#ffffff",
            surface="#ecf0f1",
            card_background="#ffffff",
            text_primary="#2c3e50",
            text_secondary="#7b8a8b",
            text_muted="#95a5a6",
            border="#dee2e6",
            border_light="#e9ecef",
            nav_background="#2c3e50",
            nav_text="#ffffff",
            nav_active="#18bc9c",
            nav_hover="#34495e",
        ),
        # LUX - Luxurious light theme
        dbc.themes.LUX: ColorScheme(
            primary="#1a1a1a",
            secondary="#919aa1",
            success="#28a745",
            danger="#d9534f",
            warning="#f8b500",
            info="#3498db",
            background="#ffffff",
            surface="#f8f9fa",
            card_background="#ffffff",
            text_primary="#1a1a1a",
            text_secondary="#6c757d",
            text_muted="#919aa1",
            border="#dee2e6",
            border_light="#e9ecef",
            nav_background="#1a1a1a",
            nav_text="#ffffff",
            nav_active="#f8b500",
            nav_hover="#333333",
        ),
        # SLATE - Dark slate theme
        dbc.themes.SLATE: ColorScheme(
            primary="#7a8288",
            secondary="#3a3f44",
            success="#62c462",
            danger="#ee5f5b",
            warning="#f89406",
            info="#5bc0de",
            background="#272b30",
            surface="#3a3f44",
            card_background="#3a3f44",
            text_primary="#c8c8c8",
            text_secondary="#adb5bd",
            text_muted="#888888",
            border="#52575c",
            border_light="#5e6366",
            nav_background="#1f2227",
            nav_text="#c8c8c8",
            nav_active="#7a8288",
            nav_hover="#2d3238",
        ),
        # SOLAR - Solarized theme
        dbc.themes.SOLAR: ColorScheme(
            primary="#b58900",
            secondary="#839496",
            success="#859900",
            danger="#dc322f",
            warning="#cb4b16",
            info="#268bd2",
            background="#002b36",
            surface="#073642",
            card_background="#073642",
            text_primary="#839496",
            text_secondary="#93a1a1",
            text_muted="#586e75",
            border="#094252",
            border_light="#0f5866",
            nav_background="#001f27",
            nav_text="#839496",
            nav_active="#b58900",
            nav_hover="#003642",
        ),
        # SUPERHERO - Dark superhero theme
        dbc.themes.SUPERHERO: ColorScheme(
            primary="#4c9be8",
            secondary="#4e5d6c",
            success="#5cb85c",
            danger="#d9534f",
            warning="#f0ad4e",
            info="#5bc0de",
            background="#0f2537",
            surface="#20374c",
            card_background="#20374c",
            text_primary="#ebebeb",
            text_secondary="#adb5bd",
            text_muted="#7a8793",
            border="#2b3e50",
            border_light="#354b60",
            nav_background="#081521",
            nav_text="#ebebeb",
            nav_active="#4c9be8",
            nav_hover="#152839",
        ),
        # COSMO - Cosmopolitan light theme
        dbc.themes.COSMO: ColorScheme(
            primary="#2780e3",
            secondary="#8f8f8f",
            success="#3fb618",
            danger="#ff0039",
            warning="#ff7518",
            info="#9954bb",
            background="#ffffff",
            surface="#f8f9fa",
            card_background="#ffffff",
            text_primary="#212529",
            text_secondary="#6c757d",
            text_muted="#8f8f8f",
            border="#dee2e6",
            border_light="#e9ecef",
            nav_background="#2780e3",
            nav_text="#ffffff",
            nav_active="#1a6bc9",
            nav_hover="#3091f5",
        ),
        # VAPOR - Vaporwave theme
        dbc.themes.VAPOR: ColorScheme(
            primary="#f44e8f",
            secondary="#4c00e2",
            success="#00f0ff",
            danger="#ea00a4",
            warning="#ff9a00",
            info="#6c5ce7",
            background="#19002b",
            surface="#2a0845",
            card_background="#2a0845",
            text_primary="#f0e7ff",
            text_secondary="#c5b3d9",
            text_muted="#9884ad",
            border="#3d1559",
            border_light="#4a1a68",
            nav_background="#0d0015",
            nav_text="#f0e7ff",
            nav_active="#f44e8f",
            nav_hover="#1f0033",
        ),
    }
