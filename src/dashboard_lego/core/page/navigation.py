"""
Navigation-related methods for DashboardPage.

:hierarchy: [Core | Page | Navigation]
:complexity: 5
"""

from typing import Any, Dict, List

import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.development.base_component import Component

from dashboard_lego.core.exceptions import ConfigurationError


class NavigationMixin:
    """
    Mixin providing navigation methods for DashboardPage.

    :hierarchy: [Core | Page | Navigation | Mixin]
    :relates-to:
     - motivated_by: "Decomposition: Extract navigation logic from DashboardPage"
     - implements: "Mixin: NavigationMixin"
     - uses: ["class: 'NavigationConfig'", "class: 'NavigationSection'"]

    :rationale: "Separates navigation building concerns from core page logic."
    :contract:
     - pre: "Class has navigation, theme_config, logger, state_manager, title, _section_blocks_cache attributes"
     - post: "Provides methods for building navigation layouts and managing sections"
    """

    def _build_navigation_links(self) -> List[Component]:
        """
        Build navigation links for sidebar integration.

        :hierarchy: [Core | Navigation | BuildLinks]
        :relates-to:
         - motivated_by: "Sidebar + Navigation integration: links go IN sidebar"
         - implements: "method: '_build_navigation_links'"

        :contract:
         - pre: "self.navigation is not None"
         - post: "Returns list of nav link components"
         - invariant: "No wrapper div, just the links"

        :complexity: 3

        :returns:
         - List[Component]: Navigation links ready for sidebar
        """
        nav_links = []
        for idx, section in enumerate(self.navigation.sections):
            if idx == self.navigation.default_section:
                initial_class = (
                    self.navigation.nav_link_active_className
                    or "themed-nav-link-active"
                )
            else:
                initial_class = self.navigation.nav_link_className or "themed-nav-link"

            nav_link_props = {
                "id": f"nav-item-{idx}",
                "href": "#",
                "n_clicks": 0,
                "className": initial_class,
            }

            nav_links.append(
                dbc.NavLink(
                    [
                        html.I(className="fas fa-chart-bar me-2"),
                        section.title,
                    ],
                    **nav_link_props,
                )
            )

        return nav_links

    def _build_navigation_content_only(self) -> List[Component]:
        """
        Build ONLY navigation content area (without sidebar).

        Used when sidebar+navigation are combined in ONE Offcanvas.

        :hierarchy: [Core | Navigation | ContentOnly]
        :relates-to:
         - motivated_by: "Sidebar + Navigation integration: avoid duplicate sidebars"
         - implements: "method: '_build_navigation_content_only'"

        :contract:
         - pre: "self.navigation is not None"
         - post: "Returns [store, content_area] WITHOUT sidebar div"
         - invariant: "No sidebar wrapper - navigation already in Offcanvas"

        :complexity: 3
        :decision_cache: "Unified sidebar: Avoid duplicate navigation sidebar"

        :returns:
         - List[Component]: [active_section_store, content_area]
        """
        # Get content style from theme
        base_content_style = self.theme_config.get_component_style(
            "navigation", "content"
        )

        # Content style WITHOUT marginLeft (no fixed sidebar to avoid)
        content_style = {
            **base_content_style,
            "padding": "2rem",
            **(self.navigation.content_style or {}),
        }

        # Load initial content
        try:
            initial_content = self._create_section_content(
                self.navigation.default_section
            )
            self.logger.debug(
                f"[Core|Navigation|ContentOnly] Loaded section {self.navigation.default_section}"
            )
        except Exception as e:
            self.logger.error(
                f"[Core|Navigation|ContentOnly] Failed to load section: {e}"
            )
            initial_content = [
                dbc.Alert(
                    [
                        html.H4("Error Loading Section", className="alert-heading"),
                        html.P(f"Failed to load initial section: {e}"),
                    ],
                    color="danger",
                    className="m-3",
                )
            ]

        # Content area (dynamic, updates on navigation)
        nav_classes = "nav-content-area"
        if self.navigation.content_className:
            nav_classes = f"{nav_classes} {self.navigation.content_className}"

        content_area = html.Div(
            id="nav-content-area",
            children=initial_content,
            style=content_style,
            className=nav_classes,
        )

        # Body wrapper for adaptive layout
        body_wrapper = html.Div(
            id="body-wrapper",
            className="",  # Will be updated by adaptive layout callback
            children=[content_area],
        )

        # Store for active section tracking
        active_section_store = dcc.Store(
            id="active-section-store", data=self.navigation.default_section
        )

        self.logger.info(
            f"[Core|Navigation|ContentOnly] Content area built | "
            f"initial_section={self.navigation.default_section}"
        )

        return [active_section_store, body_wrapper]

    def _build_navigation_layout(self) -> Component:
        """
        Builds the navigation-based layout with fixed sidebar and dynamic content.

        :hierarchy: [Feature | Navigation System | Build Navigation Layout]
        :relates-to:
         - motivated_by: "PRD: User-friendly navigation panel for multi-section dashboards"
         - implements: "method: '_build_navigation_layout'"
         - uses: ["dataclass: 'NavigationConfig'", "library: 'dash_bootstrap_components'"]

        :rationale: "Uses fixed sidebar with dbc.Nav and dcc.Store for state tracking."
        :contract:
         - pre: "self.navigation is not None and contains valid sections"
         - post: "Returns layout with fixed sidebar and dynamic content area"

        """
        if not self.navigation:
            raise ConfigurationError(
                "Navigation config is required for navigation layout"
            )

        # Dynamic sidebar width based on content
        max_title_length = max(
            len(section.title) for section in self.navigation.sections
        )
        sidebar_width = max(16, min(24, max_title_length * 0.8 + 8))  # Dynamic width

        # Get base styles from theme config
        base_sidebar_style = self.theme_config.get_component_style(
            "navigation", "sidebar"
        )
        base_content_style = self.theme_config.get_component_style(
            "navigation", "content"
        )
        # Note: nav_link styles now handled via CSS classes, not inline styles

        # Default sidebar style with layout-specific properties
        default_sidebar_style = {
            **base_sidebar_style,  # Apply theme styles first
            "position": "fixed",
            "top": 0,
            "left": 0,
            "bottom": 0,
            "width": f"{sidebar_width}rem",
            "overflowY": "auto",
            "boxShadow": "2px 0 5px rgba(0,0,0,0.1)",
            "zIndex": 1000,
        }

        # Apply custom sidebar style overrides (user customization has highest priority)
        sidebar_style = {
            **default_sidebar_style,
            **(self.navigation.sidebar_style or {}),
        }

        # Default content area style with margin to avoid sidebar overlap
        default_content_style = {
            **base_content_style,  # Apply theme styles first
            "marginLeft": f"{sidebar_width + 1}rem",
            "marginRight": "2rem",
            "width": "auto",  # Allow content to fit naturally
            "maxWidth": "100%",  # Prevent overflow
            "overflowX": "auto",  # Allow horizontal scroll if needed
        }

        # Apply custom content style overrides (user customization has highest priority)
        content_style = {
            **default_content_style,
            **(self.navigation.content_style or {}),
        }

        # Create navigation links with CSS class-based styling
        # Note: Inline styles removed to allow CSS classes to work properly
        nav_links = []
        for idx, section in enumerate(self.navigation.sections):
            # Determine className based on whether this is the active section
            # Use themed-nav-link* classes which are styled via CSS variables
            if idx == self.navigation.default_section:
                # Active section - use active class
                initial_class = (
                    self.navigation.nav_link_active_className
                    or "themed-nav-link-active"
                )
            else:
                # Inactive section - use default class
                initial_class = self.navigation.nav_link_className or "themed-nav-link"

            # Build NavLink props WITHOUT inline styles
            # CRITICAL: Don't use inline styles - they can't be updated by callbacks!
            # Instead, use className which updates via callback + CSS variable overrides
            nav_link_props = {
                "id": f"nav-item-{idx}",
                "href": "#",
                "n_clicks": 0,
                "className": initial_class,
            }

            nav_links.append(
                dbc.NavLink(
                    [
                        html.I(className="fas fa-chart-bar me-2"),  # Icon
                        section.title,
                    ],
                    **nav_link_props,
                )
            )

        # Default nav style
        default_nav_style = {}
        nav_style = {**default_nav_style, **(self.navigation.nav_style or {})}
        nav_className = self.navigation.nav_className or "nav-pills-custom"

        # Sidebar with navigation
        sidebar = html.Div(
            [
                html.Div(
                    [
                        html.I(className="fas fa-tachometer-alt me-2"),
                        html.H4(
                            self.title,
                            className="mb-0 d-inline",
                            style={"color": self.theme_config.colors.nav_text},
                        ),
                    ],
                    className="mb-4",
                ),
                html.Hr(
                    style={
                        "borderColor": self.theme_config.colors.nav_text,
                        "opacity": "0.3",
                        "margin": "1.5rem 0",
                    }
                ),
                html.P(
                    "Navigate between sections",
                    className="small mb-3",
                    style={
                        "color": self.theme_config.colors.nav_text,
                        "opacity": "0.7",
                    },
                ),
                dbc.Nav(
                    nav_links,
                    vertical=True,
                    pills=True,
                    id="nav-list",
                    className=nav_className,
                    style=nav_style,
                ),
            ],
            style=sidebar_style,
            className=self.navigation.sidebar_className,
        )

        # Load initial content for the default section
        try:
            initial_content = self._create_section_content(
                self.navigation.default_section
            )
            self.logger.debug(
                f"Loaded initial content for default section {self.navigation.default_section}"
            )
        except Exception as e:
            self.logger.error(
                f"Failed to load initial section {self.navigation.default_section}: {e}"
            )
            initial_content = [
                dbc.Alert(
                    [
                        html.H4("Error Loading Section", className="alert-heading"),
                        html.P(f"Failed to load initial section: {e}"),
                    ],
                    color="danger",
                    className="m-3",
                )
            ]

        # Content area for dynamic content with initial content loaded
        nav_classes = "nav-content-area"
        if self.navigation.content_className:
            nav_classes = f"{nav_classes} {self.navigation.content_className}"

        content_area = html.Div(
            id="nav-content-area",
            children=initial_content,
            style=content_style,
            className=nav_classes,
        )

        # Body wrapper for adaptive layout
        body_wrapper = html.Div(
            id="body-wrapper",
            className="",  # Will be updated by adaptive layout callback
            children=[content_area],
        )

        # Store to track the currently active section index
        active_section_store = dcc.Store(
            id="active-section-store", data=self.navigation.default_section
        )

        # Custom CSS will be added via external stylesheets in the app
        # No inline CSS needed here

        if self.navigation.position == "left":
            return html.Div([active_section_store, sidebar, body_wrapper])
        else:
            # Top navigation - not yet implemented
            raise NotImplementedError(
                "Top navigation position is not yet implemented. Use 'left'."
            )

    def _create_section_content(self, section_index: int) -> List[Component]:
        """
        Lazily creates and caches blocks for a given section.

        :hierarchy: [Feature | Navigation System | Create Section Content]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Lazy loading improves initial page load performance"
         - implements: "method: '_create_section_content'"
         - uses: ["dataclass: 'NavigationSection'", "class: 'StateManager'"]

        :rationale: "Cache blocks per section to avoid recreating on revisit, but create only on demand."
        :contract:
         - pre: "section_index is valid, navigation config exists"
         - post: "Returns list of rendered rows for the section; blocks are cached and registered"

        """
        # Lazy import to avoid circular dependency
        from dashboard_lego.blocks.base import BaseBlock

        if section_index in self._section_blocks_cache:
            # Use preloaded blocks (callbacks already registered)
            self.logger.debug(f"Using preloaded blocks for section {section_index}")
            # Re-render from cached layout
            rows = []
            for row_spec in self._section_layout_cache[section_index]:
                normalized_cells, row_options = self._validate_row(row_spec)
                rows.append(self._render_row(normalized_cells, row_options))
            return rows

        # Fallback: Section not preloaded (shouldn't happen if preload worked)
        self.logger.warning(
            f"Section {section_index} not preloaded - creating on-demand (callbacks may not work)"
        )
        self.logger.info(f"Lazily loading section {section_index}")
        section = self.navigation.sections[section_index]

        try:
            layout_structure = section.block_factory()
            self.logger.debug(f"Factory returned {len(layout_structure)} rows")
        except Exception as e:
            self.logger.error(
                f"Error in block factory for section {section_index}: {e}"
            )
            raise ConfigurationError(
                f"Block factory for section '{section.title}' failed: {e}"
            ) from e

        # Extract and register blocks
        section_blocks: List["BaseBlock"] = []
        for row in layout_structure:
            if isinstance(row, tuple) and len(row) == 2:
                blocks_list = row[0]
            else:
                blocks_list = row

            for item in blocks_list:
                block = item[0] if isinstance(item, tuple) else item
                if not isinstance(block, BaseBlock):
                    raise ConfigurationError(
                        f"All layout items must be of type BaseBlock in section '{section.title}'"
                    )
                section_blocks.append(block)

                # Inject navigation context for pattern matching callbacks
                block.navigation_mode = True
                block.section_index = section_index

                # Inject theme configuration
                block._set_theme_config(self.theme_config)
                # Register block with state manager
                block._register_state_interactions(self.state_manager)

        # Cache blocks and layout
        self._section_blocks_cache[section_index] = section_blocks
        if not hasattr(self, "_section_layout_cache"):
            self._section_layout_cache: Dict[int, List[List[Any]]] = {}
        self._section_layout_cache[section_index] = layout_structure

        self.logger.info(
            f"Section {section_index} loaded: {len(section_blocks)} blocks registered"
        )

        # NOTE: Callbacks are NOT registered here anymore
        # They were already registered during register_callbacks() via _preload_all_section_blocks()
        # This fallback path should rarely execute

        # Render rows
        rows = []
        for row_spec in layout_structure:
            normalized_cells, row_options = self._validate_row(row_spec)
            rows.append(self._render_row(normalized_cells, row_options))

        return rows

    def _preload_all_section_blocks(self) -> List[Any]:
        """
        Preload all section blocks for callback registration.

        CRITICAL: Dash requires all callbacks registered before app.run().
        This method creates blocks from all sections upfront.

        :hierarchy: [Architecture | Navigation | Preload]
        :relates-to:
         - motivated_by: "Dash lifecycle requires callbacks before app.run()"
         - implements: "method: '_preload_all_section_blocks'"
         - uses: ["method: 'block_factory'"]

        :contract:
         - pre: "Navigation config exists with block factories"
         - post: "Returns list of all blocks with navigation context set"

        :complexity: 5
        :decision_cache: "Preload all sections to satisfy Dash callback lifecycle requirements"

        Returns:
            List of all blocks from all sections
        """
        from dashboard_lego.blocks.base import BaseBlock

        all_blocks = []
        self.logger.info(
            f"Preloading {len(self.navigation.sections)} sections for callback registration"
        )

        for section_idx, section in enumerate(self.navigation.sections):
            try:
                # Call factory to create blocks
                layout_structure = section.block_factory()

                # Extract blocks from layout
                section_blocks = []
                for row in layout_structure:
                    if isinstance(row, tuple) and len(row) == 2:
                        blocks_list = row[0]
                    else:
                        blocks_list = row

                    for item in blocks_list:
                        block = item[0] if isinstance(item, tuple) else item
                        if isinstance(block, BaseBlock):
                            section_blocks.append(block)

                # Set navigation context for each block
                for block in section_blocks:
                    block.navigation_mode = True
                    block.section_index = section_idx
                    block._set_theme_config(self.theme_config)
                    block._register_state_interactions(self.state_manager)

                # Cache blocks and layout
                self._section_blocks_cache[section_idx] = section_blocks
                if not hasattr(self, "_section_layout_cache"):
                    self._section_layout_cache = {}
                self._section_layout_cache[section_idx] = layout_structure

                all_blocks.extend(section_blocks)
                self.logger.debug(
                    f"Preloaded section {section_idx}: {len(section_blocks)} blocks"
                )

            except Exception as e:
                self.logger.error(f"Error preloading section {section_idx}: {e}")
                raise

        self.logger.info(f"Preloaded {len(all_blocks)} total blocks from all sections")
        return all_blocks
