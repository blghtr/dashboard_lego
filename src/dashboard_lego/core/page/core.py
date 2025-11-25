"""
This module defines the DashboardPage class, which orchestrates blocks on a page.

"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Any, Callable, Dict, List, Optional

import dash_bootstrap_components as dbc
import plotly.graph_objects as go
from dash import html
from dash.development.base_component import Component

from dashboard_lego.core.exceptions import ConfigurationError
from dashboard_lego.core.page.callbacks import CallbacksMixin
from dashboard_lego.core.page.layout_builder import LayoutBuilderMixin
from dashboard_lego.core.page.navigation import NavigationMixin
from dashboard_lego.core.page.sidebar_builder import SidebarBuilderMixin
from dashboard_lego.core.page.theme_manager import ThemeManagerMixin
from dashboard_lego.core.state import StateManager
from dashboard_lego.core.theme import ThemeConfig
from dashboard_lego.utils.logger import get_logger

# Lazy import for SidebarConfig to avoid circular dependency
if TYPE_CHECKING:
    from dashboard_lego.core.sidebar import SidebarConfig


@dataclass
class NavigationSection:
    """
    Defines a single navigation section with a title and lazy block factory.

        :hierarchy: [Feature | Navigation System | NavigationSection]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Lazy loading of dashboard sections improves performance"
         - implements: "dataclass: 'NavigationSection'"
         - uses: ["interface: 'BaseBlock'"]

        :rationale: "Uses factory pattern to defer block creation until section is activated."
        :contract:
         - pre: "title is a non-empty string, block_factory is a callable returning List[List[Any]]"
         - post: "Section can be rendered on demand via factory invocation"

    """

    title: str
    block_factory: Callable[[], List[List[Any]]]


@dataclass
class NavigationConfig:
    """
    Configuration for navigation panel in DashboardPage with customizable styling.

        :hierarchy: [Feature | Navigation System | NavigationConfig]
        :relates-to:
         - motivated_by: "PRD: Simplify creation of dashboards with navigation sidebar and customization"
         - implements: "dataclass: 'NavigationConfig' with style parameters"
         - uses: ["dataclass: 'NavigationSection'"]

        :rationale: "Encapsulates all navigation settings including style customization in a typed, immutable config object."
        :contract:
         - pre: "sections is a non-empty list of NavigationSection instances"
         - post: "Config provides all data needed to render navigation UI with custom styling"

    """

    sections: List[NavigationSection]
    position: str = "left"  # "left" or "top"
    sidebar_width: int = 3  # Bootstrap columns (1-12)
    default_section: int = 0  # Index of initially active section

    # Style customization parameters
    sidebar_style: Optional[Dict[str, Any]] = None
    sidebar_className: Optional[str] = None
    content_style: Optional[Dict[str, Any]] = None
    content_className: Optional[str] = None
    nav_style: Optional[Dict[str, Any]] = None
    nav_className: Optional[str] = None
    nav_link_style: Optional[Dict[str, Any]] = None
    nav_link_className: Optional[str] = None
    nav_link_active_style: Optional[Dict[str, Any]] = None
    nav_link_active_className: Optional[str] = None


class DashboardPage(
    LayoutBuilderMixin,
    NavigationMixin,
    SidebarBuilderMixin,
    CallbacksMixin,
    ThemeManagerMixin,
):
    """
    Orchestrates the assembly of a dashboard page from a list of blocks.

        :hierarchy: [Feature | Layout System | Page Modification]
        :relates-to:
          - motivated_by: "Architectural Conclusion: Provide a flexible grid-based layout system"
          - implements: "class: 'DashboardPage'"
          - uses: ["interface: 'BaseBlock'", "class: 'StateManager'"]

        :rationale: "The page now accepts a nested list structure for layout definition and builds a Bootstrap grid, offering a balance of power and simplicity."
        :contract:
         - pre: "`blocks` must be a list of lists, where each inner item is a BaseBlock or a (BaseBlock, dict) tuple."
         - post: "A complete Dash layout with a grid structure can be retrieved."

    """

    def __init__(
        self,
        title: str,
        blocks: Optional[List[List[Any]]] = None,
        theme: str = dbc.themes.BOOTSTRAP,
        navigation: Optional[NavigationConfig] = None,
        theme_config: Optional[ThemeConfig] = None,
        sidebar: Optional["SidebarConfig"] = None,
    ):
        """
        Initializes the DashboardPage, creates a StateManager, and
        registers all blocks.

        Args:
            title: The main title of the dashboard page.
            blocks: A list of lists representing rows. Each item in a row is
                either a BaseBlock instance or a tuple of
                ``(BaseBlock, dict_of_col_props)``.

                Example::

                    [[block1], [(block2, {'width': 8}), (block3, {'width': 4})]]

                If navigation is provided, this parameter is optional.
            theme: An optional URL to a dash-bootstrap-components theme
                (e.g., ``dbc.themes.CYBORG``).
            navigation: Optional NavigationConfig for multi-section dashboard
                with lazy-loaded content.
            theme_config: Optional ThemeConfig for global styling customization.
            sidebar: Optional SidebarConfig for collapsible sidebar with fixed-ID blocks.
                Sidebar blocks use non-pattern-matched IDs, enabling cross-section
                State() subscriptions in pattern-matching callbacks.

        """
        # Lazy import to avoid circular dependency
        from dashboard_lego.blocks.base import BaseBlock

        self.logger = get_logger(__name__, DashboardPage)
        self.logger.info(f"Initializing dashboard page: '{title}'")

        self.title = title
        self.theme = theme
        self.navigation = navigation
        self.sidebar = sidebar

        # Auto-derive theme_config from dbc theme if not explicitly provided
        if theme_config is None:
            self.logger.debug(f"Auto-deriving ThemeConfig from theme: {theme}")
            self.theme_config = ThemeConfig.from_dbc_theme(theme)
        else:
            self.theme_config = theme_config

        self.logger.info(f"Using theme: {self.theme_config.name}")

        if self.sidebar:
            self.logger.info(
                f"Sidebar enabled | blocks={len(self.sidebar.blocks)} "
                f"position={self.sidebar.position} collapsible={self.sidebar.collapsible}"
            )

        self.layout_structure = blocks or []
        self.state_manager = StateManager()

        # Validate that either blocks or navigation is provided
        if not blocks and not navigation:
            raise ConfigurationError(
                "Either 'blocks' or 'navigation' must be provided to DashboardPage"
            )

        # Flatten the structure to get all block instances for registration
        # (Only for non-navigation mode; navigation uses lazy loading)
        self.blocks: List[BaseBlock] = []

        if not self.navigation:
            # Standard mode: register all blocks immediately
            try:
                for row_idx, row in enumerate(self.layout_structure):
                    # Handle both old format (list of blocks) and new format (tuple of (list, dict))
                    if isinstance(row, tuple) and len(row) == 2:
                        # New format: (list_of_blocks, row_options)
                        blocks_list = row[0]
                    else:
                        # Old format: list of blocks
                        blocks_list = row

                    self.logger.debug(
                        f"Processing row {row_idx} with {len(blocks_list)} blocks"
                    )
                    for item in blocks_list:
                        block = item[0] if isinstance(item, tuple) else item
                        if not isinstance(block, BaseBlock):
                            error_msg = (
                                f"All layout items must be of type BaseBlock. "
                                f"Got {type(block)} in row {row_idx}"
                            )
                            self.logger.error(error_msg)
                            raise ConfigurationError(error_msg)
                        self.blocks.append(block)

                self.logger.info(
                    f"Page structure validated: {len(self.layout_structure)} rows, "
                    f"{len(self.blocks)} blocks total"
                )
            except Exception as e:
                self.logger.error(f"Failed to process page structure: {e}")
                raise

            # Register all blocks with the state manager and inject theme
            self.logger.debug("Registering blocks with state manager")
            self.logger.debug(
                f"Registering {len(self.blocks)} blocks with state manager"
            )
            for block in self.blocks:
                self.logger.debug(f"Registering block: {block.block_id}")
                # Inject theme configuration
                block._set_theme_config(self.theme_config)
                # Register state interactions
                block._register_state_interactions(self.state_manager)
        else:
            # Navigation mode: blocks will be created and registered lazily
            self.logger.info(
                f"Navigation mode enabled with {len(self.navigation.sections)} sections"
            )
            # Cache for lazily loaded sections: {section_index: List[BaseBlock]}
            self._section_blocks_cache: Dict[int, List[BaseBlock]] = {}

    # --- Layout v2: helper constants ---
    _CELL_ALLOWED_KEYS: set = {
        "width",
        "xs",
        "sm",
        "md",
        "lg",
        "xl",
        "offset",
        "align",
        "className",
        "style",
        "children",
    }

    _ROW_ALLOWED_KEYS: set = {"align", "justify", "g", "className", "style"}

    def _build_sidebar_layout(self) -> Component:
        """
        Build layout with dbc.Offcanvas collapsible sidebar.

        UNIFIED SIDEBAR: Contains navigation links (if navigation enabled) + control blocks.

        :hierarchy: [Core | Layout | Sidebar | BuildLayout]
        :relates-to:
         - motivated_by: "Pattern-matching callbacks + unified sidebar UX"
         - implements: "method: '_build_sidebar_layout'"
         - uses: ["class: 'SidebarConfig'", "component: 'dbc.Offcanvas'"]

        :contract:
         - pre: "self.sidebar is not None and validated"
         - post: "ONE Offcanvas with navigation (if enabled) + controls"
         - invariant: "Sidebar blocks always use fixed string IDs"
         - spec_compliance: "Sidebar + Navigation: ONE dbc.Offcanvas component"

        :complexity: 6
        :decision_cache: "Unified sidebar: Navigation links at top, controls below"

        :returns:
         - Component: html.Div containing ONE offcanvas, toggle button, and main content
        """
        self.logger.info(
            f"[Core|Sidebar|BuildLayout] Building UNIFIED sidebar layout | "
            f"position={self.sidebar.position} width={self.sidebar.width} "
            f"has_navigation={self.navigation is not None}"
        )

        # <semantic_block: sidebar_content_assembly>
        sidebar_components = []

        # Add navigation links at TOP if navigation enabled
        if self.navigation:
            self.logger.debug(
                "[Core|Sidebar|BuildLayout] Adding navigation links to sidebar"
            )

            # Title
            sidebar_components.append(
                html.Div(
                    [
                        html.I(className="fas fa-tachometer-alt me-2"),
                        html.H4(
                            self.title,
                            className="mb-0 d-inline",
                            style={"color": self.theme_config.colors.nav_text},
                        ),
                    ],
                    className="mb-3",
                )
            )

            # Navigation section
            sidebar_components.append(
                html.Div(
                    [
                        html.P(
                            "Navigate between sections",
                            className="small mb-2",
                            style={
                                "color": self.theme_config.colors.nav_text,
                                "opacity": "0.7",
                            },
                        ),
                        dbc.Nav(
                            self._build_navigation_links(),
                            vertical=True,
                            pills=True,
                            id="nav-list",
                            className=self.navigation.nav_className
                            or "nav-pills-custom",
                            style=self.navigation.nav_style or {},
                        ),
                    ],
                    className="mb-4",
                )
            )

            # Separator
            sidebar_components.append(
                html.Hr(
                    style={
                        "borderColor": self.theme_config.colors.nav_text,
                        "opacity": "0.3",
                        "margin": "1rem 0",
                    }
                )
            )

        # Add control blocks BELOW navigation
        control_blocks = self._render_sidebar_blocks()
        sidebar_components.extend(control_blocks)

        self.logger.debug(
            f"[Core|Sidebar|BuildLayout] Sidebar assembled | "
            f"components={len(sidebar_components)} "
            f"(nav={self.navigation is not None}, controls={len(control_blocks)})"
        )
        # </semantic_block: sidebar_content_assembly>

        # <semantic_block: offcanvas_configuration>
        # Apply theme styles to Offcanvas
        # DBC Offcanvas has header + body, style both for theme consistency
        offcanvas_style = {
            "width": self.sidebar.width,
            "--bs-offcanvas-bg": self.theme_config.colors.nav_background,
            "--bs-offcanvas-color": self.theme_config.colors.nav_text,
            # NOTE(REVIEWER): --bs-btn-close-color is set globally in theme_manager.py
            # Bootstrap automatically inverts it for dark themes via data-bs-theme
        }

        # Add custom CSS class for additional control styling
        offcanvas_class = "themed-offcanvas"

        offcanvas = dbc.Offcanvas(
            id="sidebar-offcanvas",
            children=sidebar_components,
            title=self.sidebar.title or "Dashboard Controls",
            placement=self.sidebar.position,
            is_open=not self.sidebar.default_collapsed,
            backdrop=self.sidebar.backdrop,
            close_button=False,  # NOTE(REVIEWER): User requirement - remove close button, burger becomes X
            style=offcanvas_style,
            className=offcanvas_class,
        )

        self.logger.debug(
            f"[Core|Sidebar|BuildLayout] Offcanvas configured with theme | "
            f"bg={self.theme_config.colors.nav_background} | "
            f"text={self.theme_config.colors.nav_text}"
        )
        # </semantic_block: offcanvas_configuration>

        # <semantic_block: toggle_button>
        toggle_btn = None
        if self.sidebar.collapsible:
            position_style = {"top": "10px", "zIndex": 1060}
            if self.sidebar.position == "start":
                position_style["left"] = "10px"
            else:
                position_style["right"] = "10px"

            # Button icon will be updated by callback based on sidebar state
            # Initial state: burger (☰) when closed, will become X (✕) when open
            initial_icon = "✕" if not self.sidebar.default_collapsed else "☰"
            toggle_btn = dbc.Button(
                initial_icon,
                id="sidebar-toggle-btn",
                size="sm",
                color="secondary",
                className="position-fixed",
                style={
                    **position_style,
                    "width": "2.5rem",  # Square button
                    "height": "2.5rem",
                    "display": "flex",
                    "alignItems": "center",
                    "justifyContent": "center",
                    "padding": "0",
                },
            )
            self.logger.debug("[Core|Sidebar|BuildLayout] Toggle button created")
        # </semantic_block: toggle_button>

        # <semantic_block: main_content>
        # Build main content WITHOUT duplicate sidebar
        if self.navigation:
            self.logger.debug(
                "[Core|Sidebar|BuildLayout] Building navigation content (content area only)"
            )
            # Build ONLY content area (no sidebar!)
            main_content = self._build_navigation_content_only()
        else:
            self.logger.debug(
                "[Core|Sidebar|BuildLayout] Building standard grid content"
            )
            rows: List[Component] = []
            for row_idx, row_spec in enumerate(self.layout_structure):
                normalized_cells, row_options = self._validate_row(row_spec)
                rows.append(self._render_row(normalized_cells, row_options))
            main_content = [html.H1(self.title, className="my-4"), *rows]

        main_container = dbc.Container(main_content, fluid=True, className="p-3")
        # </semantic_block: main_content>

        self.logger.info(
            f"[Core|Sidebar|BuildLayout] UNIFIED sidebar layout complete | "
            f"toggle={toggle_btn is not None} | "
            f"nav_in_sidebar={self.navigation is not None}"
        )

        return html.Div([toggle_btn, offcanvas, main_container])

    def build_layout(self) -> Component:
        """
        Assembles the layouts from all blocks into a grid-based page layout.

        Supports three layout modes:
        1. Sidebar + Navigation: dbc.Offcanvas + multi-section navigation
        2. Sidebar + Standard: dbc.Offcanvas + grid layout
        3. Standard/Navigation: existing behavior (no sidebar)

        CRITICAL: For navigation mode, preload all sections BEFORE building layout
        to prevent duplicate block creation when combined with sidebar.

        :hierarchy: [Core | Page | BuildLayout]
        :relates-to:
         - motivated_by: "Dash callback lifecycle requires all blocks before app.run()"
         - implements: "method: 'build_layout' with navigation preload"
         - uses: ["method: '_preload_all_section_blocks'"]

        :contract:
         - pre: "Page configured with blocks or navigation"
         - post: "Layout built with all blocks created exactly once"
         - invariant: "Navigation sections preloaded before HTML rendering"
         - spec_compliance: "Dash callback registration lifecycle"

        :complexity: 5
        :decision_cache: "Preload navigation before layout to prevent duplicate block creation"

        Returns:
            A Dash component representing the entire page.

        """
        self.logger.info("Building page layout")

        # <semantic_block: navigation_preload>
        # CRITICAL: Preload navigation sections before layout build
        # Prevents duplicate block creation in sidebar+navigation mode
        # Ensures all blocks exist before register_callbacks() is called
        if self.navigation and not hasattr(self, "_sections_preloaded"):
            self.logger.info(
                f"Preloading {len(self.navigation.sections)} navigation sections "
                f"before layout build (prevents duplicate block creation)"
            )
            self._preload_all_section_blocks()
            self._sections_preloaded = True
            self.logger.debug("Navigation sections preloaded successfully")
        # </semantic_block: navigation_preload>

        # Sidebar mode: use Offcanvas + main content
        if self.sidebar:
            self.logger.info(
                f"Building sidebar layout | position={self.sidebar.position}"
            )
            return self._build_sidebar_layout()

        # Navigation mode: use navigation layout
        if self.navigation:
            self.logger.info("Building navigation-based layout")
            return self._build_navigation_layout()

        # Standard mode: use grid layout
        self.logger.debug(
            f"Building layout: {len(self.layout_structure)} rows, {len(self.blocks)} blocks"
        )
        rows: List[Component] = []

        try:
            for row_idx, row_spec in enumerate(self.layout_structure):
                # Validate and normalize the row and its cells
                normalized_cells, row_options = self._validate_row(row_spec)

                self.logger.debug(
                    f"Rendering row {row_idx} with {len(normalized_cells)} cells and options {row_options}"
                )
                rows.append(self._render_row(normalized_cells, row_options))

            self.logger.info(f"Layout built successfully: {len(rows)} rows rendered")
            return dbc.Container(
                [html.H1(self.title, className="my-4"), *rows], fluid=True
            )
        except Exception as e:
            self.logger.error(f"Error building layout: {e}", exc_info=True)
            raise

    def export_to_figure(
        self,
        params: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
    ) -> go.Figure:
        """
        Export entire dashboard layout to single Plotly figure.

        Combines all chart blocks into a single figure using subplots.
        Non-chart blocks (metrics, text, controls) are skipped.

        Args:
            params: Optional parameters for filtering data in all blocks
            title: Optional title for the combined figure

        Returns:
            Single Plotly Figure with all charts in grid layout

        Example:
            >>> page = DashboardPage(title="Sales Dashboard", blocks=layout)
            >>> fig = page.export_to_figure(title="Q4 Sales Report")
            >>> fig.write_html("dashboard_export.html")

        Note:
            Requires dashboard to be built without navigation (single layout).
            For navigation dashboards, export sections individually.
        """
        if self.navigation:
            raise ValueError(
                "Cannot export navigation dashboard. "
                "Export individual sections using section factories."
            )

        from dashboard_lego.utils.layout_export import export_layout_to_figure

        return export_layout_to_figure(
            self.layout_structure,
            params=params,
            title=title or self.title,
        )
