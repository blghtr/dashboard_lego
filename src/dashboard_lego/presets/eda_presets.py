"""
Pre-built EDA blocks using TypedChartBlock and plot registry.

v0.15.0: Refactored to use TypedChartBlock instead of deprecated
StaticChartBlock/InteractiveChartBlock.

:hierarchy: [Presets | EDA]
:relates-to:
 - motivated_by: "v0.15.0: Use TypedChartBlock with plot registry"
 - implements: "EDA presets with zero chart_generator code"

:complexity: 4
"""

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc

from dashboard_lego.blocks.typed_chart import Control, TypedChartBlock
from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.utils.plot_registry import register_plot_type

# ============================================================================
# Custom Plot Functions for EDA
# ============================================================================


def plot_correlation_heatmap(df: pd.DataFrame, **kwargs) -> go.Figure:
    """
    Plot correlation matrix heatmap for numerical columns.

    :hierarchy: [Presets | EDA | Plots | CorrelationHeatmap]
    :contract:
     - pre: "DataFrame contains numerical columns"
     - post: "Returns heatmap figure or empty figure"

    Args:
        df: Input DataFrame
        **kwargs: Additional plotly kwargs (title, etc.)

    Returns:
        Plotly Figure with correlation heatmap
    """
    numerical_df = df.select_dtypes(include=["float64", "int64"])

    if numerical_df.empty:
        return go.Figure().add_annotation(
            text="No numerical data for correlation matrix",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )

    corr_matrix = numerical_df.corr()
    fig = px.imshow(
        corr_matrix,
        text_auto=True,
        aspect="auto",
        labels=dict(color="Correlation"),
        **kwargs,
    )
    fig.update_xaxes(side="top")

    return fig


def plot_missing_values(df: pd.DataFrame, **kwargs) -> go.Figure:
    """
    Plot percentage of missing values per column.

    :hierarchy: [Presets | EDA | Plots | MissingValues]
    :contract:
     - pre: "DataFrame provided"
     - post: "Returns bar chart or empty figure"

    Args:
        df: Input DataFrame
        **kwargs: Additional plotly kwargs (title, etc.)

    Returns:
        Plotly Figure with missing values bar chart
    """
    missing_percent = (df.isnull().sum() / len(df)) * 100
    missing_percent = missing_percent[missing_percent > 0].sort_values(ascending=False)

    if missing_percent.empty:
        return go.Figure().add_annotation(
            text="No missing values found",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )

    fig = px.bar(
        missing_percent,
        x=missing_percent.index,
        y=missing_percent.values,
        labels={"x": "Column", "y": "Missing Values (%)"},
        **kwargs,
    )
    fig.update_layout(showlegend=False)

    return fig


def plot_grouped_histogram(df, x, color=None, **kwargs):
    """
    Plot histogram with optional grouping.

    :hierarchy: [Presets | EDA | Plots | GroupedHistogram]
    :contract:
     - pre: "x column exists in df"
     - post: "Returns histogram with optional color grouping"

    Args:
        df: Input DataFrame
        x: Column name for x-axis
        color: Optional column for grouping (None or "None" = no grouping)
        **kwargs: Additional plotly kwargs

    Returns:
        Plotly Figure with histogram
    """
    if df.empty or x not in df.columns:
        return go.Figure().add_annotation(
            text=f"Column '{x}' not found",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )

    # Handle None or "None" string for color
    actual_color = None if (color is None or color == "None") else color

    fig = px.histogram(df, x=x, color=actual_color, **kwargs)
    return fig


def plot_box_by_category(df, x, y, color=None, **kwargs):
    """
    Plot box plot comparing distributions across categories.

    :hierarchy: [Presets | EDA | Plots | BoxPlot]
    :contract:
     - pre: "x and y columns exist in df"
     - post: "Returns box plot figure"

    Args:
        df: Input DataFrame
        x: Categorical column for x-axis
        y: Numerical column for y-axis
        color: Optional column for color grouping
        **kwargs: Additional plotly kwargs

    Returns:
        Plotly Figure with box plot
    """
    if df.empty:
        return go.Figure().add_annotation(
            text="No data available",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )

    if x not in df.columns or y not in df.columns:
        return go.Figure().add_annotation(
            text=f"Required columns not found: {x}, {y}",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )

    fig = px.box(df, x=x, y=y, color=color or x, **kwargs)
    return fig


# Register custom EDA plot types
register_plot_type("correlation_heatmap", plot_correlation_heatmap)
register_plot_type("missing_values", plot_missing_values)
register_plot_type("grouped_histogram", plot_grouped_histogram)
register_plot_type("box_by_category", plot_box_by_category)


# ============================================================================
# EDA Preset Blocks
# ============================================================================


class CorrelationHeatmapPreset(TypedChartBlock):
    """
    Correlation matrix heatmap preset using TypedChartBlock.

    :hierarchy: [Presets | EDA | CorrelationHeatmapPreset]
        :relates-to:
     - motivated_by: "v0.15.0: EDA preset using TypedChartBlock"
          - implements: "preset: 'CorrelationHeatmapPreset'"
     - uses: ["block: 'TypedChartBlock'"]

    :contract:
     - pre: "DataFrame contains numerical columns"
     - post: "Renders correlation heatmap"

    :complexity: 2
    """

    def __init__(
        self,
        block_id: str,
        datasource: BaseDataSource,
        subscribes_to: str,
        title: str = "Correlation Heatmap",
        **kwargs,
    ):
        """
        Initialize correlation heatmap preset.

        Args:
            block_id: Unique identifier
            datasource: Data source instance
            subscribes_to: State ID to subscribe to
            title: Chart title
            **kwargs: Additional styling parameters
        """
        super().__init__(
            block_id=block_id,
            datasource=datasource,
            plot_type="correlation_heatmap",
            plot_params={},  # No params needed
            plot_kwargs={"title": "Correlation Matrix"},
            title=title,
            subscribes_to=subscribes_to,
            **kwargs,
        )


class MissingValuesPreset(TypedChartBlock):
    """
    Missing values analysis preset using TypedChartBlock.

    :hierarchy: [Presets | EDA | MissingValuesPreset]
    :relates-to:
     - motivated_by: "v0.15.0: EDA preset using TypedChartBlock"
     - implements: "preset: 'MissingValuesPreset'"
     - uses: ["block: 'TypedChartBlock'"]

    :contract:
     - pre: "DataFrame provided"
     - post: "Renders missing values bar chart"

    :complexity: 2
    """

    def __init__(
        self,
        block_id: str,
        datasource: BaseDataSource,
        subscribes_to: str,
        title: str = "Missing Values Analysis",
        **kwargs,
    ):
        """
        Initialize missing values preset.

        Args:
            block_id: Unique identifier
            datasource: Data source instance
            subscribes_to: State ID to subscribe to
            title: Chart title
            **kwargs: Additional styling parameters
        """
        super().__init__(
            block_id=block_id,
            datasource=datasource,
            plot_type="missing_values",
            plot_params={},  # No params needed
            plot_kwargs={"title": "Percentage of Missing Values per Column"},
            title=title,
            subscribes_to=subscribes_to,
            **kwargs,
        )


class GroupedHistogramPreset(TypedChartBlock):
    """
    Interactive histogram with grouping using TypedChartBlock.

    :hierarchy: [Presets | EDA | GroupedHistogramPreset]
        :relates-to:
     - motivated_by: "v0.15.0: Interactive histogram with controls"
          - implements: "preset: 'GroupedHistogramPreset'"
     - uses: ["block: 'TypedChartBlock'"]

    :contract:
     - pre: "DataFrame contains numerical and categorical columns"
     - post: "Renders histogram with column/group controls"

    :complexity: 3
    """

    def __init__(
        self,
        block_id: str,
        datasource: BaseDataSource,
        subscribes_to=None,
        title: str = "Distribution Analysis",
        **kwargs,
    ):
        """
        Initialize grouped histogram preset.

        Args:
            block_id: Unique identifier
            datasource: Data source instance
            subscribes_to: State ID(s) to subscribe to
            title: Chart title
            **kwargs: Additional styling parameters
        """
        # Get columns from datasource
        df = datasource.get_processed_data()
        numerical_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
        categorical_cols = ["None"] + df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        # Create controls
        controls = {
            "x_col": Control(
                component=dcc.Dropdown,
                props={
                    "options": numerical_cols,
                    "value": numerical_cols[0] if numerical_cols else None,
                    "clearable": False,
                    "style": {"minWidth": "150px"},
                },
            ),
            "group_by": Control(
                component=dcc.Dropdown,
                props={
                    "options": categorical_cols,
                    "value": "None",
                    "clearable": False,
                    "style": {"minWidth": "150px"},
                },
            ),
        }

        super().__init__(
            block_id=block_id,
            datasource=datasource,
            plot_type="grouped_histogram",
            plot_params={"x": "{{x_col}}", "color": "{{group_by}}"},
            plot_kwargs={"barmode": "overlay", "opacity": 0.75},
            title=title,
            controls=controls,
            subscribes_to=subscribes_to,
            **kwargs,
        )


class BoxPlotPreset(TypedChartBlock):
    """
    Interactive box plot preset using TypedChartBlock.

    :hierarchy: [Presets | EDA | BoxPlotPreset]
        :relates-to:
     - motivated_by: "v0.15.0: Box plot with controls"
     - implements: "preset: 'BoxPlotPreset'"
     - uses: ["block: 'TypedChartBlock'"]

        :contract:
     - pre: "DataFrame has numerical and categorical columns"
     - post: "Renders box plot with column selection"

    :complexity: 3
    """

    def __init__(
        self,
        block_id: str,
        datasource: BaseDataSource,
        subscribes_to=None,
        title: str = "Distribution Comparison (Box Plot)",
        **kwargs,
    ):
        """
        Initialize box plot preset.

        Args:
            block_id: Unique identifier
            datasource: Data source instance
            subscribes_to: State ID(s) to subscribe to
            title: Chart title
            **kwargs: Additional styling parameters
        """
        # Get columns from datasource
        df = datasource.get_processed_data()
        numerical_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
        categorical_cols = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        if not numerical_cols:
            raise ValueError("BoxPlotPreset requires at least one numerical column")
        if not categorical_cols:
            raise ValueError("BoxPlotPreset requires at least one categorical column")

        # Create controls
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
            plot_type="box_by_category",
            plot_params={"x": "{{x_col}}", "y": "{{y_col}}", "color": "{{x_col}}"},
            plot_kwargs={},
            title=title,
            controls=controls,
            subscribes_to=subscribes_to,
            **kwargs,
        )
