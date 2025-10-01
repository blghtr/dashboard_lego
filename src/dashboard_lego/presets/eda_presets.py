"""
This module contains pre-built blocks for common Exploratory Data Analysis (EDA) tasks.

"""

from typing import Any, Dict, Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc

from dashboard_lego.blocks.chart import Control, InteractiveChartBlock, StaticChartBlock
from dashboard_lego.core.datasource import BaseDataSource


class CorrelationHeatmapPreset(StaticChartBlock):
    """
    A preset block that displays a correlation matrix heatmap for the numerical columns of a DataFrame.

        :hierarchy: [Presets | EDA | CorrelationHeatmap]
        :relates-to:
          - motivated_by: "Architectural Conclusion: Provide pre-built EDA components
            for common data analysis patterns to reduce boilerplate"
          - implements: "preset: 'CorrelationHeatmapPreset'"
          - uses: ["block: 'StaticChartBlock'"]

    """

    def __init__(
        self,
        block_id: str,
        datasource: BaseDataSource,
        subscribes_to: str,
        title: str = "Correlation Heatmap",
        # Style customization parameters (inherited from StaticChartBlock)
        card_style: Optional[Dict[str, Any]] = None,
        card_className: Optional[str] = None,
        title_style: Optional[Dict[str, Any]] = None,
        title_className: Optional[str] = None,
        loading_type: str = "default",
        graph_config: Optional[Dict[str, Any]] = None,
        graph_style: Optional[Dict[str, Any]] = None,
        figure_layout: Optional[Dict[str, Any]] = None,
    ):
        """
        Initializes the CorrelationHeatmapPreset with customizable styling.

        Args:
            block_id: A unique identifier for this block instance.
            datasource: An instance of a class that implements the BaseDataSource interface.
            subscribes_to: The state ID to which this block subscribes to receive updates.
            title: The title to be displayed on the chart card.
            card_style: Optional style dictionary for the card component.
            card_className: Optional CSS class name for the card component.
            title_style: Optional style dictionary for the title component.
            title_className: Optional CSS class name for the title component.
            loading_type: Type of loading indicator to display.
            graph_config: Optional configuration for the Plotly graph.
            graph_style: Optional style dictionary for the graph component.
            figure_layout: Optional layout overrides for the Plotly figure.

        """
        super().__init__(
            block_id=block_id,
            datasource=datasource,
            title=title,
            chart_generator=self._create_heatmap,
            subscribes_to=subscribes_to,
            # Pass through customization parameters
            card_style=card_style,
            card_className=card_className,
            title_style=title_style,
            title_className=title_className,
            loading_type=loading_type,
            graph_config=graph_config,
            graph_style=graph_style,
            figure_layout=figure_layout,
        )

    def _create_heatmap(self, df: pd.DataFrame, ctx) -> go.Figure:
        """
        Calculates the correlation matrix and generates a heatmap figure.

        Args:
            df: The input DataFrame from the datasource.

        Returns:
            A Plotly Figure object representing the heatmap.

        """
        # Select only numerical columns for correlation matrix
        numerical_df = df.select_dtypes(include=["float64", "int64"])

        if numerical_df.empty:
            return go.Figure().update_layout(
                title="No numerical data to create a correlation matrix."
            )

        corr_matrix = numerical_df.corr()
        fig = px.imshow(
            corr_matrix,
            text_auto=True,
            aspect="auto",
            labels=dict(color="Correlation"),
            title="Correlation Matrix",
        )
        fig.update_xaxes(side="top")
        return fig


class GroupedHistogramPreset(InteractiveChartBlock):
    """
    A preset block that displays an interactive histogram.

    Provides controls to select the numerical column for the histogram and an
    optional categorical column for grouping.

        :hierarchy: [Presets | EDA | GroupedHistogram]
        :relates-to:
          - motivated_by: "Architectural Conclusion: Provide pre-built EDA components
            for common data analysis patterns to reduce boilerplate"
          - implements: "preset: 'GroupedHistogramPreset'"
          - uses: ["block: 'InteractiveChartBlock'"]

    """

    def __init__(
        self,
        block_id: str,
        datasource: BaseDataSource,
        title: str = "Distribution Analysis",
        # Style customization parameters (inherited from InteractiveChartBlock)
        card_style: Optional[Dict[str, Any]] = None,
        card_className: Optional[str] = None,
        title_style: Optional[Dict[str, Any]] = None,
        title_className: Optional[str] = None,
        loading_type: str = "default",
        graph_config: Optional[Dict[str, Any]] = None,
        graph_style: Optional[Dict[str, Any]] = None,
        figure_layout: Optional[Dict[str, Any]] = None,
        controls_row_style: Optional[Dict[str, Any]] = None,
        controls_row_className: Optional[str] = None,
    ):
        # Inspect the dataframe to find numerical and categorical columns
        df = datasource.get_processed_data()
        numerical_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
        categorical_cols = ["None"] + df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        if not numerical_cols:
            raise ValueError(
                "GroupedHistogramPreset requires a datasource with at least one numerical column."
            )

        controls = {
            "x_col": Control(
                component=dcc.Dropdown,
                props={
                    "options": numerical_cols,
                    "value": numerical_cols[0],
                    "clearable": False,
                    "style": {"minWidth": "150px"},
                },
            ),
            "group_by": Control(
                component=dcc.Dropdown,
                props={
                    "options": categorical_cols,
                    "value": categorical_cols[0],
                    "clearable": False,
                    "style": {"minWidth": "150px"},
                },
            ),
        }

        super().__init__(
            block_id=block_id,
            datasource=datasource,
            title=title,
            chart_generator=self._create_histogram,
            controls=controls,
            # Pass through customization parameters
            card_style=card_style,
            card_className=card_className,
            title_style=title_style,
            title_className=title_className,
            loading_type=loading_type,
            graph_config=graph_config,
            graph_style=graph_style,
            figure_layout=figure_layout,
            controls_row_style=controls_row_style,
            controls_row_className=controls_row_className,
        )

    def _create_histogram(self, df: pd.DataFrame, ctx) -> go.Figure:
        """
        Generates a histogram based on the selected control values.

        """
        x_col = ctx.controls.get("x_col")
        group_by = ctx.controls.get("group_by")

        if not x_col:
            return go.Figure().update_layout(title="Please select a column to display.")

        fig = px.histogram(
            df,
            x=x_col,
            color=None if group_by == "None" else group_by,
            title=f"Distribution of {x_col}"
            + (f" grouped by {group_by}" if group_by != "None" else ""),
            barmode="overlay",
        )
        fig.update_traces(opacity=0.75)
        return fig


class MissingValuesPreset(StaticChartBlock):
    """
    A preset block that displays the percentage of missing values for each column in a bar chart.

        :hierarchy: [Presets | EDA | MissingValues]
        :relates-to:
          - motivated_by: "Architectural Conclusion: Missing value analysis is a
            fundamental EDA requirement for data quality assessment"
          - implements: "preset: 'MissingValuesPreset'"
          - uses: ["block: 'StaticChartBlock'"]

        :rationale: "Chosen as a high-value, simple-to-implement preset for initial data quality assessment."
        :contract:
          - pre: "A DataFrame is available from the data source."
          - post: "A bar chart is rendered showing the percentage of missing values per column."

    """

    def __init__(
        self,
        block_id: str,
        datasource: BaseDataSource,
        subscribes_to: str,
        title: str = "Missing Values Analysis",
        # Style customization parameters (inherited from StaticChartBlock)
        card_style: Optional[Dict[str, Any]] = None,
        card_className: Optional[str] = None,
        title_style: Optional[Dict[str, Any]] = None,
        title_className: Optional[str] = None,
        loading_type: str = "default",
        graph_config: Optional[Dict[str, Any]] = None,
        graph_style: Optional[Dict[str, Any]] = None,
        figure_layout: Optional[Dict[str, Any]] = None,
    ):
        """
        Initializes the MissingValuesPreset with customizable styling.

        Args:
            block_id: A unique identifier for this block instance.
            datasource: An instance of a class that implements the BaseDataSource interface.
            subscribes_to: The state ID to which this block subscribes to receive updates.
            title: The title to be displayed on the chart card.
            card_style: Optional style dictionary for the card component.
            card_className: Optional CSS class name for the card component.
            title_style: Optional style dictionary for the title component.
            title_className: Optional CSS class name for the title component.
            loading_type: Type of loading indicator to display.
            graph_config: Optional configuration for the Plotly graph.
            graph_style: Optional style dictionary for the graph component.
            figure_layout: Optional layout overrides for the Plotly figure.

        """
        super().__init__(
            block_id=block_id,
            datasource=datasource,
            title=title,
            chart_generator=self._create_missing_values_chart,
            subscribes_to=subscribes_to,
            # Pass through customization parameters
            card_style=card_style,
            card_className=card_className,
            title_style=title_style,
            title_className=title_className,
            loading_type=loading_type,
            graph_config=graph_config,
            graph_style=graph_style,
            figure_layout=figure_layout,
        )

    def _create_missing_values_chart(self, df: pd.DataFrame, ctx) -> go.Figure:
        """
        Calculates missing values and generates a bar chart.

        Args:
            df: The input DataFrame from the datasource.

        Returns:
            A Plotly Figure object representing the bar chart.

        """
        missing_percent = (df.isnull().sum() / len(df)) * 100
        missing_percent = missing_percent[missing_percent > 0].sort_values(
            ascending=False
        )

        if missing_percent.empty:
            return go.Figure().update_layout(
                title="No missing values found in the dataset."
            )

        fig = px.bar(
            missing_percent,
            x=missing_percent.index,
            y=missing_percent.values,
            labels={"x": "Column", "y": "Missing Values (%)"},
            title="Percentage of Missing Values per Column",
        )
        fig.update_layout(showlegend=False)
        return fig


class BoxPlotPreset(InteractiveChartBlock):
    """
    A preset block that displays an interactive box plot.

    Provides controls to select a numerical column and a categorical column
    to compare distributions.

        :hierarchy: [Presets | EDA | BoxPlot]
        :relates-to:
          - motivated_by: "Architectural Conclusion: Box plots are essential for
            understanding data distribution and identifying outliers"
          - implements: "preset: 'BoxPlotPreset'"
          - uses: ["block: 'InteractiveChartBlock'"]

        :rationale: "Chosen as a standard and effective way to compare distributions across categories."
        :contract:
          - pre: "User selects a numerical and a categorical column."
          - post: "A box plot is rendered showing the distribution of the numerical column grouped by the categorical column."

    """

    def __init__(
        self,
        block_id: str,
        datasource: BaseDataSource,
        title: str = "Distribution Comparison (Box Plot)",
        # Style customization parameters (inherited from InteractiveChartBlock)
        card_style: Optional[Dict[str, Any]] = None,
        card_className: Optional[str] = None,
        title_style: Optional[Dict[str, Any]] = None,
        title_className: Optional[str] = None,
        loading_type: str = "default",
        graph_config: Optional[Dict[str, Any]] = None,
        graph_style: Optional[Dict[str, Any]] = None,
        figure_layout: Optional[Dict[str, Any]] = None,
        controls_row_style: Optional[Dict[str, Any]] = None,
        controls_row_className: Optional[str] = None,
    ):
        df = datasource.get_processed_data()
        numerical_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
        categorical_cols = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        if not numerical_cols:
            raise ValueError(
                "BoxPlotPreset requires a datasource with at least one numerical column."
            )
        if not categorical_cols:
            raise ValueError(
                "BoxPlotPreset requires a datasource with at least one categorical column."
            )

        controls = {
            "y_col": Control(
                component=dcc.Dropdown,
                props={
                    "options": numerical_cols,
                    "value": numerical_cols[0],
                    "clearable": False,
                    "style": {"minWidth": "150px"},
                },
            ),
            "x_col": Control(
                component=dcc.Dropdown,
                props={
                    "options": categorical_cols,
                    "value": categorical_cols[0],
                    "clearable": False,
                    "style": {"minWidth": "150px"},
                },
            ),
        }

        super().__init__(
            block_id=block_id,
            datasource=datasource,
            title=title,
            chart_generator=self._create_box_plot,
            controls=controls,
            # Pass through customization parameters
            card_style=card_style,
            card_className=card_className,
            title_style=title_style,
            title_className=title_className,
            loading_type=loading_type,
            graph_config=graph_config,
            graph_style=graph_style,
            figure_layout=figure_layout,
            controls_row_style=controls_row_style,
            controls_row_className=controls_row_className,
        )

    def _create_box_plot(self, df: pd.DataFrame, ctx) -> go.Figure:
        """
        Generates a box plot based on the selected control values.

        """
        y_col = ctx.controls.get("y_col")
        x_col = ctx.controls.get("x_col")

        if not y_col or not x_col:
            return go.Figure().update_layout(title="Please select columns to display.")

        fig = px.box(
            df,
            x=x_col,
            y=y_col,
            title=f"Distribution of {y_col} by {x_col}",
            color=x_col,
        )
        return fig
