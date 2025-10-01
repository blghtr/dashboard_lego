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
                    (BaseBlock, dict_of_col_props).
                    Example: [[block1], [(block2, {'width': 8}),
                                        (block3, {'width': 4})]]
                    If navigation is provided, this parameter is optional.
            theme: An optional URL to a dash-bootstrap-components theme
                   (e.g., dbc.themes.CYBORG).
            navigation: Optional NavigationConfig for multi-section dashboard
                       with lazy-loaded content.
            theme_config: Optional ThemeConfig for global styling customization.

        """
        self.logger = get_logger(__name__, DashboardPage)
        self.logger.info(f"Initializing dashboard page: '{title}'")

        self.title = title
        self.theme = theme
        self.navigation = navigation
        self.theme_config = theme_config or ThemeConfig.light_theme()
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

            # Register all blocks with the state manager
            self.logger.debug("Registering blocks with state manager")
            self.logger.debug(
                f"Registering {len(self.blocks)} blocks with state manager"
            )
            for block in self.blocks:
                self.logger.debug(f"Registering block: {block.block_id}")
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

        # Default sidebar style with better colors and spacing
        default_sidebar_style = {
            "position": "fixed",
            "top": 0,
            "left": 0,
            "bottom": 0,
            "width": f"{sidebar_width}rem",
            "padding": "2rem 1.5rem",
            "background-color": "#2c3e50",  # Dark blue-gray
            "color": "#ecf0f1",  # Light text
            "overflow-y": "auto",
            "box-shadow": "2px 0 5px rgba(0,0,0,0.1)",
            "z-index": 1000,
        }

        # Apply custom sidebar style overrides
        sidebar_style = {
            **default_sidebar_style,
            **(self.navigation.sidebar_style or {}),
        }

        # Default content area style with margin to avoid sidebar overlap
        default_content_style = {
            "margin-left": f"{sidebar_width + 1}rem",
            "margin-right": "2rem",
            "padding": "2rem 1rem",
            "min-height": "100vh",
            "background-color": "#ffffff",
        }

        # Apply custom content style overrides
        content_style = {
            **default_content_style,
            **(self.navigation.content_style or {}),
        }

        # Default nav link style
        default_nav_link_style = {
            "color": "#ecf0f1",
            "border-radius": "8px",
            "padding": "0.75rem 1rem",
            "transition": "all 0.3s ease",
        }

        # Apply custom nav link style overrides
        nav_link_style = {
            **default_nav_link_style,
            **(self.navigation.nav_link_style or {}),
        }

        # Default nav link className
        nav_link_className = self.navigation.nav_link_className or "mb-2"

        # Create navigation links with customizable styling
        nav_links = []
        for idx, section in enumerate(self.navigation.sections):
            # Apply active style if this is the active section
            if (
                idx == self.navigation.default_section
                and self.navigation.nav_link_active_style
            ):
                link_style = {**nav_link_style, **self.navigation.nav_link_active_style}
                link_className = (
                    self.navigation.nav_link_active_className or nav_link_className
                )
            else:
                link_style = nav_link_style
                link_className = nav_link_className

            nav_links.append(
                dbc.NavLink(
                    [
                        html.I(className="fas fa-chart-bar me-2"),  # Icon
                        section.title,
                    ],
                    id=f"nav-item-{idx}",
                    href=f"#section-{idx}",
                    active=idx == self.navigation.default_section,
                    n_clicks=0,
                    className=link_className,
                    style=link_style,
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
                html.Hr(style={"border-color": "#34495e", "margin": "1.5rem 0"}),
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

        # Content area for dynamic content
        content_area = html.Div(
            id="nav-content-area",
            children=[],
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
            # Navigation-specific callbacks
            if self.navigation:
                self._register_navigation_callbacks(app)

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
                Output(f"nav-item-{i}", "active")
                for i in range(len(self.navigation.sections))
            ],
            [
                Input(f"nav-item-{i}", "n_clicks")
                for i in range(len(self.navigation.sections))
            ],
            prevent_initial_call=False,
        )
        def update_navigation(*args):
            """
            Updates content area and navigation link states on user clicks.

            """
            ctx = callback_context

            # On initial call, load default section
            if not ctx.triggered or ctx.triggered[0]["prop_id"] == ".":
                section_idx = self.navigation.default_section
                self.logger.debug(f"Initial load: section {section_idx}")
            else:
                # Extract clicked item index from triggered id
                triggered_id = ctx.triggered[0]["prop_id"].split(".")[0]
                section_idx = int(triggered_id.split("-")[-1])
                self.logger.info(
                    f"Navigation click: switching to section {section_idx}"
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

            # Update active states for nav items
            active_states = [
                i == section_idx for i in range(len(self.navigation.sections))
            ]

            return [content, section_idx] + active_states

        self.logger.info("Navigation callbacks registered")
