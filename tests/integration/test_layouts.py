"""
Integration tests for layout presets and page rendering.

    :hierarchy: [Integration Tests | Layouts]
    :covers:
     - object: "class: DashboardPage"
     - requirement: "LAYOUTS_IMPLEMENTATION_PLAN: Presets and responsive rendering"

    :scenario: "Build pages using presets and assert dbc.Row/Col structure and props."
    :strategy: "Instantiate lightweight mock blocks and verify Dash components."
    :contract:
     - pre: "Create blocks and compose with presets"
     - post: "The built layout contains expected rows, columns, and properties"

"""

from typing import Any

from dash import html

from dashboard_lego.blocks.base import BaseBlock
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.core.page import DashboardPage
from dashboard_lego.presets.layouts import (
    kpi_row_top,
    one_column,
    sidebar_main_3_9,
    three_column_4_4_4,
    two_column_6_6,
    two_column_8_4,
)


class _DummyBlock(BaseBlock):
    def __init__(self, block_id: str):
        super().__init__(block_id=block_id, datasource=_DummySource())
        self._layout = html.Div(block_id)

    def layout(self):
        return self._layout


class _DummySource(DataSource):
    def _load_raw_data(self, params: dict):
        return None

    def get_filter_options(self, filter_name: str):
        return []

    def get_summary(self) -> str:
        return ""

    def get_kpis(self) -> dict:
        return {}


def test_two_column_8_4_layout_builds_correct_structure():
    main = _DummyBlock("main")
    side = _DummyBlock("side")

    layout_spec = two_column_8_4(main, side)
    page = DashboardPage(title="Test", blocks=layout_spec)
    container = page.build_layout()

    rows = container.children[1:]
    assert len(rows) == 1
    cols = rows[0].children
    assert len(cols) == 2
    assert cols[0].md == 8
    assert cols[1].md == 4


def test_kpi_row_top_distributes_widths_evenly():
    k1, k2, k3 = _DummyBlock("k1"), _DummyBlock("k2"), _DummyBlock("k3")
    content = one_column([_DummyBlock("c1")])

    layout_spec = kpi_row_top([k1, k2, k3], content)
    page = DashboardPage(title="Test", blocks=layout_spec)
    container = page.build_layout()

    rows = container.children[1:]
    assert len(rows) >= 2
    kpi_cols = rows[0].children
    assert len(kpi_cols) == 3
    assert all(getattr(col, "md", 0) == 4 for col in kpi_cols)
