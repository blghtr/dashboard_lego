"""
This module defines the DashboardPage class, which orchestrates blocks on a page.

"""

from dataclasses import dataclass
from typing import Any, Callable, Dict, Iterable, List, Optional, Tuple

import dash_bootstrap_components as dbc
from dash import dcc, html
from dash.dependencies import Input, Output
from dash.development.base_component import Component

from dashboard_lego.blocks.base import BaseBlock
from dashboard_lego.core.state import StateManager
from dashboard_lego.core.theme import ThemeConfig
from dashboard_lego.utils.exceptions import ConfigurationError
from dashboard_lego.utils.logger import get_logger


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


class DashboardPage:
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

        """
        self.logger = get_logger(__name__, DashboardPage)
        self.logger.info(f"Initializing dashboard page: '{title}'")

        self.title = title
        self.theme = theme
        self.navigation = navigation

        # Auto-derive theme_config from dbc theme if not explicitly provided
        if theme_config is None:
            self.logger.debug(f"Auto-deriving ThemeConfig from theme: {theme}")
            self.theme_config = ThemeConfig.from_dbc_theme(theme)
        else:
            self.theme_config = theme_config

        self.logger.info(f"Using theme: {self.theme_config.name}")

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

    def _normalize_cell(
        self, cell_spec: Any, row_length: int
    ) -> Tuple[BaseBlock, Dict[str, Any]]:
        """
        Normalizes a cell spec to a `(block, options)` tuple with defaults.

            :hierarchy: [Architecture | Layout System | Normalize Cell]
            :relates-to:
             - motivated_by: "Need a robust, typed layout parsing layer before rendering"
             - implements: "method: '_normalize_cell'"
             - uses: ["class: 'BaseBlock'"]

            :rationale: "Centralizes option handling and back-compat defaults."
            :contract:
             - pre: "cell_spec is BaseBlock or (BaseBlock, dict)"
             - post: "Returns (block, options) where options contains only allowed keys; assigns default equal width if none provided"

        """
        if isinstance(cell_spec, tuple):
            block, options = cell_spec
        else:
            block, options = cell_spec, {}

        if not isinstance(block, BaseBlock):
            raise TypeError("All layout items must be of type BaseBlock")

        if not isinstance(options, dict):
            raise ConfigurationError("Cell options must be a dict if provided")

        unknown = set(options.keys()) - self._CELL_ALLOWED_KEYS
        if unknown:
            raise ConfigurationError(
                f"Unknown cell option keys: {sorted(list(unknown))}. "
                f"Allowed: {sorted(list(self._CELL_ALLOWED_KEYS))}"
            )

        # Back-compat default: if no responsive width provided, set 'width'
        if not any(k in options for k in ["width", "xs", "sm", "md", "lg", "xl"]):
            # Equal split; ensure at least 1
            options["width"] = max(1, 12 // max(1, row_length))

        return block, options

    def _validate_row(self, row_spec: Any) -> Tuple[List[Any], Dict[str, Any]]:
        """
        Validates and normalizes a row spec to `(row_cells, row_options)`.

            :hierarchy: [Architecture | Layout System | Validate Row]
            :relates-to:
             - motivated_by: "Catch invalid layouts early with informative errors"
             - implements: "method: '_validate_row'"
             - uses: ["method: '_normalize_cell'"]

            :rationale: "Fast-fail validation with friendly diagnostics simplifies debugging."
            :contract:
             - pre: "row_spec is a list of cells or (list_of_cells, dict)"
             - post: "Returns (cells, row_options) with allowed keys only; ensures width bounds and per-breakpoint sums do not exceed 12 when specified"

        """
        if (
            isinstance(row_spec, tuple)
            and len(row_spec) == 2
            and isinstance(row_spec[1], dict)
        ):
            row_cells, row_options = row_spec
        else:
            row_cells, row_options = row_spec, {}

        if not isinstance(row_cells, Iterable) or isinstance(row_cells, (str, bytes)):
            raise ConfigurationError("Each row must be an iterable of cells")

        row_cells = list(row_cells)
        if len(row_cells) == 0:
            raise ConfigurationError("Row cannot be empty")

        # Row options validation
        unknown_row = set(row_options.keys()) - self._ROW_ALLOWED_KEYS
        if unknown_row:
            raise ConfigurationError(
                f"Unknown row option keys: {sorted(list(unknown_row))}. "
                f"Allowed: {sorted(list(self._ROW_ALLOWED_KEYS))}"
            )

        # Normalize cells and perform per-cell validations
        normalized: List[Tuple[BaseBlock, Dict[str, Any]]] = []
        for cell in row_cells:
            block, options = self._normalize_cell(cell, row_length=len(row_cells))

            # Validate width bounds for any provided breakpoint
            for key in ["width", "xs", "sm", "md", "lg", "xl"]:
                if key in options:
                    value = options[key]
                    if not isinstance(value, int) or value < 1 or value > 12:
                        raise ConfigurationError(
                            f"Invalid width for '{key}': {value}. Must be an integer 1..12"
                        )
            normalized.append((block, options))

        # Validate that explicit breakpoint sums do not exceed 12
        for bp in ["width", "xs", "sm", "md", "lg", "xl"]:
            bp_sum = sum(opts.get(bp, 0) for _, opts in normalized if bp in opts)
            if bp_sum and bp_sum > 12:
                raise ConfigurationError(
                    f"Sum of column widths for breakpoint '{bp}' exceeds 12: {bp_sum}"
                )

        # Return cells back in their original representation (block, options)
        return [(b, o) for b, o in normalized], row_options

    def _render_row(
        self,
        row_cells: List[Tuple[BaseBlock, Dict[str, Any]]],
        row_options: Dict[str, Any],
    ) -> Component:
        """
        Renders a row into a `dbc.Row` with validated options.

            :hierarchy: [Architecture | Layout System | Render Row]
            :relates-to:
             - motivated_by: "Map declarative row options to dbc.Row props"
             - implements: "method: '_render_row'"
             - uses: ["method: '_render_cell'"]

            :rationale: "Keeps build_layout small and focused by delegating rendering."
            :contract:
             - pre: "row_cells are normalized, row_options validated"
             - post: "Returns a dbc.Row containing dbc.Col children"

        """
        cols = [self._render_cell(block, opts) for block, opts in row_cells]
        row_kwargs: Dict[str, Any] = {}

        # Handle Bootstrap gap classes
        if "g" in row_options:
            gap = row_options["g"]
            if isinstance(gap, int):
                row_kwargs["className"] = f"g-{gap}"
            else:
                row_kwargs["className"] = f"g-{gap}"

        # Handle other row options
        for key in ["align", "justify", "className", "style"]:
            if key in row_options:
                if key == "className" and "className" in row_kwargs:
                    # Merge gap class with existing className
                    row_kwargs["className"] = (
                        f"{row_kwargs['className']} {row_options[key]}"
                    )
                else:
                    row_kwargs[key] = row_options[key]

        # Keep legacy spacing class unless overridden
        if "className" not in row_kwargs:
            row_kwargs["className"] = "mb-4"
        return dbc.Row(cols, **row_kwargs)

    def _render_cell(self, block: BaseBlock, options: Dict[str, Any]) -> Component:
        """
        Renders a single cell as `dbc.Col` and supports optional nested rows.

            :hierarchy: [Architecture | Layout System | Render Cell]
            :relates-to:
             - motivated_by: "Support responsive widths and nested rows in columns"
             - implements: "method: '_render_cell'"
             - uses: ["class: 'BaseBlock'", "method: '_validate_row'", "method: '_render_row'"]

            :rationale: "Enables one-level nested rows to build complex layouts without deep hierarchies."
            :contract:
             - pre: "options may include responsive widths and 'children' (list of row specs)"
             - post: "Returns dbc.Col with content and optional nested dbc.Row sections"

        """
        # Split options into Col kwargs and special fields
        col_kwargs: Dict[str, Any] = {}

        # Handle offset classes
        if "offset" in options:
            offset = options["offset"]
            if isinstance(offset, int):
                col_kwargs["className"] = f"offset-{offset}"
            else:
                col_kwargs["className"] = f"offset-{offset}"

        # Handle other column options
        for key in [
            "width",
            "xs",
            "sm",
            "md",
            "lg",
            "xl",
            "align",
            "className",
            "style",
        ]:
            if key in options:
                if key == "className" and "className" in col_kwargs:
                    # Merge offset class with existing className
                    col_kwargs["className"] = (
                        f"{col_kwargs['className']} {options[key]}"
                    )
                else:
                    col_kwargs[key] = options[key]

        content_children: List[Component] = []
        # Primary block content
        content_children.append(block.layout())

        # Nested rows if provided
        children_rows = options.get("children")
        if children_rows:
            if not isinstance(children_rows, Iterable) or isinstance(
                children_rows, (str, bytes)
            ):
                raise ConfigurationError("'children' must be a list of row specs")
            for child_row in children_rows:
                normalized_child_cells, child_row_opts = self._validate_row(child_row)
                content_children.append(
                    self._render_row(normalized_child_cells, child_row_opts)
                )

        # If only one child, pass directly; else wrap
        col_content: Component = (
            content_children[0]
            if len(content_children) == 1
            else html.Div(content_children)
        )
        return dbc.Col(col_content, **col_kwargs)

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
            "minHeight": "100vh",
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

            # Build NavLink props
            # Note: Do NOT apply inline styles here, even if provided via NavigationConfig,
            # because inline styles cannot be updated by callbacks and would override className
            # Users should use CSS class overrides via nav_link_className parameters
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
                        html.H4(self.title, className="mb-0 d-inline"),
                    ],
                    className="mb-4",
                ),
                html.Hr(style={"borderColor": "#34495e", "margin": "1.5rem 0"}),
                html.P(
                    "Navigate between sections",
                    className="text-muted small mb-3",
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
        content_area = html.Div(
            id="nav-content-area",
            children=initial_content,
            style=content_style,
            className=self.navigation.content_className,
        )

        # Store to track the currently active section index
        active_section_store = dcc.Store(
            id="active-section-store", data=self.navigation.default_section
        )

        # Custom CSS will be added via external stylesheets in the app
        # No inline CSS needed here

        if self.navigation.position == "left":
            return html.Div([active_section_store, sidebar, content_area])
        else:
            # Top navigation - not yet implemented
            raise NotImplementedError(
                "Top navigation position is not yet implemented. Use 'left'."
            )

    def build_layout(self) -> Component:
        """
        Assembles the layouts from all blocks into a grid-based page layout.

        Returns:
            A Dash component representing the entire page.

        """
        self.logger.info("Building page layout")

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
        if section_index in self._section_blocks_cache:
            # Return cached content
            self.logger.debug(f"Using cached content for section {section_index}")
            # Re-render from cached blocks
            rows = []
            for row_spec in self._section_layout_cache[section_index]:
                normalized_cells, row_options = self._validate_row(row_spec)
                rows.append(self._render_row(normalized_cells, row_options))
            return rows

        # Create new blocks via factory
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
        section_blocks: List[BaseBlock] = []
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

        # NEW: Dynamically register callbacks for lazy-loaded sections
        if hasattr(self, "_app_instance") and self._app_instance is not None:
            self.logger.info(
                f"Registering callbacks for lazy-loaded section {section_index}"
            )
            self.state_manager.generate_callbacks(self._app_instance)
            self.state_manager.bind_callbacks(self._app_instance, section_blocks)
            self.logger.info(f"Callbacks registered for section {section_index}")

        # Render rows
        rows = []
        for row_spec in layout_structure:
            normalized_cells, row_options = self._validate_row(row_spec)
            rows.append(self._render_row(normalized_cells, row_options))

        return rows

    def register_callbacks(self, app: Any):
        """
        Registers callbacks using both old (state-based) and new (block-centric) mechanisms.

        :hierarchy: [Architecture | Callback Registration | DashboardPage]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Hybrid callback system enables
           both legacy and modern callback patterns for backward compatibility"
         - implements: "method: 'register_callbacks' with dual mechanism"
         - uses: ["method: 'generate_callbacks'", "method: 'bind_callbacks'"]

        :rationale: "Use old mechanism for static blocks with state dependencies,
         new mechanism for interactive blocks with controls."
        :contract:
         - pre: "StateManager is initialized, blocks are registered."
         - post: "All callbacks (old and new style) are registered with Dash app."

        Args:
            app: The Dash app instance.

        """
        self.logger.info("Registering callbacks with Dash app")

        try:
            # Navigation-specific callbacks MUST be registered BEFORE error handling wrapper
            if self.navigation:
                self._register_navigation_callbacks(app)

            # Store app reference for lazy-loaded sections
            self._app_instance = app

            # Set up comprehensive error handling for Dash callbacks
            # NOTE: This replaces app.callback, so must be done AFTER navigation callbacks
            self._setup_callback_error_handling(app)

            # OLD MECHANISM: State-based callbacks for StaticChartBlock
            self.state_manager.generate_callbacks(app)

            # NEW MECHANISM: Block-centric callbacks for InteractiveChartBlock
            # For navigation mode, we need to handle dynamic blocks
            if self.navigation:
                # Bind callbacks for any already-loaded sections
                all_section_blocks = []
                for blocks in self._section_blocks_cache.values():
                    all_section_blocks.extend(blocks)
                if all_section_blocks:
                    self.state_manager.bind_callbacks(app, all_section_blocks)
            else:
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

            # Update className for nav items based on active state
            # Use themed-nav-link* classes which are styled via CSS variables
            nav_class_names = []
            for i in range(len(self.navigation.sections)):
                if i == section_idx:
                    # Active state - use active className (defaults to themed-nav-link-active)
                    active_class = (
                        self.navigation.nav_link_active_className
                        or "themed-nav-link-active"
                    )
                    nav_class_names.append(active_class)
                else:
                    # Inactive state - use default className (defaults to themed-nav-link)
                    default_class = (
                        self.navigation.nav_link_className or "themed-nav-link"
                    )
                    nav_class_names.append(default_class)

            self.logger.info(
                f"🎯 Setting nav classNames: {nav_class_names} (section_idx={section_idx})"
            )

            return [content, section_idx] + nav_class_names

        self.logger.info("Navigation callbacks registered")

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
        css_vars_str = ";\n                ".join(
            f"{k}: {v}" for k, v in css_vars.items()
        )

        # Determine Bootstrap theme mode
        bs_theme = "dark" if self.theme_config.name.lower() == "dark" else "light"

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

        # Navigation CSS classes using theme CSS variables
        nav_css = """
            /* Navigation link styles using theme variables */
            .themed-nav-link {
                color: var(--theme-nav-text);
                background-color: transparent;
                padding: var(--theme-spacing-md);
                border-radius: var(--theme-border-radius);
                text-decoration: none;
                transition: all 0.3s ease;
                display: block;
            }
            .themed-nav-link:hover {
                background-color: var(--theme-nav-hover);
            }
            .themed-nav-link-active {
                background-color: var(--theme-nav-active) !important;
                color: var(--theme-white) !important;
            }"""

        return f"""<!DOCTYPE html>
<html data-bs-theme="{bs_theme}">
    <head>
        {{{{%metas%}}}}
        <title>{{{{%title%}}}}</title>
        {{{{%favicon%}}}}
        {{{{%css%}}}}
        <style>
            :root {{
                {css_vars_str}
            }}{dropdown_css}{nav_css}
        </style>
    </head>
    <body>
        {{{{%app_entry%}}}}
        <footer>
            {{{{%config%}}}}
            {{{{%scripts%}}}}
            {{{{%renderer%}}}}
        </footer>
    </body>
</html>"""

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

        # Apply theme HTML template
        app.index_string = self.get_theme_html_template()

        # Build and set layout
        app.layout = self.build_layout()

        # Register all callbacks
        self.register_callbacks(app)

        self.logger.info("Dash app created and configured successfully")
        return app
