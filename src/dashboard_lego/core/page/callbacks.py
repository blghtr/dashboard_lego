"""
Callback registration methods for DashboardPage.

:hierarchy: [Core | Page | Callbacks]
:complexity: 5
"""

from typing import Any

import dash_bootstrap_components as dbc
from dash import html
from dash.dependencies import Input, Output


class CallbacksMixin:
    """
    Mixin providing callback registration methods for DashboardPage.

    :hierarchy: [Core | Page | Callbacks | Mixin]
    :relates-to:
     - motivated_by: "Decomposition: Extract callback logic from DashboardPage"
     - implements: "Mixin: CallbacksMixin"
     - uses: ["class: 'StateManager'"]

    :rationale: "Separates callback registration concerns from core page logic."
    :contract:
     - pre: "Class has sidebar, navigation, state_manager, logger, blocks, _section_blocks_cache attributes"
     - post: "Provides methods for registering all callbacks with Dash app"
    """

    def register_callbacks(self, app: Any):
        """
        Registers callbacks using both mechanisms.

        CRITICAL: For navigation mode, preloads all sections to satisfy Dash requirement
        that all callbacks must be registered before app.run().

        :hierarchy: [Architecture | Callback Registration | DashboardPage]
        :relates-to:
         - motivated_by: "Dash lifecycle requires all callbacks before app.run()"
         - implements: "method: 'register_callbacks' with preload"
         - uses: ["method: '_preload_all_section_blocks'", "method: 'generate_callbacks'", "method: 'bind_callbacks'"]

        :rationale: "Preload all section blocks before registering callbacks to satisfy Dash requirements."
        :contract:
         - pre: "StateManager is initialized"
         - post: "All callbacks registered before app.run()"

        Args:
            app: The Dash app instance.
        """
        self.logger.info("Registering callbacks with Dash app")

        try:
            # Sidebar-specific callbacks
            if self.sidebar and self.sidebar.collapsible:
                self._register_sidebar_callbacks(app)
                self._register_sidebar_adaptive_layout_callback(app)

            # Navigation-specific callbacks
            if self.navigation:
                self._register_navigation_callbacks(app)

            # Store app reference
            self._app_instance = app

            # Set up error handling
            self._setup_callback_error_handling(app)

            # CRITICAL: For navigation, preload ALL sections before registering callbacks
            # NOTE: Sections may already be preloaded in build_layout() for sidebar mode
            if self.navigation:
                if not hasattr(self, "_sections_preloaded"):
                    self.logger.info(
                        "Preloading sections for callback registration "
                        "(not yet preloaded in build_layout)"
                    )
                    all_blocks = self._preload_all_section_blocks()
                    self._sections_preloaded = True
                else:
                    self.logger.debug(
                        "Using already preloaded sections from build_layout()"
                    )
                    # Collect all blocks from cache
                    all_blocks = []
                    for section_blocks in self._section_blocks_cache.values():
                        all_blocks.extend(section_blocks)

                self.state_manager.generate_callbacks(app, all_blocks)
                self.state_manager.bind_callbacks(app, all_blocks)
            else:
                # Non-navigation mode: standard flow
                self.state_manager.generate_callbacks(app, self.blocks)
                self.state_manager.bind_callbacks(app, self.blocks)

            self.logger.info("Callbacks registered successfully")
        except Exception as e:
            self.logger.error(f"Error registering callbacks: {e}", exc_info=True)
            raise

    def _setup_callback_error_handling(self, app: Any):
        """
        Sets up comprehensive error handling for Dash callbacks.

        :hierarchy: [Architecture | Error Handling | DashboardPage]
        :relates-to:
         - motivated_by: "Bug Fix: Error handling wrapper must preserve original callback registration"
         - implements: "method: '_setup_callback_error_handling'"
         - uses: ["attribute: 'logger'"]

        :rationale: "Wraps callback functions with error handling while preserving Dash's callback registration."
        :contract:
         - pre: "Dash app instance is provided."
         - post: "Callback error handling is configured without breaking callback registration."

        Args:
            app: The Dash app instance.
        """
        from dash.exceptions import PreventUpdate

        # Save the original callback decorator
        original_callback = app.callback

        def enhanced_callback(*args, **kwargs):
            """Enhanced callback decorator that wraps functions with error handling."""

            def decorator(func):
                def wrapper(*callback_args, **callback_kwargs):
                    try:
                        self.logger.debug(
                            f"🎬 Callback '{func.__name__}' triggered with "
                            f"{len(callback_args)} args, {len(callback_kwargs)} kwargs"
                        )
                        result = func(*callback_args, **callback_kwargs)
                        self.logger.debug(
                            f"✅ Callback '{func.__name__}' completed successfully"
                        )
                        return result
                    except PreventUpdate:
                        # Re-raise PreventUpdate as it's intentional
                        self.logger.debug(
                            f"⏭️  Callback '{func.__name__}' prevented update"
                        )
                        raise
                    except Exception as e:
                        # Log the error with context
                        self.logger.error(
                            f"❌ Callback error in function '{func.__name__}': {e}",
                            exc_info=True,
                        )

                        # Try to provide a meaningful error message
                        error_msg = f"Error in callback: {str(e)}"

                        # For figure outputs, return error figure
                        if args and hasattr(args[0], "component_property"):
                            if args[0].component_property == "figure":
                                import plotly.graph_objects as go

                                return go.Figure().update_layout(
                                    title="Callback Error",
                                    annotations=[
                                        dict(
                                            text=error_msg,
                                            xref="paper",
                                            yref="paper",
                                            x=0.5,
                                            y=0.5,
                                            showarrow=False,
                                            font=dict(size=14, color="red"),
                                        )
                                    ],
                                )

                        # For other outputs, return error message
                        return f"Error: {error_msg}"

                # CRITICAL: Call original_callback to actually register with Dash!
                return original_callback(*args, **kwargs)(wrapper)

            return decorator

        # Replace the callback decorator with our wrapper
        app.callback = enhanced_callback

        self.logger.debug("✅ Enhanced callback error handling configured")

    def _register_navigation_callbacks(self, app: Any):
        """
        Registers navigation-specific callbacks for section switching.

        :hierarchy: [Feature | Navigation System | Register Navigation Callbacks]
        :relates-to:
         - motivated_by: "Navigation panel requires interactive section switching"
         - implements: "method: '_register_navigation_callbacks'"
         - uses: ["library: 'dash'", "method: '_create_section_content'"]

        :rationale: "Dynamic callback responds to nav clicks and loads content lazily."
        :contract:
         - pre: "Navigation config exists, app is valid Dash instance"
         - post: "Callback registered to update content area and nav states"

        """
        from dash import callback_context

        @app.callback(
            [
                Output("nav-content-area", "children"),
                Output("active-section-store", "data"),
            ]
            + [
                Output(f"nav-item-{i}", "className")
                for i in range(len(self.navigation.sections))
            ]
            + [
                Output(f"nav-item-{i}", "style")
                for i in range(len(self.navigation.sections))
            ],
            [
                Input(f"nav-item-{i}", "n_clicks")
                for i in range(len(self.navigation.sections))
            ],
        )
        def update_navigation(*n_clicks_list):
            """
            Updates content area and navigation link states on user clicks.

            """
            ctx = callback_context

            self.logger.info("=== Navigation callback fired ===")
            self.logger.info(f"n_clicks values: {n_clicks_list}")
            self.logger.info(f"ctx.triggered: {ctx.triggered}")

            # On initial call (no trigger or prop_id is ".")
            if not ctx.triggered or ctx.triggered[0]["prop_id"] == ".":
                section_idx = self.navigation.default_section
                self.logger.info(f"Initial load: loading default section {section_idx}")
            else:
                # Find which nav item was clicked
                triggered_prop_id = ctx.triggered[0]["prop_id"]
                self.logger.info(f"Callback triggered by: {triggered_prop_id}")

                # Extract clicked item index from triggered id
                if "nav-item-" in triggered_prop_id:
                    item_id = triggered_prop_id.split(".")[0]
                    section_idx = int(item_id.split("-")[-1])
                    self.logger.info(
                        f"✅ Navigation click: switching to section {section_idx}"
                    )
                else:
                    # Fallback to default
                    section_idx = self.navigation.default_section
                    self.logger.warning(
                        f"⚠️ Unknown trigger: {triggered_prop_id}, using default"
                    )

            # Load section content
            try:
                content = self._create_section_content(section_idx)
            except Exception as e:
                self.logger.error(f"Failed to load section {section_idx}: {e}")
                content = [
                    dbc.Alert(
                        [
                            html.H4("Error Loading Section", className="alert-heading"),
                            html.P(f"Failed to load section: {e}"),
                        ],
                        color="danger",
                        className="m-3",
                    )
                ]

            # Update className AND style for nav items based on active state
            nav_class_names = []
            nav_styles = []

            for i in range(len(self.navigation.sections)):
                if i == section_idx:
                    # Active state
                    nav_class_names.append(
                        self.navigation.nav_link_active_className
                        or "themed-nav-link-active"
                    )
                    # Active style - theme colors from config
                    nav_styles.append(
                        {
                            "color": self.theme_config.colors.nav_text or "#ecf0f1",
                            "backgroundColor": self.theme_config.colors.nav_active
                            or "#3498db",
                            "fontWeight": "600",
                        }
                    )
                else:
                    # Inactive state
                    nav_class_names.append(
                        self.navigation.nav_link_className or "themed-nav-link"
                    )
                    # Inactive style - light text, transparent bg
                    nav_styles.append(
                        {
                            "color": self.theme_config.colors.nav_text or "#ecf0f1",
                            "backgroundColor": "transparent",
                            "fontWeight": "500",
                        }
                    )

            self.logger.info(
                f"🎯 Setting nav classNames: {nav_class_names} (section_idx={section_idx})"
            )

            # Return: content, section_idx, 3x className, 3x style (8 total outputs)
            return [content, section_idx] + nav_class_names + nav_styles

        self.logger.info("Navigation callbacks registered")

    def _register_sidebar_callbacks(self, app: Any):
        """
        Register callback for sidebar collapse/expand toggle.

        Uses standard DBC pattern: Button click → toggle Offcanvas.is_open

        :hierarchy: [Core | Layout | Sidebar | Callbacks]
        :relates-to:
         - motivated_by: "User needs to collapse/expand sidebar for better UX"
         - implements: "method: '_register_sidebar_callbacks'"
         - uses: ["component: 'dbc.Offcanvas'", "component: 'dbc.Button'"]

        :contract:
         - pre: "self.sidebar.collapsible is True"
         - post: "Callback toggles sidebar visibility on button click"
         - invariant: "Offcanvas.is_open toggles between True/False"

        :complexity: 3
        :decision_cache: "sidebar_toggle: Chose dbc.Offcanvas.is_open property over custom CSS for standard DBC behavior"

        Args:
            app: Dash application instance
        """
        from dash.dependencies import Input, Output, State

        self.logger.info("[Core|Sidebar|Callbacks] Registering sidebar toggle callback")

        # <semantic_block: toggle_callback>
        @app.callback(
            [
                Output("sidebar-offcanvas", "is_open"),
                Output("sidebar-toggle-btn", "children"),
            ],
            [Input("sidebar-toggle-btn", "n_clicks")],
            [State("sidebar-offcanvas", "is_open")],
        )
        def toggle_sidebar(n_clicks, is_open):
            """
            Toggle sidebar open/closed state and update button icon.

            :hierarchy: [Core | Sidebar | Toggle | Callback]
            :contract:
             - pre: "Button clicked (n_clicks changes)"
             - post: "Offcanvas.is_open is inverted, button icon changes (☰ ↔ ✕)"
            """
            if n_clicks is None:
                # Initial load - return current state and appropriate icon
                icon = "✕" if is_open else "☰"
                return is_open, icon

            # Toggle state
            new_state = not is_open
            # Update icon: X when open, burger when closed
            icon = "✕" if new_state else "☰"

            self.logger.debug(
                f"[Core|Sidebar|Toggle] Button clicked | "
                f"n_clicks={n_clicks} | is_open={is_open} → {new_state} | icon={icon}"
            )

            return new_state, icon

        # </semantic_block: toggle_callback>

        self.logger.info(
            "[Core|Sidebar|Callbacks] Sidebar toggle callback registered successfully"
        )

    def _register_sidebar_adaptive_layout_callback(self, app: Any):
        """
        Register callback to adapt main content layout when sidebar toggles.

        :hierarchy: [Core | Page | Callbacks | AdaptiveLayout]
        :relates-to:
         - motivated_by: "User request: Push content instead of overlay"
         - implements: "callback: adaptive layout on sidebar toggle"

        :contract:
         - pre: "sidebar.push_content is True"
         - post: "body-wrapper className updates to push content"

        :complexity: 2
        """
        if not self.sidebar.push_content:
            return

        @app.callback(
            Output("body-wrapper", "className"),
            Input("sidebar-offcanvas", "is_open"),
            prevent_initial_call=False,
        )
        def adapt_layout_on_sidebar_toggle(is_open):
            """Adapt body wrapper className based on sidebar state."""
            self.logger.info(
                f"[Core|Sidebar|AdaptiveLayout] Callback fired | "
                f"is_open={is_open} | position={self.sidebar.position}"
            )

            if is_open:
                if self.sidebar.position == "start":
                    class_name = "sidebar-open-start"
                else:
                    class_name = "sidebar-open-end"
            else:
                class_name = ""

            self.logger.debug(
                f"[Core|Sidebar|AdaptiveLayout] Returning className: " f"'{class_name}'"
            )
            return class_name

        self.logger.info(
            "[Core|Sidebar|Callbacks] Sidebar adaptive layout callback "
            "registered successfully"
        )
