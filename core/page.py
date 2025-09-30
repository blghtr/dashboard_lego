"""
This module defines the DashboardPage class, which orchestrates blocks on a page.

"""
from typing import List, Any, Dict, Tuple, Optional, Iterable, Union

import dash_bootstrap_components as dbc
from dash import html
from dash.development.base_component import Component

from blocks.base import BaseBlock
from core.state import StateManager
from utils.logger import get_logger
from utils.exceptions import ConfigurationError

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
        blocks: List[List[Any]],
        theme: str = dbc.themes.BOOTSTRAP
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
            theme: An optional URL to a dash-bootstrap-components theme
                   (e.g., dbc.themes.CYBORG).

        """
        self.logger = get_logger(__name__, DashboardPage)
        self.logger.info(f"Initializing dashboard page: '{title}'")
        
        self.title = title
        self.theme = theme
        self.layout_structure = blocks
        self.state_manager = StateManager()

        # Flatten the structure to get all block instances for registration
        self.blocks: List[BaseBlock] = []
        try:
            for row_idx, row in enumerate(self.layout_structure):
                # Handle both old format (list of blocks) and new format (tuple of (list, dict))
                if isinstance(row, tuple) and len(row) == 2:
                    # New format: (list_of_blocks, row_options)
                    blocks_list = row[0]
                else:
                    # Old format: list of blocks
                    blocks_list = row
                
                self.logger.debug(f"Processing row {row_idx} with {len(blocks_list)} blocks")
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
        self.logger.debug(f"Registering {len(self.blocks)} blocks with state manager")
        for block in self.blocks:
            self.logger.debug(f"Registering block: {block.block_id}")
            block._register_state_interactions(self.state_manager)

    # --- Layout v2: helper constants ---
    _CELL_ALLOWED_KEYS: set = {
        'width', 'xs', 'sm', 'md', 'lg', 'xl', 'offset', 'align', 'className', 'style', 'children'
    }

    _ROW_ALLOWED_KEYS: set = {'align', 'justify', 'g', 'className', 'style'}

    def _normalize_cell(
        self,
        cell_spec: Any,
        row_length: int
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
        if not any(k in options for k in ['width', 'xs', 'sm', 'md', 'lg', 'xl']):
            # Equal split; ensure at least 1
            options['width'] = max(1, 12 // max(1, row_length))

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
        if isinstance(row_spec, tuple) and len(row_spec) == 2 and isinstance(row_spec[1], dict):
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
            for key in ['width', 'xs', 'sm', 'md', 'lg', 'xl']:
                if key in options:
                    value = options[key]
                    if not isinstance(value, int) or value < 1 or value > 12:
                        raise ConfigurationError(
                            f"Invalid width for '{key}': {value}. Must be an integer 1..12"
                        )
            normalized.append((block, options))

        # Validate that explicit breakpoint sums do not exceed 12
        for bp in ['width', 'xs', 'sm', 'md', 'lg', 'xl']:
            bp_sum = sum(opts.get(bp, 0) for _, opts in normalized if bp in opts)
            if bp_sum and bp_sum > 12:
                raise ConfigurationError(
                    f"Sum of column widths for breakpoint '{bp}' exceeds 12: {bp_sum}"
                )

        # Return cells back in their original representation (block, options)
        return [(b, o) for b, o in normalized], row_options

    def _render_row(
        self, row_cells: List[Tuple[BaseBlock, Dict[str, Any]]], row_options: Dict[str, Any]
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
        if 'g' in row_options:
            gap = row_options['g']
            if isinstance(gap, int):
                row_kwargs['className'] = f"g-{gap}"
            else:
                row_kwargs['className'] = f"g-{gap}"
        
        # Handle other row options
        for key in ['align', 'justify', 'className', 'style']:
            if key in row_options:
                if key == 'className' and 'className' in row_kwargs:
                    # Merge gap class with existing className
                    row_kwargs['className'] = f"{row_kwargs['className']} {row_options[key]}"
                else:
                    row_kwargs[key] = row_options[key]
        
        # Keep legacy spacing class unless overridden
        if 'className' not in row_kwargs:
            row_kwargs['className'] = 'mb-4'
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
        if 'offset' in options:
            offset = options['offset']
            if isinstance(offset, int):
                col_kwargs['className'] = f"offset-{offset}"
            else:
                col_kwargs['className'] = f"offset-{offset}"
        
        # Handle other column options
        for key in ['width', 'xs', 'sm', 'md', 'lg', 'xl', 'align', 'className', 'style']:
            if key in options:
                if key == 'className' and 'className' in col_kwargs:
                    # Merge offset class with existing className
                    col_kwargs['className'] = f"{col_kwargs['className']} {options[key]}"
                else:
                    col_kwargs[key] = options[key]

        content_children: List[Component] = []
        # Primary block content
        content_children.append(block.layout())

        # Nested rows if provided
        children_rows = options.get('children')
        if children_rows:
            if not isinstance(children_rows, Iterable) or isinstance(children_rows, (str, bytes)):
                raise ConfigurationError("'children' must be a list of row specs")
            for child_row in children_rows:
                normalized_child_cells, child_row_opts = self._validate_row(child_row)
                content_children.append(self._render_row(normalized_child_cells, child_row_opts))

        # If only one child, pass directly; else wrap
        col_content: Component = content_children[0] if len(content_children) == 1 else html.Div(content_children)
        return dbc.Col(col_content, **col_kwargs)

    def build_layout(self) -> Component:
        """
        Assembles the layouts from all blocks into a grid-based page layout.

        Returns:
            A Dash component representing the entire page.

        """
        self.logger.info("Building page layout")
        self.logger.debug(f"Building layout: {len(self.layout_structure)} rows, {len(self.blocks)} blocks")
        rows: List[Component] = []
        
        try:
            for row_idx, row_spec in enumerate(self.layout_structure):
                # Validate and normalize the row and its cells
                normalized_cells, row_options = self._validate_row(row_spec)

                self.logger.debug(
                    f"Rendering row {row_idx} with {len(normalized_cells)} cells and options {row_options}"
                )
                rows.append(self._render_row(normalized_cells, row_options))

            self.logger.info(
                f"Layout built successfully: {len(rows)} rows rendered"
            )
            return dbc.Container(
                [
                    html.H1(self.title, className="my-4"),
                    *rows
                ],
                fluid=True
            )
        except Exception as e:
            self.logger.error(f"Error building layout: {e}", exc_info=True)
            raise

    def register_callbacks(self, app: Any):
        """
        Registers callbacks using both old (state-based) and new (block-centric) mechanisms.
        
        :hierarchy: [Architecture | Callback Registration | DashboardPage]
        :relates-to:
         - motivated_by: "ARCHITECTURE_REFACTOR_PLAN Step 4: Hybrid callback system"
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
            # OLD MECHANISM: State-based callbacks for StaticChartBlock
            self.state_manager.generate_callbacks(app)
            
            # NEW MECHANISM: Block-centric callbacks for InteractiveChartBlock
            self.state_manager.bind_callbacks(app, self.blocks)
            
            self.logger.info("Callbacks registered successfully")
        except Exception as e:
            self.logger.error(
                f"Error registering callbacks: {e}", exc_info=True
            )
            raise
