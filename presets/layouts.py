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

from typing import List, Sequence

from blocks.base import BaseBlock


def one_column(blocks: Sequence[BaseBlock]):
    """
    Single full-width column per row.

        :hierarchy: [Feature | Layout System | Presets | one_column]
        :relates-to:
         - motivated_by: "Common pattern for stacked content"
         - implements: "function: 'one_column'"
         - uses: ["interface: 'BaseBlock'"]

        :rationale: "Keeps content vertically stacked with consistent spacing."
        :contract:
         - pre: "blocks is a non-empty sequence of BaseBlock"
         - post: "Returns rows where each row contains a single full-width column"

    """
    return [[(block, {'md': 12})] for block in blocks]


def two_column_6_6(left: BaseBlock, right: BaseBlock):
    """
    Two equal columns on medium+ screens.

        :hierarchy: [Feature | Layout System | Presets | two_column_6_6]
        :relates-to:
         - motivated_by: "Balanced two-column layouts"
         - implements: "function: 'two_column_6_6'"
         - uses: ["interface: 'BaseBlock'"]

        :rationale: "Even split for symmetric content presentation."
        :contract:
         - pre: "left and right are BaseBlock"
         - post: "Returns a single row with two 6-unit columns"

    """
    return [[(left, {'md': 6}), (right, {'md': 6})]]


def two_column_8_4(main: BaseBlock, side: BaseBlock):
    """
    Main content with a narrower sidebar.

        :hierarchy: [Feature | Layout System | Presets | two_column_8_4]
        :relates-to:
         - motivated_by: "Content-first pages with secondary sidebar"
         - implements: "function: 'two_column_8_4'"
         - uses: ["interface: 'BaseBlock'"]

        :rationale: "Allocates more space to primary content."
        :contract:
         - pre: "main and side are BaseBlock"
         - post: "Returns a single row with 8/4 split"

    """
    return [[(main, {'md': 8}), (side, {'md': 4})]]


def three_column_4_4_4(a: BaseBlock, b: BaseBlock, c: BaseBlock):
    """
    Three equal columns on medium+ screens.

        :hierarchy: [Feature | Layout System | Presets | three_column_4_4_4]
        :relates-to:
         - motivated_by: "Cards in a 3-up grid"
         - implements: "function: 'three_column_4_4_4'"
         - uses: ["interface: 'BaseBlock'"]

        :rationale: "Common gallery and card layout."
        :contract:
         - pre: "a, b, c are BaseBlock"
         - post: "Returns a single row with 4/4/4 split"

    """
    return [[(a, {'md': 4}), (b, {'md': 4}), (c, {'md': 4})]]


def sidebar_main_3_9(side: BaseBlock, main: BaseBlock):
    """
    Narrow sidebar with wide main area.

        :hierarchy: [Feature | Layout System | Presets | sidebar_main_3_9]
        :relates-to:
         - motivated_by: "Classic dashboard layout"
         - implements: "function: 'sidebar_main_3_9'"
         - uses: ["interface: 'BaseBlock'"]

        :rationale: "Emphasizes content while providing space for filters or summaries."
        :contract:
         - pre: "side and main are BaseBlock"
         - post: "Returns a single row with 3/9 split"

    """
    return [[(side, {'md': 3}), (main, {'md': 9})]]


def kpi_row_top(kpi_blocks: Sequence[BaseBlock], content_rows: List[List[BaseBlock]]):
    """
    KPIs in a tight top row, with content rows below.

        :hierarchy: [Feature | Layout System | Presets | kpi_row_top]
        :relates-to:
         - motivated_by: "Dashboards commonly present KPIs on top"
         - implements: "function: 'kpi_row_top'"
         - uses: ["interface: 'BaseBlock'"]

        :rationale: "Provides a compact summary before detailed content."
        :contract:
         - pre: "kpi_blocks is a sequence, content_rows is a list of rows"
         - post: "Returns a layout with KPI row and appended content rows"

    """
    kpi_count = max(1, len(kpi_blocks))
    kpi_width = max(1, 12 // kpi_count)
    kpi_row = [[(k, {'md': kpi_width}) for k in kpi_blocks]]
    return kpi_row + [row for row in content_rows]




