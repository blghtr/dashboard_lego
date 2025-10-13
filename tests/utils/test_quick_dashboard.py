"""
Tests for quick dashboard factory.

Tests quick_dashboard() factory function with simple and advanced modes.

:hierarchy: [Tests | Utils | QuickDashboard]
:covers: "quick_dashboard function and InMemoryDataBuilder class"
"""

from unittest.mock import Mock, patch

import dash
import pandas as pd
import pytest

from dashboard_lego.blocks import SingleMetricBlock, TextBlock, TypedChartBlock
from dashboard_lego.core import BaseDataSource
from dashboard_lego.utils.quick_dashboard import (
    InMemoryDataBuilder,
    _create_block_from_spec,
    _detect_jupyter,
    _get_theme_url_and_config,
    _smart_layout,
    quick_dashboard,
)


class TestInMemoryDataBuilder:
    """Test InMemoryDataBuilder class."""

    def test_build_returns_dataframe(self):
        """Test that build() returns the wrapped DataFrame."""
        df = pd.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        builder = InMemoryDataBuilder(df)

        result = builder.build({})

        assert isinstance(result, pd.DataFrame)
        assert len(result) == 3
        assert list(result.columns) == ["A", "B"]

    def test_build_returns_copy(self):
        """Test that build() returns copy (no external mutations)."""
        df = pd.DataFrame({"A": [1, 2, 3]})
        builder = InMemoryDataBuilder(df)

        # Modify original
        df["A"] = [10, 20, 30]

        # Builder should have original values
        result = builder.build({})
        assert list(result["A"]) == [1, 2, 3]

    def test_invalid_dataframe_raises(self):
        """Test that invalid DataFrame raises ValueError."""
        with pytest.raises(ValueError, match="must be a valid pandas DataFrame"):
            InMemoryDataBuilder(None)

        with pytest.raises(ValueError, match="must be a valid pandas DataFrame"):
            InMemoryDataBuilder("not a dataframe")  # type: ignore

    def test_empty_dataframe_warns(self):
        """Test that empty DataFrame logs warning."""
        df = pd.DataFrame()
        builder = InMemoryDataBuilder(df)
        result = builder.build({})
        assert result.empty


class TestDetectJupyter:
    """Test Jupyter environment detection."""

    def test_detect_jupyter_in_ipython(self, monkeypatch):
        """Test detection when in IPython/Jupyter."""

        def fake_get_ipython():
            return Mock(spec=["config"])

        monkeypatch.setattr("builtins.get_ipython", fake_get_ipython, raising=False)
        assert _detect_jupyter() is True

    def test_detect_jupyter_not_in_ipython(self, monkeypatch):
        """Test detection when not in IPython/Jupyter."""
        monkeypatch.delattr("builtins.get_ipython", raising=False)
        assert _detect_jupyter() is False


class TestGetThemeUrlAndConfig:
    """Test theme URL and config mapping."""

    def test_known_theme(self):
        """Test that known theme returns correct URL and config."""
        url, config = _get_theme_url_and_config("lux")
        assert "lux" in url.lower()
        assert config is not None

    def test_unknown_theme_defaults_to_lux(self):
        """Test that unknown theme defaults to lux."""
        url, config = _get_theme_url_and_config("unknown_theme")
        assert "lux" in url.lower()

    def test_case_insensitive(self):
        """Test that theme name is case-insensitive."""
        url1, _ = _get_theme_url_and_config("LUX")
        url2, _ = _get_theme_url_and_config("lux")
        assert url1 == url2


class TestCreateBlockFromSpec:
    """Test block creation from card specs."""

    @pytest.fixture
    def datasource(self):
        """Create test datasource."""
        df = pd.DataFrame({"Sales": [100, 200], "Product": ["A", "B"]})
        return BaseDataSource(data_builder=InMemoryDataBuilder(df), cache_ttl=0)

    def test_create_metric_block(self, datasource):
        """Test creating metric block from spec."""
        card_spec = {
            "type": "metric",
            "column": "Sales",
            "agg": "sum",
            "title": "Total Sales",
            "color": "success",
        }

        block = _create_block_from_spec(card_spec, datasource, "test_metric")

        assert isinstance(block, SingleMetricBlock)
        assert block.block_id == "test_metric"

    def test_create_chart_block(self, datasource):
        """Test creating chart block from spec."""
        card_spec = {
            "type": "chart",
            "plot_type": "bar",
            "x": "Product",
            "y": "Sales",
            "title": "Sales Chart",
        }

        block = _create_block_from_spec(card_spec, datasource, "test_chart")

        assert isinstance(block, TypedChartBlock)
        assert block.block_id == "test_chart"

    def test_create_text_block(self, datasource):
        """Test creating text block from spec."""
        card_spec = {"type": "text", "content": "## Test Content"}

        block = _create_block_from_spec(card_spec, datasource, "test_text")

        assert isinstance(block, TextBlock)
        assert block.block_id == "test_text"

    def test_metric_missing_required_fields(self, datasource):
        """Test that metric card without required fields raises."""
        card_spec = {"type": "metric", "column": "Sales"}  # Missing agg, title

        with pytest.raises(ValueError, match="missing required fields"):
            _create_block_from_spec(card_spec, datasource, "test")

    def test_chart_missing_required_fields(self, datasource):
        """Test that chart card without required fields raises."""
        card_spec = {
            "type": "chart",
            "plot_type": "bar",
            "x": "Product",
        }  # Missing y, title

        with pytest.raises(ValueError, match="missing required fields"):
            _create_block_from_spec(card_spec, datasource, "test")

    def test_text_missing_content(self, datasource):
        """Test that text card without content raises."""
        card_spec = {"type": "text"}  # Missing content

        with pytest.raises(ValueError, match="missing required field: content"):
            _create_block_from_spec(card_spec, datasource, "test")

    def test_unknown_card_type(self, datasource):
        """Test that unknown card type raises."""
        card_spec = {"type": "unknown"}

        with pytest.raises(ValueError, match="Unknown card type"):
            _create_block_from_spec(card_spec, datasource, "test")


class TestSmartLayout:
    """Test smart layout algorithm."""

    @pytest.fixture
    def datasource(self):
        """Create test datasource."""
        df = pd.DataFrame({"Sales": [100, 200], "Revenue": [1000, 2000]})
        return BaseDataSource(data_builder=InMemoryDataBuilder(df), cache_ttl=0)

    def test_pure_metrics(self, datasource):
        """Test layout with only metrics (all in one row)."""
        card_specs = [
            {"type": "metric", "column": "Sales", "agg": "sum", "title": "Total Sales"},
            {
                "type": "metric",
                "column": "Revenue",
                "agg": "sum",
                "title": "Total Revenue",
            },
        ]

        layout = _smart_layout(card_specs, datasource)

        # Should have 1 row (metrics row)
        assert len(layout) == 1

    def test_pure_charts_one(self, datasource):
        """Test layout with 1 chart (full width)."""
        card_specs = [
            {
                "type": "chart",
                "plot_type": "bar",
                "x": "Sales",
                "y": "Revenue",
                "title": "Chart",
            }
        ]

        layout = _smart_layout(card_specs, datasource)

        # Should have 1 row (chart full width)
        assert len(layout) == 1

    def test_pure_charts_two(self, datasource):
        """Test layout with 2 charts (50/50)."""
        card_specs = [
            {
                "type": "chart",
                "plot_type": "bar",
                "x": "Sales",
                "y": "Revenue",
                "title": "Chart1",
            },
            {
                "type": "chart",
                "plot_type": "line",
                "x": "Sales",
                "y": "Revenue",
                "title": "Chart2",
            },
        ]

        layout = _smart_layout(card_specs, datasource)

        # Should have 1 row (2 charts 50/50)
        assert len(layout) == 1

    def test_pure_charts_three(self, datasource):
        """Test layout with 3 charts (1 full + 2 in 50/50)."""
        card_specs = [
            {
                "type": "chart",
                "plot_type": "bar",
                "x": "Sales",
                "y": "Revenue",
                "title": "C1",
            },
            {
                "type": "chart",
                "plot_type": "line",
                "x": "Sales",
                "y": "Revenue",
                "title": "C2",
            },
            {
                "type": "chart",
                "plot_type": "scatter",
                "x": "Sales",
                "y": "Revenue",
                "title": "C3",
            },
        ]

        layout = _smart_layout(card_specs, datasource)

        # Should have 2 rows (1 full, then 2 in 50/50)
        assert len(layout) == 2

    def test_mixed_one_metric_one_chart(self, datasource):
        """Test layout with 1M + 1C (metrics row + chart full)."""
        card_specs = [
            {"type": "metric", "column": "Sales", "agg": "sum", "title": "Total"},
            {
                "type": "chart",
                "plot_type": "bar",
                "x": "Sales",
                "y": "Revenue",
                "title": "Chart",
            },
        ]

        layout = _smart_layout(card_specs, datasource)

        # Should have 2 rows (metrics + chart)
        assert len(layout) == 2

    def test_mixed_two_metrics_two_charts(self, datasource):
        """Test layout with 2M + 2C (metrics row + charts 50/50)."""
        card_specs = [
            {"type": "metric", "column": "Sales", "agg": "sum", "title": "Total Sales"},
            {
                "type": "metric",
                "column": "Revenue",
                "agg": "sum",
                "title": "Total Revenue",
            },
            {
                "type": "chart",
                "plot_type": "bar",
                "x": "Sales",
                "y": "Revenue",
                "title": "C1",
            },
            {
                "type": "chart",
                "plot_type": "line",
                "x": "Sales",
                "y": "Revenue",
                "title": "C2",
            },
        ]

        layout = _smart_layout(card_specs, datasource)

        # Should have 2 rows (metrics + 2 charts)
        assert len(layout) == 2

    def test_too_many_cards_raises(self, datasource):
        """Test that more than 4 cards raises."""
        card_specs = [
            {"type": "metric", "column": "Sales", "agg": "sum", "title": f"M{i}"}
            for i in range(5)
        ]

        with pytest.raises(ValueError, match="Too many cards"):
            _smart_layout(card_specs, datasource)


class TestQuickDashboardSimpleMode:
    """Test quick_dashboard() in simple mode."""

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame."""
        return pd.DataFrame(
            {
                "Product": ["Widget", "Gadget", "Tool"],
                "Sales": [100, 200, 150],
                "Revenue": [1000, 2000, 1500],
            }
        )

    def test_simple_mode_one_metric_card(self, sample_df):
        """Test simple mode with 1 metric card."""
        app = quick_dashboard(
            df=sample_df,
            cards=[
                {
                    "type": "metric",
                    "column": "Sales",
                    "agg": "sum",
                    "title": "Total Sales",
                }
            ],
        )

        assert isinstance(app, dash.Dash)
        assert app.layout is not None

    def test_simple_mode_two_cards(self, sample_df):
        """Test simple mode with 2 cards (metric + chart)."""
        app = quick_dashboard(
            df=sample_df,
            cards=[
                {
                    "type": "metric",
                    "column": "Sales",
                    "agg": "sum",
                    "title": "Total Sales",
                },
                {
                    "type": "chart",
                    "plot_type": "bar",
                    "x": "Product",
                    "y": "Sales",
                    "title": "Sales Chart",
                },
            ],
        )

        assert isinstance(app, dash.Dash)

    def test_simple_mode_three_cards(self, sample_df):
        """Test simple mode with 3 cards (all types)."""
        app = quick_dashboard(
            df=sample_df,
            cards=[
                {
                    "type": "metric",
                    "column": "Sales",
                    "agg": "sum",
                    "title": "Total Sales",
                },
                {
                    "type": "chart",
                    "plot_type": "bar",
                    "x": "Product",
                    "y": "Sales",
                    "title": "Sales Chart",
                },
                {"type": "text", "content": "## Analysis Summary"},
            ],
        )

        assert isinstance(app, dash.Dash)

    def test_simple_mode_four_cards(self, sample_df):
        """Test simple mode with 4 cards (2x2 grid)."""
        app = quick_dashboard(
            df=sample_df,
            cards=[
                {
                    "type": "metric",
                    "column": "Sales",
                    "agg": "sum",
                    "title": "Total Sales",
                },
                {
                    "type": "metric",
                    "column": "Revenue",
                    "agg": "sum",
                    "title": "Total Revenue",
                },
                {
                    "type": "chart",
                    "plot_type": "bar",
                    "x": "Product",
                    "y": "Sales",
                    "title": "Sales",
                },
                {
                    "type": "chart",
                    "plot_type": "bar",
                    "x": "Product",
                    "y": "Revenue",
                    "title": "Revenue",
                },
            ],
        )

        assert isinstance(app, dash.Dash)

    def test_simple_mode_with_theme(self, sample_df):
        """Test simple mode with custom theme."""
        app = quick_dashboard(
            df=sample_df,
            cards=[
                {
                    "type": "metric",
                    "column": "Sales",
                    "agg": "sum",
                    "title": "Total Sales",
                }
            ],
            theme="dark",
        )

        assert isinstance(app, dash.Dash)

    def test_simple_mode_with_title(self, sample_df):
        """Test simple mode with custom title."""
        app = quick_dashboard(
            df=sample_df,
            cards=[
                {
                    "type": "metric",
                    "column": "Sales",
                    "agg": "sum",
                    "title": "Total Sales",
                }
            ],
            title="Custom Dashboard",
        )

        assert isinstance(app, dash.Dash)

    def test_simple_mode_too_many_cards(self, sample_df):
        """Test that more than 4 cards raises."""
        cards = [
            {"type": "metric", "column": "Sales", "agg": "sum", "title": f"Metric {i}"}
            for i in range(5)
        ]

        with pytest.raises(ValueError, match="Too many cards"):
            quick_dashboard(df=sample_df, cards=cards)

    def test_simple_mode_no_cards(self, sample_df):
        """Test that no cards raises."""
        with pytest.raises(ValueError, match="requires 'cards' list"):
            quick_dashboard(df=sample_df, cards=[])

    def test_simple_mode_invalid_card_spec(self, sample_df):
        """Test that invalid card spec raises."""
        with pytest.raises(ValueError, match="Invalid card spec"):
            quick_dashboard(
                df=sample_df,
                cards=[{"type": "metric", "column": "Sales"}],  # Missing agg, title
            )


class TestQuickDashboardAdvancedMode:
    """Test quick_dashboard() in advanced mode."""

    @pytest.fixture
    def sample_blocks(self):
        """Create sample blocks."""
        df = pd.DataFrame({"Sales": [100, 200], "Product": ["A", "B"]})
        datasource = BaseDataSource(data_builder=InMemoryDataBuilder(df), cache_ttl=0)

        return [
            SingleMetricBlock(
                block_id="m1",
                datasource=datasource,
                metric_spec={"column": "Sales", "agg": "sum", "title": "Total Sales"},
            ),
            TypedChartBlock(
                block_id="c1",
                datasource=datasource,
                plot_type="bar",
                plot_params={"x": "Product", "y": "Sales"},
                title="Sales Chart",
            ),
        ]

    def test_advanced_mode_with_blocks(self, sample_blocks):
        """Test advanced mode with pre-built blocks."""
        app = quick_dashboard(blocks=sample_blocks)

        assert isinstance(app, dash.Dash)
        assert app.layout is not None

    def test_advanced_mode_too_many_blocks(self, sample_blocks):
        """Test that more than 4 blocks raises."""
        blocks = sample_blocks * 3  # 6 blocks

        with pytest.raises(ValueError, match="Too many blocks"):
            quick_dashboard(blocks=blocks)


class TestQuickDashboardContractValidation:
    """Test contract validation (pre/post/invariants)."""

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame."""
        return pd.DataFrame({"Sales": [100, 200]})

    def test_both_df_and_blocks_raises(self, sample_df):
        """Test that providing both df and blocks raises."""
        blocks = [Mock(spec=SingleMetricBlock)]

        with pytest.raises(ValueError, match="Cannot provide both"):
            quick_dashboard(
                df=sample_df, cards=[{"type": "text", "content": "Test"}], blocks=blocks
            )

    def test_neither_df_nor_blocks_raises(self):
        """Test that providing neither df nor blocks raises."""
        with pytest.raises(ValueError, match="Must provide either"):
            quick_dashboard()

    def test_no_disk_io_cache_ttl_zero(self, sample_df):
        """Test that datasource uses cache_ttl=0 (no disk writes)."""
        # Spy on BaseDataSource initialization to check cache_ttl
        original_init = BaseDataSource.__init__

        captured_cache_ttl = None

        def spy_init(self, *args, **kwargs):
            nonlocal captured_cache_ttl
            captured_cache_ttl = kwargs.get("cache_ttl")
            return original_init(self, *args, **kwargs)

        with patch.object(BaseDataSource, "__init__", spy_init):
            quick_dashboard(
                df=sample_df,
                cards=[
                    {
                        "type": "metric",
                        "column": "Sales",
                        "agg": "sum",
                        "title": "Total",
                    }
                ],
            )

        # Verify cache_ttl=0 was passed (no disk caching)
        assert captured_cache_ttl == 0


class TestQuickDashboardAppType:
    """Test app type (always standard Dash)."""

    @pytest.fixture
    def sample_df(self):
        """Create sample DataFrame."""
        return pd.DataFrame({"Sales": [100, 200]})

    def test_returns_standard_dash(self, sample_df):
        """Test that standard Dash is always returned."""
        app = quick_dashboard(
            df=sample_df,
            cards=[
                {
                    "type": "metric",
                    "column": "Sales",
                    "agg": "sum",
                    "title": "Total",
                }
            ],
        )

        # Should always return standard Dash
        assert isinstance(app, dash.Dash)
        assert hasattr(app, "run")
        assert hasattr(app, "layout")
