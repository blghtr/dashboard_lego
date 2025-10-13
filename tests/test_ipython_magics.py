"""
Tests for IPython magic functions.

Tests Dashboard Lego magic commands.

:hierarchy: [Tests | IPython | Magics]
:covers: "IPython magic functions for Dashboard Lego"

Note: Magic command tests require real IPython shell and are tested manually.
      These unit tests only cover the load_extension function.
"""

from unittest.mock import Mock

import pytest

pytest.importorskip("IPython")

from dashboard_lego.ipython_magics import load_ipython_extension


@pytest.mark.skip(
    reason="DashboardMagics requires real IPython shell (traitlets validation)"
)
class TestParseCellConfig:
    """Test cell configuration parser (without creating Magics instance)."""

    def test_parse_basic_config(self):
        """Test parsing basic configuration."""
        from dashboard_lego.ipython_magics import DashboardMagics

        # Create mock shell with minimal attributes
        shell = Mock()
        shell.user_ns = {}
        shell.configurables = []

        # Test _parse_cell_config directly
        magics = DashboardMagics(shell)

        cell = """
dataframe: df
title: "My Dashboard"
theme: lux
port: 8050
        """

        config = magics._parse_cell_config(cell)

        assert config["dataframe"] == "df"
        assert config["title"] == "My Dashboard"
        assert config["theme"] == "lux"
        assert config["port"] == 8050

    def test_parse_metric_cards(self):
        """Test parsing metric cards."""
        from dashboard_lego.ipython_magics import DashboardMagics

        shell = Mock()
        shell.user_ns = {}
        shell.configurables = []

        magics = DashboardMagics(shell)

        cell = """
dataframe: df
cards:
  - metric: Sales, sum, "Total Sales", success
  - metric: Revenue, mean, "Avg Revenue"
        """

        config = magics._parse_cell_config(cell)

        assert len(config["cards"]) == 2
        assert config["cards"][0]["type"] == "metric"
        assert config["cards"][0]["column"] == "Sales"
        assert config["cards"][0]["agg"] == "sum"
        assert config["cards"][0]["title"] == "Total Sales"
        assert config["cards"][0]["color"] == "success"

        # Second metric with default color
        assert config["cards"][1]["color"] == "primary"

    def test_parse_chart_cards(self):
        """Test parsing chart cards."""
        from dashboard_lego.ipython_magics import DashboardMagics

        shell = Mock()
        shell.user_ns = {}
        shell.configurables = []

        magics = DashboardMagics(shell)

        cell = """
dataframe: df
cards:
  - chart: bar, Product, Sales, "Sales Chart"
        """

        config = magics._parse_cell_config(cell)

        assert len(config["cards"]) == 1
        assert config["cards"][0]["type"] == "chart"
        assert config["cards"][0]["plot_type"] == "bar"
        assert config["cards"][0]["x"] == "Product"
        assert config["cards"][0]["y"] == "Sales"
        assert config["cards"][0]["title"] == "Sales Chart"

    def test_parse_text_cards(self):
        """Test parsing text cards with newlines."""
        from dashboard_lego.ipython_magics import DashboardMagics

        shell = Mock()
        shell.user_ns = {}
        shell.configurables = []

        magics = DashboardMagics(shell)

        cell = """
dataframe: df
cards:
  - text: "## Summary\\n\\nKey insights"
        """

        config = magics._parse_cell_config(cell)

        assert len(config["cards"]) == 1
        assert config["cards"][0]["type"] == "text"
        # Check that \n was converted to actual newline
        assert "\n" in config["cards"][0]["content"]
        assert "Summary" in config["cards"][0]["content"]

    def test_parse_mixed_cards(self):
        """Test parsing multiple card types."""
        from dashboard_lego.ipython_magics import DashboardMagics

        shell = Mock()
        shell.user_ns = {}
        shell.configurables = []

        magics = DashboardMagics(shell)

        cell = """
dataframe: df
title: "Mixed Dashboard"
cards:
  - metric: Sales, sum, "Total"
  - chart: bar, Product, Sales, "Chart"
  - text: "Text content"
        """

        config = magics._parse_cell_config(cell)

        assert len(config["cards"]) == 3
        assert config["cards"][0]["type"] == "metric"
        assert config["cards"][1]["type"] == "chart"
        assert config["cards"][2]["type"] == "text"

    def test_parse_ignores_comments(self):
        """Test that comments are ignored."""
        from dashboard_lego.ipython_magics import DashboardMagics

        shell = Mock()
        shell.user_ns = {}
        shell.configurables = []

        magics = DashboardMagics(shell)

        cell = """
# This is a comment
dataframe: df
# Another comment
cards:
  # Comment before card
  - metric: Sales, sum, "Total"
        """

        config = magics._parse_cell_config(cell)

        assert config["dataframe"] == "df"
        assert len(config["cards"]) == 1


class TestLoadExtension:
    """Test extension loading."""

    def test_load_extension_registers_magics(self, capsys):
        """Test that load_ipython_extension registers magics."""
        mock_ipython = Mock()

        load_ipython_extension(mock_ipython)

        # Should call register_magics
        assert mock_ipython.register_magics.called

        # Should print success message
        captured = capsys.readouterr()
        assert "Dashboard Lego magics loaded" in captured.out
