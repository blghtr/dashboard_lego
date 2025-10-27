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

from typing import Any, Dict, Optional

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc

from dashboard_lego.blocks.typed_chart import Control
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.presets.base_preset import BasePreset
from dashboard_lego.utils.plot_registry import register_plot_type

#  TODO: Refactor this from scratch
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


class CorrelationHeatmapPreset(BasePreset):
    """
    Correlation matrix heatmap preset using BasePreset.

    :hierarchy: [Presets | EDA | CorrelationHeatmapPreset]
    :relates-to:
     - motivated_by: "v0.15.0: EDA preset using BasePreset"
     - implements: "preset: 'CorrelationHeatmapPreset'"
     - uses: ["class: 'BasePreset'"]

    :contract:
     - pre: "DataFrame contains numerical columns"
     - post: "Renders correlation heatmap"

    :complexity: 2
    """

    def __init__(
        self,
        block_id: str,
        datasource: DataSource,
        subscribes_to: str,
        title: str = "Correlation Heatmap",
        controls: bool = False,
        **kwargs,
    ):
        """
        Initialize correlation heatmap preset.

        Args:
            block_id: Unique identifier
            datasource: Data source instance
            subscribes_to: State ID to subscribe to
            title: Chart title
            controls: Control configuration (False=no controls, True=default controls)
            **kwargs: Additional styling parameters
        """
        super().__init__(
            block_id=block_id,
            datasource=datasource,
            subscribes_to=subscribes_to,
            title=title,
            controls=controls,
            **kwargs,
        )

    @property
    def default_controls(self) -> Dict[str, Control]:
        """
        Default control definitions for correlation heatmap preset.

        Returns:
            Empty dict - no controls needed for correlation heatmap
        """
        return {}

    def _get_plot_type(self) -> str:
        """Plot type identifier for correlation heatmap."""
        return "correlation_heatmap"

    def _validate_datasource(self, datasource: DataSource) -> None:
        """
        Validate datasource requirements for correlation heatmap.

        Args:
            datasource: DataSource instance to validate

        Raises:
            ValueError: If datasource doesn't have numerical columns
        """
        df = datasource.get_processed_data()
        numerical_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()

        if len(numerical_cols) < 2:
            raise ValueError(
                "CorrelationHeatmapPreset requires at least two numerical columns"
            )

    def _build_plot_params(
        self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build plot_params for correlation heatmap.

        Args:
            final_controls: Final control configuration
            kwargs: Additional parameters and fallback values

        Returns:
            Empty dict - no plot parameters needed
        """
        return {}

    def _build_plot_kwargs(
        self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build plot_kwargs for correlation heatmap.

        Args:
            final_controls: Final control configuration
            kwargs: Additional parameters and fallback values

        Returns:
            Dictionary of plot kwargs
        """
        return {"title": kwargs.get("title", "Correlation Matrix")}

    def _get_plot_title(self, final_controls: Dict[str, Control]) -> Optional[str]:
        """
        Get dynamic plot title for correlation heatmap.

        Args:
            final_controls: Final control configuration

        Returns:
            None - no dynamic title needed
        """
        return None


class MissingValuesPreset(BasePreset):
    """
    Missing values analysis preset using BasePreset.

    :hierarchy: [Presets | EDA | MissingValuesPreset]
    :relates-to:
     - motivated_by: "v0.15.0: EDA preset using BasePreset"
     - implements: "preset: 'MissingValuesPreset'"
     - uses: ["class: 'BasePreset'"]

    :contract:
     - pre: "DataFrame provided"
     - post: "Renders missing values bar chart"

    :complexity: 2
    """

    def __init__(
        self,
        block_id: str,
        datasource: DataSource,
        subscribes_to: str,
        title: str = "Missing Values Analysis",
        controls: bool = False,
        **kwargs,
    ):
        """
        Initialize missing values preset.

        Args:
            block_id: Unique identifier
            datasource: Data source instance
            subscribes_to: State ID to subscribe to
            title: Chart title
            controls: Control configuration (False=no controls, True=default controls)
            **kwargs: Additional styling parameters
        """
        super().__init__(
            block_id=block_id,
            datasource=datasource,
            subscribes_to=subscribes_to,
            title=title,
            controls=controls,
            **kwargs,
        )

    @property
    def default_controls(self) -> Dict[str, Control]:
        """
        Default control definitions for missing values preset.

        Returns:
            Empty dict - no controls needed for missing values analysis
        """
        return {}

    def _get_plot_type(self) -> str:
        """Plot type identifier for missing values analysis."""
        return "missing_values"

    def _validate_datasource(self, datasource: DataSource) -> None:
        """
        Validate datasource requirements for missing values analysis.

        Args:
            datasource: DataSource instance to validate

        Raises:
            ValueError: If datasource is empty
        """
        df = datasource.get_processed_data()
        if df.empty:
            raise ValueError("MissingValuesPreset requires non-empty DataFrame")

    def _build_plot_params(
        self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build plot_params for missing values analysis.

        Args:
            final_controls: Final control configuration
            kwargs: Additional parameters and fallback values

        Returns:
            Empty dict - no plot parameters needed
        """
        return {}

    def _build_plot_kwargs(
        self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build plot_kwargs for missing values analysis.

        Args:
            final_controls: Final control configuration
            kwargs: Additional parameters and fallback values

        Returns:
            Dictionary of plot kwargs
        """
        return {"title": kwargs.get("title", "Percentage of Missing Values per Column")}

    def _get_plot_title(self, final_controls: Dict[str, Control]) -> Optional[str]:
        """
        Get dynamic plot title for missing values analysis.

        Args:
            final_controls: Final control configuration

        Returns:
            None - no dynamic title needed
        """
        return None


class GroupedHistogramPreset(BasePreset):
    """
    Interactive histogram with grouping using BasePreset.

    :hierarchy: [Presets | EDA | GroupedHistogramPreset]
    :relates-to:
     - motivated_by: "v0.15.0: Interactive histogram with controls using BasePreset"
     - implements: "preset: 'GroupedHistogramPreset'"
     - uses: ["class: 'BasePreset'"]

    :contract:
     - pre: "DataFrame contains numerical and categorical columns"
     - post: "Renders histogram with column/group controls"

    :complexity: 3
    """

    def __init__(
        self,
        block_id: str,
        datasource: DataSource,
        subscribes_to=None,
        title: str = "Distribution Analysis",
        controls: bool = True,
        **kwargs,
    ):
        """
        Initialize grouped histogram preset.

        Args:
            block_id: Unique identifier
            datasource: Data source instance
            subscribes_to: State ID(s) to subscribe to
            title: Chart title
            controls: Control configuration (False=no controls, True=default controls)
            **kwargs: Additional styling parameters and control values
        """
        # Store datasource for use in properties
        self._datasource = datasource
        self._block_id = block_id

        super().__init__(
            block_id=block_id,
            datasource=datasource,
            subscribes_to=subscribes_to,
            title=title,
            controls=controls,
            **kwargs,
        )

    @property
    def default_controls(self) -> Dict[str, Control]:
        """
        Default control definitions for grouped histogram preset.

        Returns:
            Dictionary mapping control names to Control objects
        """
        # Get columns from datasource for control options
        df = self._datasource.get_processed_data()
        numerical_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
        categorical_cols = ["None"] + df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        return {
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

    def _get_plot_type(self) -> str:
        """Plot type identifier for grouped histogram."""
        return "grouped_histogram"

    def _validate_datasource(self, datasource: DataSource) -> None:
        """
        Validate datasource requirements for grouped histogram.

        Args:
            datasource: DataSource instance to validate

        Raises:
            ValueError: If datasource doesn't have numerical columns
        """
        df = datasource.get_processed_data()
        numerical_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()

        if len(numerical_cols) < 1:
            raise ValueError(
                "GroupedHistogramPreset requires at least one numerical column"
            )

    def _build_plot_params(
        self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build plot_params for grouped histogram.

        Args:
            final_controls: Final control configuration
            kwargs: Additional parameters and fallback values

        Returns:
            Dictionary of plot parameters
        """
        # Get default values from datasource
        df = self._datasource.get_processed_data()
        numerical_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()

        plot_params = {}

        if "x_col" in final_controls:
            plot_params["x"] = "{{x_col}}"
        else:
            plot_params["x"] = kwargs.get("x_col", numerical_cols[0])

        if "group_by" in final_controls:
            plot_params["color"] = "{{group_by}}"
        else:
            plot_params["color"] = kwargs.get("group_by", "None")

        return plot_params

    def _build_plot_kwargs(
        self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build plot_kwargs for grouped histogram.

        Args:
            final_controls: Final control configuration
            kwargs: Additional parameters and fallback values

        Returns:
            Dictionary of plot kwargs
        """
        return {"barmode": "overlay", "opacity": 0.75, "title": kwargs.get("title")}

    def _get_plot_title(self, final_controls: Dict[str, Control]) -> Optional[str]:
        """
        Get dynamic plot title for grouped histogram.

        Args:
            final_controls: Final control configuration

        Returns:
            Dynamic title string with placeholders or None
        """
        if "x_col" in final_controls:
            return "Distribution: {{x_col}}"
        return None


class BoxPlotPreset(BasePreset):
    """
    Interactive box plot preset using BasePreset.

    :hierarchy: [Presets | EDA | BoxPlotPreset]
    :relates-to:
     - motivated_by: "v0.15.0: Box plot with controls using BasePreset"
     - implements: "preset: 'BoxPlotPreset'"
     - uses: ["class: 'BasePreset'"]

    :contract:
     - pre: "DataFrame has numerical and categorical columns"
     - post: "Renders box plot with column selection"

    :complexity: 3
    """

    def __init__(
        self,
        block_id: str,
        datasource: DataSource,
        subscribes_to=None,
        title: str = "Distribution Comparison (Box Plot)",
        controls: bool = True,
        **kwargs,
    ):
        """
        Initialize box plot preset.

        Args:
            block_id: Unique identifier
            datasource: Data source instance
            subscribes_to: State ID(s) to subscribe to
            title: Chart title
            controls: Control configuration (False=no controls, True=default controls)
            **kwargs: Additional styling parameters and control values
        """
        # Store datasource for use in properties
        self._datasource = datasource
        self._block_id = block_id

        super().__init__(
            block_id=block_id,
            datasource=datasource,
            subscribes_to=subscribes_to,
            title=title,
            controls=controls,
            **kwargs,
        )

    @property
    def default_controls(self) -> Dict[str, Control]:
        """
        Default control definitions for box plot preset.

        Returns:
            Dictionary mapping control names to Control objects
        """
        # Get columns from datasource for control options
        df = self._datasource.get_processed_data()
        numerical_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
        categorical_cols = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        return {
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

    def _get_plot_type(self) -> str:
        """Plot type identifier for box plot."""
        return "box_by_category"

    def _validate_datasource(self, datasource: DataSource) -> None:
        """
        Validate datasource requirements for box plot.

        Args:
            datasource: DataSource instance to validate

        Raises:
            ValueError: If datasource doesn't have required columns
        """
        df = datasource.get_processed_data()
        numerical_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
        categorical_cols = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        if not numerical_cols:
            raise ValueError("BoxPlotPreset requires at least one numerical column")
        if not categorical_cols:
            raise ValueError("BoxPlotPreset requires at least one categorical column")

    def _build_plot_params(
        self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build plot_params for box plot.

        Args:
            final_controls: Final control configuration
            kwargs: Additional parameters and fallback values

        Returns:
            Dictionary of plot parameters
        """
        # Get default values from datasource
        df = self._datasource.get_processed_data()
        numerical_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()
        categorical_cols = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        plot_params = {}

        if "x_col" in final_controls:
            plot_params["x"] = "{{x_col}}"
        else:
            plot_params["x"] = kwargs.get("x_col", categorical_cols[0])

        if "y_col" in final_controls:
            plot_params["y"] = "{{y_col}}"
        else:
            plot_params["y"] = kwargs.get("y_col", numerical_cols[0])

        # Color uses same as x_col
        if "x_col" in final_controls:
            plot_params["color"] = "{{x_col}}"
        else:
            plot_params["color"] = kwargs.get("x_col", categorical_cols[0])

        return plot_params

    def _build_plot_kwargs(
        self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build plot_kwargs for box plot.

        Args:
            final_controls: Final control configuration
            kwargs: Additional parameters and fallback values

        Returns:
            Dictionary of plot kwargs
        """
        return {"title": kwargs.get("title")}

    def _get_plot_title(self, final_controls: Dict[str, Control]) -> Optional[str]:
        """
        Get dynamic plot title for box plot.

        Args:
            final_controls: Final control configuration

        Returns:
            Dynamic title string with placeholders or None
        """
        if "y_col" in final_controls and "x_col" in final_controls:
            return "Box: {{y_col}} by {{x_col}}"
        return None


class KneePlotPreset(BasePreset):
    """
    Interactive knee/elbow plot preset using BasePreset.

    :hierarchy: [Presets | EDA | KneePlotPreset]
    :relates-to:
     - motivated_by: "v0.15.0: Knee/elbow plots for optimization analysis and cluster validation"
     - implements: "preset: 'KneePlotPreset'"
     - uses: ["class: 'BasePreset'", "plot_type: 'knee_plot'"]

    :contract:
     - pre: "DataFrame has numerical columns for x and y axes"
     - post: "Renders knee plot with optional automatic knee detection"
     - dependency: "Automatic knee detection requires 'kneed' package (uv pip install kneed)"
     - controls: "Flexible control configuration via controls parameter"

    :complexity: 3
    """

    def __init__(
        self,
        block_id: str,
        datasource: DataSource,
        subscribes_to=None,
        title: str = "Knee Plot Analysis",
        controls: bool = False,
        **kwargs,
    ):
        """
        Initialize knee plot preset.

        :hierarchy: [Presets | EDA | KneePlotPreset | Initialization]
        :relates-to:
         - motivated_by: "Flexible knee plot with configurable controls using BasePreset"
         - implements: "method: '__init__'"

        :contract:
         - pre: "datasource contains numerical columns"
         - post: "Preset ready with configured controls or no controls"
         - controls_logic: "controls=False: no controls, controls=True: default controls, controls=dict: custom control config"

        Args:
            block_id: Unique identifier
            datasource: Data source instance
            subscribes_to: State ID(s) to subscribe to
            title: Chart title
            controls: Control configuration:
                - False (default): No controls, expects values in kwargs
                - True: Create default controls for all parameters
                - Dict[str, bool|Control]: Custom control configuration:
                    - bool: Enable/disable default control
                    - Control: Replace with custom control
            **kwargs: Additional styling parameters and control values
        """
        # Store datasource for use in properties
        self._datasource = datasource
        self._block_id = block_id

        super().__init__(
            block_id=block_id,
            datasource=datasource,
            subscribes_to=subscribes_to,
            title=title,
            controls=controls,
            **kwargs,
        )

    @property
    def default_controls(self) -> Dict[str, Control]:
        """
        Default control definitions for knee plot preset.

        :hierarchy: [Presets | EDA | KneePlotPreset | DefaultControls]
        :relates-to:
         - motivated_by: "Define available controls for knee plot"
         - implements: "property: 'default_controls'"

        :contract:
         - pre: "datasource contains numerical columns"
         - post: "Returns dict of Control objects for knee plot parameters"

        Returns:
            Dictionary mapping control names to Control objects
        """
        # Get columns from datasource for control options
        df = self._datasource.get_processed_data()
        numerical_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()

        return {
            "x_col": Control(
                component=dcc.Dropdown,
                props={
                    "options": numerical_cols,
                    "value": numerical_cols[0],
                    "clearable": False,
                    "placeholder": "Select X column",
                },
            ),
            "y_col": Control(
                component=dcc.Dropdown,
                props={
                    "options": numerical_cols,
                    "value": (
                        numerical_cols[1]
                        if len(numerical_cols) > 1
                        else numerical_cols[0]
                    ),
                    "clearable": False,
                    "placeholder": "Select Y column",
                },
            ),
            "auto_knee": Control(
                component=dbc.Switch,
                props={
                    "label": "Auto Knee Detection",
                    "value": False,
                },
            ),
            "curve": Control(
                component=dcc.Dropdown,
                props={
                    "options": [
                        {"label": "Concave", "value": "concave"},
                        {"label": "Convex", "value": "convex"},
                    ],
                    "value": "concave",
                    "clearable": False,
                },
            ),
            "direction": Control(
                component=dcc.Dropdown,
                props={
                    "options": [
                        {"label": "Increasing", "value": "increasing"},
                        {"label": "Decreasing", "value": "decreasing"},
                    ],
                    "value": "increasing",
                    "clearable": False,
                },
            ),
            "S": Control(
                component=dcc.Input,
                props={
                    "type": "number",
                    "step": 0.1,
                    "value": 1.0,
                    "min": 0.1,
                    "max": 10.0,
                    "style": {"minWidth": "80px"},
                    "placeholder": "Sensitivity",
                },
            ),
        }

    def _get_plot_type(self) -> str:
        """
        Plot type identifier for knee plot.

        """
        return "knee_plot"

    def _validate_datasource(self, datasource: DataSource) -> None:
        """
        Validate datasource requirements for knee plot.

        :hierarchy: [Presets | EDA | KneePlotPreset | Validation]
        :relates-to:
         - motivated_by: "Ensure datasource has required numerical columns"
         - implements: "method: '_validate_datasource'"

        :contract:
         - pre: "datasource is DataSource instance"
         - post: "Raises ValueError if requirements not met"

        Args:
            datasource: DataSource instance to validate

        Raises:
            ValueError: If datasource doesn't have at least 2 numerical columns
        """
        df = datasource.get_processed_data()
        numerical_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()

        if len(numerical_cols) < 2:
            raise ValueError("KneePlotPreset requires at least two numerical columns")

    def _build_plot_params(
        self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build plot_params for knee plot.

        :hierarchy: [Presets | EDA | KneePlotPreset | PlotParams]
        :relates-to:
         - motivated_by: "Build plot parameters based on available controls"
         - implements: "method: '_build_plot_params'"

        :contract:
         - pre: "final_controls is processed control config, kwargs contains fallback values"
         - post: "Returns plot_params dict with x and y parameters"

        Args:
            final_controls: Final control configuration
            kwargs: Additional parameters and fallback values

        Returns:
            Dictionary of plot parameters
        """
        # Get default values from datasource
        df = self._datasource.get_processed_data()
        numerical_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()

        plot_params = {}

        if "x_col" in final_controls:
            plot_params["x"] = "{{x_col}}"
        else:
            plot_params["x"] = kwargs.get("x_col", numerical_cols[0])

        if "y_col" in final_controls:
            plot_params["y"] = "{{y_col}}"
        else:
            plot_params["y"] = kwargs.get(
                "y_col",
                numerical_cols[1] if len(numerical_cols) > 1 else numerical_cols[0],
            )

        return plot_params

    def _build_plot_kwargs(
        self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build plot_kwargs for knee plot.

        :hierarchy: [Presets | EDA | KneePlotPreset | PlotKwargs]
        :relates-to:
         - motivated_by: "Build plot kwargs based on available controls"
         - implements: "method: '_build_plot_kwargs'"

        :contract:
         - pre: "final_controls is processed control config, kwargs contains fallback values"
         - post: "Returns plot_kwargs dict with knee detection parameters"

        Args:
            final_controls: Final control configuration
            kwargs: Additional parameters and fallback values

        Returns:
            Dictionary of plot kwargs
        """
        plot_kwargs = {}

        if "auto_knee" in final_controls:
            plot_kwargs["auto_knee"] = "{{auto_knee}}"
        else:
            plot_kwargs["auto_knee"] = kwargs.get("auto_knee", False)

        if "curve" in final_controls:
            plot_kwargs["knee_curve"] = "{{curve}}"
        else:
            plot_kwargs["knee_curve"] = kwargs.get("knee_curve", "concave")

        if "direction" in final_controls:
            plot_kwargs["knee_direction"] = "{{direction}}"
        else:
            plot_kwargs["knee_direction"] = kwargs.get("knee_direction", "increasing")

        if "S" in final_controls:
            plot_kwargs["knee_S"] = "{{S}}"
        else:
            plot_kwargs["knee_S"] = kwargs.get("knee_S", 1.0)

        return plot_kwargs

    def _get_plot_title(self, final_controls: Dict[str, Control]) -> Optional[str]:
        """
        Get dynamic plot title for knee plot.

        :hierarchy: [Presets | EDA | KneePlotPreset | PlotTitle]
        :relates-to:
         - motivated_by: "Generate dynamic title when controls are available"
         - implements: "method: '_get_plot_title'"

        :contract:
         - pre: "final_controls is processed control config"
         - post: "Returns title string with placeholders or None"

        Args:
            final_controls: Final control configuration

        Returns:
            Dynamic title string with placeholders or None
        """
        if "x_col" in final_controls and "y_col" in final_controls:
            return "Knee Plot: {{x_col}} vs {{y_col}}"
        return None
