"""
Tests for IPython magic functions.

Tests Dashboard Lego magic commands.

:hierarchy: [Tests | IPython | Magics]
:covers: "IPython magic functions for Dashboard Lego"
"""

from unittest.mock import Mock, patch

import pandas as pd
import pytest

pytest.importorskip("IPython")

from IPython.testing import tools as tt

from dashboard_lego.ipython_magics import DashboardMagics, load_ipython_extension


class TestDashboardThemeMagic:
    """Test %dashboard_theme magic."""

    @pytest.fixture
    def magics(self):
        """Create magic instance with mock shell."""
        shell = Mock()
        shell.user_ns = {}
        return DashboardMagics(shell)

    def test_theme_magic_shows_current(self, magics, capsys):
        """Test that calling without args shows current theme."""
        magics.shell.user_ns["_dashboard_theme"] = "cyborg"

        magics.dashboard_theme("")

        captured = capsys.readouterr()
        assert "Current theme: cyborg" in captured.out
        assert "Available themes:" in captured.out

    def test_theme_magic_sets_theme(self, magics, capsys):
        """Test that calling with theme name sets it."""
        magics.dashboard_theme("dark")

        assert magics.shell.user_ns["_dashboard_theme"] == "dark"

        captured = capsys.readouterr()
        assert "Theme set to: dark" in captured.out


class TestParseCellConfig:
    """Test cell configuration parser."""

    @pytest.fixture
    def magics(self):
        """Create magic instance."""
        shell = Mock()
        shell.user_ns = {}
        return DashboardMagics(shell)

    def test_parse_basic_config(self, magics):
        """Test parsing basic configuration."""
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

    def test_parse_metric_cards(self, magics):
        """Test parsing metric cards."""
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

    def test_parse_chart_cards(self, magics):
        """Test parsing chart cards."""
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

    def test_parse_text_cards(self, magics):
        """Test parsing text cards."""
        cell = """
dataframe: df
cards:
  - text: "## Summary\\n\\nKey insights"
        """

        config = magics._parse_cell_config(cell)

        assert len(config["cards"]) == 1
        assert config["cards"][0]["type"] == "text"
        assert "Summary" in config["cards"][0]["content"]

    def test_parse_mixed_cards(self, magics):
        """Test parsing multiple card types."""
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

    def test_parse_ignores_comments(self, magics):
        """Test that comments are ignored."""
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
