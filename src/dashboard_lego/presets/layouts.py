"""
Layout presets for `DashboardPage` using the extended layout API.

    :hierarchy: [Feature | Layout System | Presets]
    :relates-to:
     - motivated_by: "Provide reusable, ergonomic layouts for common dashboard patterns"
     - implements: ["module: 'presets.layouts'"]
     - uses: ["class: 'BaseBlock'", "class: 'DashboardPage'"]

    :rationale: "Encapsulate frequently used grid structures to speed up page assembly."
    :contract:
     - pre: "Functions receive blocks (BaseBlock instances)"
     - post: "Functions return a list-of-rows compatible with DashboardPage layout API"

"""

from typing import Any, Dict, List, Optional, Sequence

from dashboard_lego.blocks.base import BaseBlock


def one_column(
    blocks: Sequence[BaseBlock],
    *,
    block_options: Optional[Dict[str, Any]] = None,
    row_options: Optional[Dict[str, Any]] = None,
):
    """
    Single full-width column per row with customizable options.

        :hierarchy: [Feature | Layout System | Presets | one_column]
        :relates-to:
         - motivated_by: "Common pattern for stacked content with customization"
         - implements: "function: 'one_column' with options"
         - uses: ["interface: 'BaseBlock'"]

        :rationale: "Keeps content vertically stacked with consistent spacing and
         customizable styling options."
        :contract:
         - pre: "blocks is a non-empty sequence of BaseBlock"
         - post: "Returns rows where each row contains a single full-width column
           with applied options"

    Args:
        blocks: Sequence of BaseBlock instances to display
        block_options: Optional options to apply to each block (style, className, etc.)
        row_options: Optional options to apply to each row (g, align, justify, etc.)

    """
    block_opts = {"md": 12, **(block_options or {})}
    rows = [[(block, block_opts)] for block in blocks]

    if row_options:
        return [(row, row_options) for row in rows]
    return rows


def two_column_6_6(
    left: BaseBlock,
    right: BaseBlock,
    *,
    left_options: Optional[Dict[str, Any]] = None,
    right_options: Optional[Dict[str, Any]] = None,
    row_options: Optional[Dict[str, Any]] = None,
):
    """
    Two equal columns on medium+ screens with customizable options.

        :hierarchy: [Feature | Layout System | Presets | two_column_6_6]
        :relates-to:
         - motivated_by: "Balanced two-column layouts with customization"
         - implements: "function: 'two_column_6_6' with options"
         - uses: ["interface: 'BaseBlock'"]

        :rationale: "Even split for symmetric content presentation with
         customizable styling options."
        :contract:
         - pre: "left and right are BaseBlock"
         - post: "Returns a single row with two 6-unit columns with applied options"

    Args:
        left: Left column block
        right: Right column block
        left_options: Optional options for left column (style, className, etc.)
        right_options: Optional options for right column (style, className, etc.)
        row_options: Optional options for the row (g, align, justify, etc.)

    """
    left_opts = {"md": 6, **(left_options or {})}
    right_opts = {"md": 6, **(right_options or {})}

    row = [(left, left_opts), (right, right_opts)]

    if row_options:
        return [(row, row_options)]
    return [row]


def two_column_8_4(
    main: BaseBlock,
    side: BaseBlock,
    *,
    main_options: Optional[Dict[str, Any]] = None,
    side_options: Optional[Dict[str, Any]] = None,
    row_options: Optional[Dict[str, Any]] = None,
):
    """
    Main content with a narrower sidebar with customizable options.

        :hierarchy: [Feature | Layout System | Presets | two_column_8_4]
        :relates-to:
         - motivated_by: "Content-first pages with secondary sidebar and customization"
         - implements: "function: 'two_column_8_4' with options"
         - uses: ["interface: 'BaseBlock'"]

        :rationale: "Allocates more space to primary content with customizable
         styling options."
        :contract:
         - pre: "main and side are BaseBlock"
         - post: "Returns a single row with 8/4 split with applied options"

    Args:
        main: Main content block
        side: Sidebar block
        main_options: Optional options for main column (style, className, etc.)
        side_options: Optional options for side column (style, className, etc.)
        row_options: Optional options for the row (g, align, justify, etc.)

    """
    main_opts = {"md": 8, **(main_options or {})}
    side_opts = {"md": 4, **(side_options or {})}

    row = [(main, main_opts), (side, side_opts)]

    if row_options:
        return [(row, row_options)]
    return [row]


def three_column_4_4_4(
    a: BaseBlock,
    b: BaseBlock,
    c: BaseBlock,
    *,
    a_options: Optional[Dict[str, Any]] = None,
    b_options: Optional[Dict[str, Any]] = None,
    c_options: Optional[Dict[str, Any]] = None,
    row_options: Optional[Dict[str, Any]] = None,
):
    """
    Three equal columns on medium+ screens with customizable options.

        :hierarchy: [Feature | Layout System | Presets | three_column_4_4_4]
        :relates-to:
         - motivated_by: "Cards in a 3-up grid with customization"
         - implements: "function: 'three_column_4_4_4' with options"
         - uses: ["interface: 'BaseBlock'"]

        :rationale: "Common gallery and card layout with customizable styling options."
        :contract:
         - pre: "a, b, c are BaseBlock"
         - post: "Returns a single row with 4/4/4 split with applied options"

    Args:
        a: First column block
        b: Second column block
        c: Third column block
        a_options: Optional options for first column (style, className, etc.)
        b_options: Optional options for second column (style, className, etc.)
        c_options: Optional options for third column (style, className, etc.)
        row_options: Optional options for the row (g, align, justify, etc.)

    """
    a_opts = {"md": 4, **(a_options or {})}
    b_opts = {"md": 4, **(b_options or {})}
    c_opts = {"md": 4, **(c_options or {})}

    row = [(a, a_opts), (b, b_opts), (c, c_opts)]

    if row_options:
        return [(row, row_options)]
    return [row]


def sidebar_main_3_9(
    side: BaseBlock,
    main: BaseBlock,
    *,
    side_options: Optional[Dict[str, Any]] = None,
    main_options: Optional[Dict[str, Any]] = None,
    row_options: Optional[Dict[str, Any]] = None,
):
    """
    Narrow sidebar with wide main area with customizable options.

        :hierarchy: [Feature | Layout System | Presets | sidebar_main_3_9]
        :relates-to:
         - motivated_by: "Classic dashboard layout with customization"
         - implements: "function: 'sidebar_main_3_9' with options"
         - uses: ["interface: 'BaseBlock'"]

        :rationale: "Emphasizes content while providing space for filters or summaries
         with customizable styling options."
        :contract:
         - pre: "side and main are BaseBlock"
         - post: "Returns a single row with 3/9 split with applied options"

    Args:
        side: Sidebar block
        main: Main content block
        side_options: Optional options for sidebar column (style, className, etc.)
        main_options: Optional options for main column (style, className, etc.)
        row_options: Optional options for the row (g, align, justify, etc.)

    """
    side_opts = {"md": 3, **(side_options or {})}
    main_opts = {"md": 9, **(main_options or {})}

    row = [(side, side_opts), (main, main_opts)]

    if row_options:
        return [(row, row_options)]
    return [row]


def kpi_row_top(
    kpi_blocks: Sequence[BaseBlock],
    content_rows: List[List[BaseBlock]],
    *,
    kpi_options: Optional[Dict[str, Any]] = None,
    kpi_row_options: Optional[Dict[str, Any]] = None,
    content_row_options: Optional[Dict[str, Any]] = None,
):
    """
    KPIs in a tight top row, with content rows below with customizable options.

        :hierarchy: [Feature | Layout System | Presets | kpi_row_top]
        :relates-to:
         - motivated_by: "Dashboards commonly present KPIs on top with customization"
         - implements: "function: 'kpi_row_top' with options"
         - uses: ["interface: 'BaseBlock'"]

        :rationale: "Provides a compact summary before detailed content with
         customizable styling options."
        :contract:
         - pre: "kpi_blocks is a sequence, content_rows is a list of rows"
         - post: "Returns a layout with KPI row and appended content rows with applied options"

    Args:
        kpi_blocks: Sequence of KPI blocks to display in the top row
        content_rows: List of content rows to display below KPIs
        kpi_options: Optional options to apply to each KPI block (style, className, etc.)
        kpi_row_options: Optional options for the KPI row (g, align, justify, etc.)
        content_row_options: Optional options for content rows (g, align, justify, etc.)

    """
    kpi_count = max(1, len(kpi_blocks))
    kpi_width = max(1, 12 // kpi_count)

    # Build KPI row with options
    kpi_opts = {"md": kpi_width, **(kpi_options or {})}
    kpi_row = [(k, kpi_opts) for k in kpi_blocks]

    # Apply row options if provided
    if kpi_row_options:
        kpi_row = (kpi_row, kpi_row_options)
    else:
        kpi_row = [kpi_row]

    # Process content rows
    processed_content_rows = []
    for row in content_rows:
        if content_row_options:
            processed_content_rows.append((row, content_row_options))
        else:
            processed_content_rows.append(row)

    return kpi_row + processed_content_rows
