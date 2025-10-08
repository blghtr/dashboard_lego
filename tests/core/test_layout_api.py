"""
Unit tests for layout API helpers in DashboardPage.

    :hierarchy: [Unit Tests | Layouts | Helpers]
    :covers:
     - object: "method: _normalize_cell"
     - object: "method: _validate_row"
     - requirement: "LAYOUTS_IMPLEMENTATION_PLAN: Validation helpers"

    :scenario: "Normalize cells, validate rows, and ensure friendly errors."
    :strategy: "Use dummy blocks and assert option handling and errors."
    :contract:
     - pre: "Instantiate page with minimal layout"
     - post: "Helpers behave per spec"

"""

import pytest
from dash import html

from dashboard_lego.blocks.base import BaseBlock
from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.core.page import DashboardPage
from dashboard_lego.utils.exceptions import ConfigurationError


class _DummyBlock(BaseBlock):
    def __init__(self, block_id: str):
        super().__init__(block_id=block_id, datasource=_DummySource())
        self._layout = html.Div(block_id)

    def layout(self):
        return self._layout


class _DummySource(BaseDataSource):
    def _load_raw_data(self, params: dict):
        return None

    def get_filter_options(self, filter_name: str):
        return []

    def get_summary(self) -> str:
        return ""

    def get_kpis(self) -> dict:
        return {}


def test_validate_row_rejects_unknown_row_keys():
    a = _DummyBlock("a")
    page = DashboardPage(title="T", blocks=[[a]])
    with pytest.raises(ConfigurationError):
        page._validate_row(([a], {"weird": 1}))


def test_normalize_cell_assigns_default_width():
    a = _DummyBlock("a")
    page = DashboardPage(title="T", blocks=[[a]])
    block, opts = page._normalize_cell(a, row_length=3)
    assert block is a
    assert "width" in opts and 1 <= opts["width"] <= 12


def test_validate_row_enforces_breakpoint_sum():
    a = _DummyBlock("a")
    b = _DummyBlock("b")
    page = DashboardPage(title="T", blocks=[[a, b]])
    with pytest.raises(ConfigurationError):
        page._validate_row(([(a, {"md": 10}), (b, {"md": 6})], {}))
