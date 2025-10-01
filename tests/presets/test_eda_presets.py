"""
Tests for the EDA (Exploratory Data Analysis) presets.

:hierarchy: [Testing | Unit Tests | Presets | EDA]
:relates-to:
 - motivated_by: "Architectural Conclusion: EDA presets require thorough testing
   to ensure accurate data visualization and analysis capabilities"
 - implements: "test_suite: 'EDAPresets'"

:strategy: "Use a factory fixture to create mock datasources with specific dataframes for each test case. This allows for isolated testing of each preset's data handling and figure generation logic."
:contract:
 - pre: "Test environment is set up with pytest, pandas, and plotly."
 - post: "All tests for EDA presets pass, and code coverage for the module is 100%."

"""

import os
import sys
from unittest.mock import MagicMock

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import pytest

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dashboard_lego.core.chart_context import ChartContext
from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.presets.eda_presets import (
    BoxPlotPreset,
    CorrelationHeatmapPreset,
    GroupedHistogramPreset,
    MissingValuesPreset,
)


@pytest.fixture
def datasource_factory():
    """
    Factory fixture to create a mock datasource with a given DataFrame.

    :hierarchy: [Testing | Fixtures | datasource_factory]
    :scenario: "Returns a function that can be called with a DataFrame to create a mock datasource."
    :returns: A factory function.
    """

    def _factory(df: pd.DataFrame):
        mock_ds = MagicMock(spec=BaseDataSource)
        mock_ds.get_processed_data.return_value = df
        # Mock the init_data method to reflect the data loading
        mock_ds.init_data.return_value = True
        # When _load_data is called, it will use the provided df
        mock_ds._load_data.return_value = df
        return mock_ds

    return _factory


def create_chart_context(datasource, controls=None):
    """Helper function to create ChartContext for tests."""
    if controls is None:
        controls = {}
    mock_logger = MagicMock()
    return ChartContext(datasource=datasource, controls=controls, logger=mock_logger)


class TestCorrelationHeatmapPreset:
    """
    Tests for the CorrelationHeatmapPreset.
    """

    def test_initialization(self, datasource_factory):
        """
        Tests that the CorrelationHeatmapPreset initializes correctly.
        """
        df = pd.DataFrame({"a": [1], "b": [2]})
        mock_ds = datasource_factory(df)
        preset = CorrelationHeatmapPreset(
            block_id="test_corr", datasource=mock_ds, subscribes_to="filters"
        )
        assert preset.title == "Correlation Heatmap"
        assert preset.block_id == "test_corr"

    def test_generates_figure(self, datasource_factory):
        """
        Tests that a heatmap figure is generated with valid data.
        """
        df = pd.DataFrame(
            {
                "numeric_1": [1, 2, 3, 4],
                "numeric_2": [4, 3, 2, 1],
                "categorical": ["a", "b", "a", "b"],
            }
        )
        mock_ds = datasource_factory(df)
        preset = CorrelationHeatmapPreset(
            block_id="test_corr", datasource=mock_ds, subscribes_to="filters"
        )

        ctx = create_chart_context(mock_ds)
        fig = preset._create_heatmap(df, ctx)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert isinstance(fig.data[0], go.Heatmap)
        assert fig.layout.title.text == "Correlation Matrix"

    def test_no_numerical_data(self, datasource_factory):
        """
        Tests behavior when the DataFrame has no numerical data.
        """
        df = pd.DataFrame({"categorical": ["a", "b", "c"]})
        mock_ds = datasource_factory(df)
        preset = CorrelationHeatmapPreset(
            block_id="test_corr", datasource=mock_ds, subscribes_to="filters"
        )

        ctx = create_chart_context(mock_ds)
        fig = preset._create_heatmap(df, ctx)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 0
        assert "No numerical data" in fig.layout.title.text


class TestGroupedHistogramPreset:
    """
    Tests for the GroupedHistogramPreset.
    """

    def test_initialization_raises_error_on_no_numerical_data(self, datasource_factory):
        """
        Tests that initialization raises a ValueError if the datasource has no numerical columns.
        """
        df = pd.DataFrame({"categorical": ["a", "b", "c"]})
        mock_ds = datasource_factory(df)
        with pytest.raises(
            ValueError, match="requires a datasource with at least one numerical column"
        ):
            GroupedHistogramPreset(block_id="test_hist", datasource=mock_ds)

    def test_initialization(self, datasource_factory):
        """
        Tests successful initialization.
        """
        df = pd.DataFrame({"numeric": [1, 2], "categorical": ["a", "b"]})
        mock_ds = datasource_factory(df)
        preset = GroupedHistogramPreset(block_id="test_hist", datasource=mock_ds)
        assert preset.title == "Distribution Analysis"
        assert "x_col" in preset.controls
        assert "group_by" in preset.controls

    def test_generates_figure(self, datasource_factory):
        """
        Tests that a histogram figure is generated.
        """
        df = pd.DataFrame(
            {"numeric": [1, 2, 2, 3], "categorical": ["a", "b", "a", "b"]}
        )
        mock_ds = datasource_factory(df)
        preset = GroupedHistogramPreset(block_id="test_hist", datasource=mock_ds)

        ctx = create_chart_context(mock_ds, {"x_col": "numeric", "group_by": "None"})
        fig = preset._create_histogram(df, ctx)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert isinstance(fig.data[0], go.Histogram)
        assert "Distribution of numeric" in fig.layout.title.text

    def test_generates_figure_with_grouping(self, datasource_factory):
        """
        Tests that a grouped histogram is generated correctly.
        """
        df = pd.DataFrame(
            {"numeric": [1, 2, 2, 3], "categorical": ["a", "b", "a", "b"]}
        )
        mock_ds = datasource_factory(df)
        preset = GroupedHistogramPreset(block_id="test_hist", datasource=mock_ds)

        ctx = create_chart_context(
            mock_ds, {"x_col": "numeric", "group_by": "categorical"}
        )
        fig = preset._create_histogram(df, ctx)

        assert isinstance(fig, go.Figure)
        # Plotly creates a trace for each category
        assert len(fig.data) == 2
        assert isinstance(fig.data[0], go.Histogram)
        assert "grouped by categorical" in fig.layout.title.text

    def test_no_x_col_provided(self, datasource_factory):
        """
        Tests behavior when x_col is not provided to the chart generator.
        """
        df = pd.DataFrame({"numeric": [1, 2, 3]})
        mock_ds = datasource_factory(df)
        preset = GroupedHistogramPreset(block_id="test_hist", datasource=mock_ds)

        ctx = create_chart_context(mock_ds, {"x_col": None, "group_by": "None"})
        fig = preset._create_histogram(df, ctx)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 0
        assert "Please select a column" in fig.layout.title.text


class TestMissingValuesPreset:
    """
    Tests for the MissingValuesPreset.
    """

    def test_initialization(self, datasource_factory):
        """
        Tests that the MissingValuesPreset initializes correctly.
        """
        df = pd.DataFrame({"a": [1]})
        mock_ds = datasource_factory(df)
        preset = MissingValuesPreset(
            block_id="test_missing", datasource=mock_ds, subscribes_to="filters"
        )
        assert preset.title == "Missing Values Analysis"

    def test_generates_figure_with_missing_values(self, datasource_factory):
        """
        Tests that a bar chart is generated showing missing value percentages.
        """
        df = pd.DataFrame(
            {
                "a": [1, 2, np.nan, 4],
                "b": [np.nan, np.nan, np.nan, np.nan],
                "c": [1, 2, 3, 4],
            }
        )
        mock_ds = datasource_factory(df)
        preset = MissingValuesPreset(
            block_id="test_missing", datasource=mock_ds, subscribes_to="filters"
        )

        ctx = create_chart_context(mock_ds)
        fig = preset._create_missing_values_chart(df, ctx)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1
        assert isinstance(fig.data[0], go.Bar)

        # Check the data in the bar chart
        chart_data = fig.data[0]
        assert list(chart_data.x) == ["b", "a"]  # Sorted descending
        assert list(chart_data.y) == [100.0, 25.0]

    def test_no_missing_values(self, datasource_factory):
        """
        Tests behavior when the DataFrame has no missing values.
        """
        df = pd.DataFrame({"a": [1, 2, 3], "b": [4, 5, 6]})
        mock_ds = datasource_factory(df)
        preset = MissingValuesPreset(
            block_id="test_missing", datasource=mock_ds, subscribes_to="filters"
        )

        ctx = create_chart_context(mock_ds)
        fig = preset._create_missing_values_chart(df, ctx)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 0
        assert "No missing values found" in fig.layout.title.text


class TestBoxPlotPreset:
    """
    Tests for the BoxPlotPreset.
    """

    def test_initialization_raises_error(self, datasource_factory):
        """
        Tests that initialization raises ValueError if required column types are missing.
        """
        # No numerical
        df_no_numeric = pd.DataFrame({"cat": ["a", "b"]})
        mock_ds_no_numeric = datasource_factory(df_no_numeric)
        with pytest.raises(
            ValueError, match="requires a datasource with at least one numerical column"
        ):
            BoxPlotPreset(block_id="test_box", datasource=mock_ds_no_numeric)

        # No categorical
        df_no_cat = pd.DataFrame({"num": [1, 2]})
        mock_ds_no_cat = datasource_factory(df_no_cat)
        with pytest.raises(
            ValueError,
            match="requires a datasource with at least one categorical column",
        ):
            BoxPlotPreset(block_id="test_box", datasource=mock_ds_no_cat)

    def test_generates_figure(self, datasource_factory):
        """
        Tests that a box plot figure is generated.
        """
        df = pd.DataFrame(
            {"numeric": [1, 2, 10, 11], "categorical": ["a", "a", "b", "b"]}
        )
        mock_ds = datasource_factory(df)
        preset = BoxPlotPreset(block_id="test_box", datasource=mock_ds)

        ctx = create_chart_context(
            mock_ds, {"y_col": "numeric", "x_col": "categorical"}
        )
        fig = preset._create_box_plot(df, ctx)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) > 0  # Plotly might create one or more traces
        assert isinstance(fig.data[0], go.Box)
        assert "Distribution of numeric by categorical" in fig.layout.title.text

    def test_no_columns_provided(self, datasource_factory):
        """
        Tests behavior when columns are not provided to the chart generator.
        """
        df = pd.DataFrame({"numeric": [1], "categorical": ["a"]})
        mock_ds = datasource_factory(df)
        preset = BoxPlotPreset(block_id="test_box", datasource=mock_ds)

        ctx = create_chart_context(mock_ds, {"y_col": None, "x_col": None})
        fig = preset._create_box_plot(df, ctx)

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 0
        assert "Please select columns to display" in fig.layout.title.text
