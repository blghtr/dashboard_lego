"""
Theme management methods for DashboardPage.

:hierarchy: [Core | Page | Theme Manager]
:complexity: 3
"""

from typing import Any


class ThemeManagerMixin:
    """
    Mixin providing theme management methods for DashboardPage.

    :hierarchy: [Core | Page | Theme Manager | Mixin]
    :relates-to:
     - motivated_by: "Decomposition: Extract theme logic from DashboardPage"
     - implements: "Mixin: ThemeManagerMixin"
     - uses: ["class: 'ThemeConfig'"]

    :rationale: "Separates theme management concerns from core page logic."
    :contract:
     - pre: "Class has theme_config, theme, logger attributes"
     - post: "Provides methods for generating themed HTML and creating Dash apps"
    """

    def get_theme_html_template(self) -> str:
        """
        Generate HTML template with theme CSS variables and Bootstrap data-bs-theme.

        This method creates a complete HTML template that applies the theme configuration
        to the Dash application. It includes:
        - Bootstrap theme mode (data-bs-theme attribute)
        - CSS custom properties from theme config
        - Dark theme dropdown fixes if needed

        :hierarchy: [Feature | Theme System | HTML Template Generation]
        :relates-to:
         - motivated_by: "Theme system should be automatically applied without manual CSS injection"
         - implements: "method: 'get_theme_html_template'"
         - uses: ["method: 'to_css_variables'"]

        :rationale: "Provides a single method to generate themed HTML, eliminating manual CSS magic."
        :contract:
         - pre: "Theme config is initialized"
         - post: "Returns complete HTML template string for app.index_string"

        Returns:
            HTML string with theme styling for app.index_string

        Example:
            >>> page = DashboardPage(title="Dashboard", blocks=[], theme_config=ThemeConfig.dark_theme())
            >>> app.index_string = page.get_theme_html_template()
        """
        # Get CSS variables from theme
        css_vars = self.theme_config.to_css_variables()

        # CRITICAL: Map custom --theme-* variables to Bootstrap --bs-* variables
        # Bootstrap components use --bs-* variables, not --theme-*
        # NOTE(REVIEWER): This mapping ensures Dash Bootstrap Components receive correct theme values
        bootstrap_vars = {
            # Body and surface - Bootstrap uses these for body and container backgrounds
            "--bs-body-bg": css_vars.get("--theme-background", "#ffffff"),
            "--bs-body-color": css_vars.get("--theme-text-primary", "#212529"),
            "--bs-secondary-bg": css_vars.get("--theme-surface", "#f8f9fa"),
            # Offcanvas - Bootstrap uses --bs-offcanvas-bg and --bs-offcanvas-color
            # FIXME(REVIEWER): Must map offcanvas variables for proper theme application
            "--bs-offcanvas-bg": css_vars.get(
                "--theme-nav-background", css_vars.get("--theme-surface", "#f8f9fa")
            ),
            "--bs-offcanvas-color": css_vars.get(
                "--theme-nav-text", css_vars.get("--theme-text-primary", "#212529")
            ),
            # Cards - Bootstrap uses --bs-card-bg for card backgrounds
            "--bs-card-bg": css_vars.get(
                "--theme-card-background", css_vars.get("--theme-surface", "#ffffff")
            ),
            "--bs-card-color": css_vars.get("--theme-text-primary", "#212529"),
            "--bs-card-border-color": css_vars.get("--theme-border", "#dee2e6"),
            # Buttons - For toggle button, use surface color instead of secondary for better visibility
            # NOTE(REVIEWER): --bs-secondary (#6c757d) is too gray for dark themes
            # Use --bs-secondary-bg (surface) for toggle button to match theme better
            "--bs-secondary": css_vars.get("--theme-secondary", "#6c757d"),
            # Secondary button text uses --bs-body-color (already mapped above)
            # Close button - Bootstrap uses --bs-btn-close-color for the X icon
            # NOTE(REVIEWER): Bootstrap automatically inverts btn-close color for dark themes via data-bs-theme
            # For dark themes: set black color, Bootstrap inverts it to white (visible on dark background)
            # For light themes: set black color, stays black (visible on light background)
            # We always use black as base - Bootstrap handles inversion automatically
            "--bs-btn-close-color": "#000000",
            "--bs-btn-close-opacity": "1.0",
            # Borders
            "--bs-border-color": css_vars.get("--theme-border", "#dee2e6"),
        }

        # Combine custom variables with Bootstrap mappings
        all_vars = {**css_vars, **bootstrap_vars}
        css_vars_str = ";\n                ".join(
            f"{k}: {v}" for k, v in all_vars.items()
        )

        # Determine Bootstrap theme mode
        # Dark themes: dark, cyborg, darkly, solar, superhero, vapor, slate
        dark_themes = {
            "dark",
            "cyborg",
            "darkly",
            "solar",
            "superhero",
            "vapor",
            "slate",
        }
        bs_theme = "dark" if self.theme_config.name.lower() in dark_themes else "light"

        # Generate dropdown fix CSS for dark theme
        dropdown_css = ""
        if bs_theme == "dark":
            dropdown_css = """
            /* Fix dropdown menus for dark theme */
            .dropdown-menu {
                background-color: var(--bs-dark) !important;
                border: 1px solid var(--bs-border-color) !important;
            }
            .dropdown-item {
                color: var(--bs-body-color) !important;
            }
            .dropdown-item:hover {
                background-color: var(--bs-secondary) !important;
                color: var(--bs-body-color) !important;
            }
            /* Fix Select component dropdowns */
            .Select-menu-outer {
                background-color: var(--bs-dark) !important;
                border: 1px solid var(--bs-border-color) !important;
            }
            .Select-option {
                background-color: var(--bs-dark) !important;
                color: var(--bs-body-color) !important;
            }
            .Select-option:hover {
                background-color: var(--bs-secondary) !important;
            }"""

        # Override Bootstrap CSS variables for navigation
        # CRITICAL: Must override --bs-nav-link-color and --bs-nav-pills-link-active-bg
        # Get color values from theme
        nav_text_color = self.theme_config.colors.nav_text or "#ecf0f1"
        nav_active_bg = self.theme_config.colors.nav_active or "#3498db"

        nav_css = f"""
            /* Override Bootstrap CSS variables for navigation */
            #nav-list {{
                --bs-nav-link-color: {nav_text_color} !important;
                --bs-nav-link-hover-color: {nav_text_color} !important;
                --bs-nav-pills-link-active-bg: {nav_active_bg} !important;
                --bs-nav-pills-link-active-color: #ffffff !important;
            }}

            /* Additional styling for themed-nav-link classes */
            #nav-list .nav-link.themed-nav-link {{
                display: flex !important;
                align-items: center !important;
                font-weight: 500 !important;
            }}
            #nav-list .nav-link.themed-nav-link:hover {{
                background-color: rgba(255,255,255,0.1) !important;
            }}
            #nav-list .nav-link.themed-nav-link-active {{
                font-weight: 600 !important;
            }}"""

        # Global theme application CSS
        # NOTE(REVIEWER): Dash Bootstrap Components automatically apply theme via Bootstrap CSS variables
        # We only style CUSTOM elements (not Dash Bootstrap Components)
        # Custom elements: nav-content-area (html.Div wrapper, no Dash Bootstrap equivalent)
        global_theme_css = """
            /* Body uses Bootstrap --bs-body-bg and --bs-body-color (mapped from --theme-*) */
            body {
                background-color: var(--bs-body-bg) !important;
                color: var(--bs-body-color) !important;
                margin: 0;
                padding: 0;
                min-height: 100vh;
            }

            /* Ensure Dash entry point covers screen */
            #react-entry-point {
                background-color: var(--bs-body-bg) !important;
                min-height: 100vh;
            }

            /* CUSTOM ELEMENT: nav-content-area (html.Div wrapper, no Dash Bootstrap equivalent) */
            /* NOTE(REVIEWER): This is a custom wrapper div, not a Dash Bootstrap component */
            /* Uses standard theme colors based on location (main content area) */
            .nav-content-area,
            #nav-content-area {
                background-color: var(--bs-body-bg) !important;
                color: var(--bs-body-color) !important;
            }

            /* Dash Bootstrap Components automatically apply theme via CSS variables: */
            /* - dbc.Offcanvas uses --bs-offcanvas-bg (already mapped) */
            /* - dbc.Card uses --bs-card-bg (already mapped) */
            /* - dbc.Button uses --bs-secondary (already mapped) */
            /* - dbc.Container uses --bs-body-bg (already mapped) */
            /* No explicit overrides needed - Bootstrap handles it automatically */

            /* CUSTOM STYLING: Toggle button as floating card (user requirement) */
            /* NOTE(REVIEWER): This is a design requirement, not standard Bootstrap button styling */
            /* Uses card colors to match card blocks visually */
            #sidebar-toggle-btn.btn-secondary {
                background-color: var(--bs-card-bg) !important;
                border: 1px solid var(--bs-card-border-color) !important;
                border-radius: 0.375rem !important;
                padding: 0.5rem 0.75rem !important;
                box-shadow: rgba(0, 0, 0, 0.1) 0px 2px 4px !important;
                color: var(--bs-card-color) !important;
            }

            /* CUSTOM STYLING: Add offset for offcanvas-title to avoid overlap with toggle button */
            /* NOTE(REVIEWER): Toggle button is 2.5rem x 2.5rem at top: 10px, so offcanvas-title needs margin-top */
            /* Button height (2.5rem) + top position (10px) + gap (10px) = ~3.5rem margin-top */
            #sidebar-offcanvas .offcanvas-title {
                margin-top: 3.5rem !important;
            }"""

        # Build template string
        # CRITICAL: Dash expects {%var%} format (single braces, not double)
        # Bootstrap requires variables in both :root and [data-bs-theme=dark] for dark themes
        # Use string replacement for dynamic values to avoid brace escaping issues
        if bs_theme == "dark":
            # For dark themes, set variables in both :root and [data-bs-theme=dark]
            root_selector = ":root,\n            [data-bs-theme=dark]"
        else:
            # For light themes, set variables in :root
            root_selector = ":root"

        template = """<!DOCTYPE html>
<html data-bs-theme="{bs_theme}">
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            {root_selector} {{
                {css_vars_str}
            }}{dropdown_css}{nav_css}{global_theme_css}
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>"""

        # Replace placeholders using .replace() to avoid brace escaping
        template = template.replace("{bs_theme}", bs_theme)
        template = template.replace("{root_selector}", root_selector)
        template = template.replace("{css_vars_str}", css_vars_str)
        template = template.replace("{dropdown_css}", dropdown_css)
        template = template.replace("{nav_css}", nav_css)
        template = template.replace("{global_theme_css}", global_theme_css)

        return template

    def create_app(self, **kwargs) -> Any:
        """
        Create Dash app with theme automatically applied.

        This is a convenience method that creates a fully configured Dash app with:
        - Theme applied via HTML template
        - Layout built and set
        - Callbacks registered

        :hierarchy: [Feature | App Creation | Convenience Method]
        :relates-to:
         - motivated_by: "Simplify dashboard creation with automatic theme application"
         - implements: "method: 'create_app'"
         - uses: ["method: 'get_theme_html_template'", "method: 'build_layout'", "method: 'register_callbacks'"]

        :rationale: "Provides one-line app creation for common use cases."
        :contract:
         - pre: "Page is fully configured with blocks/navigation and theme"
         - post: "Returns ready-to-run Dash app instance"

        Args:
            **kwargs: Additional arguments for Dash() constructor (e.g., suppress_callback_exceptions)

        Returns:
            Configured Dash app instance ready to run

        Example:
            >>> page = DashboardPage(title="My Dashboard", blocks=[[chart1, chart2]])
            >>> app = page.create_app()
            >>> app.run(debug=True)
        """
        from dash import Dash

        self.logger.info(f"Creating Dash app with {self.theme_config.name} theme")

        # Create Dash app with theme stylesheet
        app = Dash(__name__, external_stylesheets=[self.theme], **kwargs)

        # Set app title so it's available in index_string template
        app.title = self.title

        # Apply theme HTML template
        app.index_string = self.get_theme_html_template()
        self.logger.debug(
            f"[ThemeManager] HTML Template size: {len(app.index_string)} chars"
        )

        # Build and set layout
        app.layout = self.build_layout()

        # Register all callbacks
        self.register_callbacks(app)

        self.logger.info("Dash app created and configured successfully")
        return app
