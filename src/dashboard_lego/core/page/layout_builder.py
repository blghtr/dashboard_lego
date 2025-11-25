"""
Layout building methods for DashboardPage.

:hierarchy: [Core | Page | Layout Builder]
:complexity: 4
"""

from typing import TYPE_CHECKING, Any, Dict, Iterable, List, Tuple

import dash_bootstrap_components as dbc
from dash import html
from dash.development.base_component import Component

from dashboard_lego.core.exceptions import ConfigurationError

if TYPE_CHECKING:
    from dashboard_lego.blocks.base import BaseBlock


class LayoutBuilderMixin:
    """
    Mixin providing layout building methods for DashboardPage.

    :hierarchy: [Core | Page | Layout Builder | Mixin]
    :relates-to:
     - motivated_by: "Decomposition: Extract layout logic from DashboardPage"
     - implements: "Mixin: LayoutBuilderMixin"
     - uses: ["class: 'BaseBlock'", "component: 'dbc.Row'", "component: 'dbc.Col'"]

    :rationale: "Separates layout building concerns from core page logic."
    :contract:
     - pre: "Class has _CELL_ALLOWED_KEYS and _ROW_ALLOWED_KEYS attributes"
     - post: "Provides methods for normalizing, validating, and rendering layout structures"
    """

    # Layout validation constants (must be defined in class using this mixin)
    _CELL_ALLOWED_KEYS: set
    _ROW_ALLOWED_KEYS: set

    def _normalize_cell(
        self, cell_spec: Any, row_length: int
    ) -> Tuple["BaseBlock", Dict[str, Any]]:
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
        # Lazy import to avoid circular dependency
        from dashboard_lego.blocks.base import BaseBlock

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
        normalized: List[Tuple["BaseBlock", Dict[str, Any]]] = []
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
        row_cells: List[Tuple["BaseBlock", Dict[str, Any]]],
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
            row_kwargs["className"] = "mb-4 align-items-stretch"
        else:
            # Add align-items-stretch for equal height columns
            if "align-items-stretch" not in row_kwargs["className"]:
                row_kwargs["className"] += " align-items-stretch"

        return dbc.Row(cols, **row_kwargs)

    def _render_cell(self, block: "BaseBlock", options: Dict[str, Any]) -> Component:
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

        # Add h-100 for equal height columns in rows (unless user overrides)
        if "className" not in options:
            col_kwargs["className"] = "h-100"

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
                    # Merge h-100 with user className
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
