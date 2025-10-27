"""Tests for new IPython magic commands for Plotly export."""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from dashboard_lego.blocks.typed_chart import TypedChartBlock
from dashboard_lego.core import DataBuilder, DataSource
from dashboard_lego.ipython_magics import DashboardMagics


class MockDataBuilder(DataBuilder):
    def build(self, params):
        return pd.DataFrame({"x": [1, 2, 3], "y": [4, 5, 6]})


@pytest.fixture
def mock_datasource():
    return DataSource(data_builder=MockDataBuilder())


@pytest.fixture
def sample_chart(mock_datasource):
    return TypedChartBlock(
        block_id="test_chart",
        datasource=mock_datasource,
        plot_type="scatter",
        plot_params={"x": "x", "y": "y"},
        title="Test Chart",
    )


@pytest.fixture
def mock_shell(sample_chart):
    shell = MagicMock()
    shell.user_ns = {"test_chart": sample_chart, "_dashboard_theme": "lux"}
    # Make shell look like a proper IPython shell for traitlets
    shell.__class__.__name__ = "InteractiveShell"
    return shell


@pytest.fixture
def magics(mock_shell):
    # Create magics without calling super().__init__ to avoid traitlets issues
    magics = DashboardMagics.__new__(DashboardMagics)
    magics.shell = mock_shell
    # Initialize user namespace defaults
    if "_dashboard_theme" not in mock_shell.user_ns:
        mock_shell.user_ns["_dashboard_theme"] = "lux"
    if "_dashboard_processes" not in mock_shell.user_ns:
        mock_shell.user_ns["_dashboard_processes"] = {}
    return magics


class TestPlotlyExportMagic:
    def test_plotly_export_html_success(self, magics, sample_chart):
        """Test HTML export works correctly."""
        with tempfile.NamedTemporaryFile(suffix=".html", delete=False) as tmp:
            tmp_path = tmp.name

        try:
            # Mock get_figure to return a simple figure
            with patch.object(sample_chart, "get_figure", return_value=MagicMock()):
                magics.plotly_export(
                    f'test_chart --format html --output {tmp_path} --title "Test"'
                )

                # Check that get_figure was called
                sample_chart.get_figure.assert_called_once()

        finally:
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)

    def test_plotly_export_missing_output(self, magics):
        """Test error when output file not specified."""
        with patch("builtins.print") as mock_print:
            magics.plotly_export("test_chart --format html")
            mock_print.assert_called_with("❌ Error: --output/-o is required")

    def test_plotly_export_block_not_found(self, magics):
        """Test error when block variable not found."""
        with patch("builtins.print") as mock_print:
            magics.plotly_export("nonexistent_block --format html --output test.html")
            mock_print.assert_called_with(
                "❌ Error: Block variable 'nonexistent_block' not found"
            )

    def test_plotly_export_block_no_get_figure(self, magics, mock_shell):
        """Test error when block doesn't support figure export."""

        # Add a block without get_figure method
        class BadBlock:
            pass

        mock_shell.user_ns["bad_block"] = BadBlock()

        with patch("builtins.print") as mock_print:
            magics.plotly_export("bad_block --format html --output test.html")
            mock_print.assert_called_with(
                "❌ Error: Block 'bad_block' does not support figure export"
            )


class TestPlotlyShowMagic:
    def test_plotly_show_success(self, magics, sample_chart):
        """Test show magic works correctly."""
        with patch.object(
            sample_chart, "get_figure", return_value=MagicMock()
        ) as mock_get_figure:
            mock_fig = MagicMock()
            mock_get_figure.return_value = mock_fig

            magics.plotly_show('test_chart --title "Test Chart"')

            # Check that get_figure was called
            mock_get_figure.assert_called_once()

            # Check that show was called on the figure
            mock_fig.show.assert_called_once()

    def test_plotly_show_block_not_found(self, magics):
        """Test error when block variable not found."""
        with patch("builtins.print") as mock_print:
            magics.plotly_show("nonexistent_block")
            mock_print.assert_called_with(
                "❌ Error: Block variable 'nonexistent_block' not found"
            )


class TestPlotlyExportCellMagic:
    def test_plotly_export_cell_success(self, magics, sample_chart):
        """Test cell magic for batch export works."""
        cell_content = """
exports:
  - block: test_chart
    format: html
    output: test.html
    title: "Test Chart"
"""

        with patch.object(
            sample_chart, "get_figure", return_value=MagicMock()
        ) as mock_get_figure:
            mock_fig = MagicMock()
            mock_get_figure.return_value = mock_fig

            with patch("builtins.print") as mock_print:
                magics.plotly_export_cell("", cell_content)

                # Check that get_figure was called
                mock_get_figure.assert_called_once()

                # Check that write_html was called
                mock_fig.write_html.assert_called_once_with("test.html")

    def test_plotly_export_cell_no_exports(self, magics):
        """Test error when no exports in cell config."""
        cell_content = """
title: "Test"
"""

        with patch("builtins.print") as mock_print:
            magics.plotly_export_cell("", cell_content)
            mock_print.assert_called_with("❌ Error: No exports specified in cell")

    def test_plotly_export_cell_block_not_found(self, magics):
        """Test error when block not found in batch export."""
        cell_content = """
exports:
  - block: nonexistent_chart
    format: html
    output: test.html
"""

        with patch("builtins.print") as mock_print:
            magics.plotly_export_cell("", cell_content)
            # Should print error about block not found and continue
            assert any(
                "nonexistent_chart" in str(call) for call in mock_print.call_args_list
            )
