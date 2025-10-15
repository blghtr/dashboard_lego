"""Integration tests for layout export functionality."""

import pandas as pd
import plotly.graph_objects as go
import pytest

from dashboard_lego.blocks.typed_chart import TypedChartBlock
from dashboard_lego.core import BaseDataSource, DataBuilder
from dashboard_lego.utils.layout_export import export_layout_to_figure


class SampleDataBuilder(DataBuilder):
    def build(self, params):
        return pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})


@pytest.fixture
def sample_datasource():
    return BaseDataSource(data_builder=SampleDataBuilder())


def test_export_single_row_layout(sample_datasource):
    """Test exporting layout with single row."""
    chart1 = TypedChartBlock(
        block_id="chart1",
        datasource=sample_datasource,
        plot_type="scatter",
        plot_params={"x": "x", "y": "y"},
        title="Chart 1",
    )
    chart2 = TypedChartBlock(
        block_id="chart2",
        datasource=sample_datasource,
        plot_type="bar",
        plot_params={"x": "x", "y": "y"},
        title="Chart 2",
    )

    layout = [[chart1, chart2]]
    fig = export_layout_to_figure(layout)

    assert isinstance(fig, go.Figure)
    assert len(fig.data) >= 2  # At least 2 traces


def test_export_multi_row_layout(sample_datasource):
    """Test exporting layout with multiple rows."""
    charts = [
        TypedChartBlock(
            block_id=f"chart{i}",
            datasource=sample_datasource,
            plot_type="scatter",
            plot_params={"x": "x", "y": "y"},
        )
        for i in range(3)
    ]

    layout = [[charts[0], charts[1]], [charts[2]]]
    fig = export_layout_to_figure(layout, title="Test Dashboard")

    assert isinstance(fig, go.Figure)
    assert fig.layout.title.text == "Test Dashboard"


def test_export_skips_non_chart_blocks(sample_datasource):
    """Test that non-chart blocks are skipped."""
    from dashboard_lego.blocks.text import TextBlock

    chart = TypedChartBlock(
        block_id="chart",
        datasource=sample_datasource,
        plot_type="scatter",
        plot_params={"x": "x", "y": "y"},
    )
    text = TextBlock(
        block_id="text",
        datasource=sample_datasource,
        content_generator=lambda df: "Some text",
    )

    layout = [[chart, text]]  # Mixed blocks
    fig = export_layout_to_figure(layout)

    assert isinstance(fig, go.Figure)
    # Should only have chart traces, text block skipped
