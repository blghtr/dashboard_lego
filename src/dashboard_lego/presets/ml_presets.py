"""
This module provides preset blocks for machine learning visualization.

"""

from typing import Any, Dict, List, Optional, Union

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import dcc, html
from sklearn.metrics import confusion_matrix

from dashboard_lego.blocks.base import BaseBlock
from dashboard_lego.blocks.typed_chart import Control
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.presets.base_preset import BasePreset
from dashboard_lego.utils.plot_registry import register_plot_type

#  TODO: Refactor this from scratch


class ModelSummaryBlock(BaseBlock):
    """
    A block for displaying a summary of model hyperparameters.

        :hierarchy: [Presets | ML | ModelSummaryBlock]
        :relates-to:
          - motivated_by: "Architectural Conclusion: Model summary blocks are essential
            for displaying comprehensive model information and statistics"
          - implements: "block: 'ModelSummaryBlock'"
          - uses: ["block: 'BaseBlock'"]

        :rationale: "Implemented as a custom block inheriting from BaseBlock to provide a flexible layout for displaying key-value data."
        :contract:
          - pre: "Datasource must implement get_summary_data() returning a dict."
          - post: "The block renders a card with the model's summary data."

    """

    def __init__(
        self,
        block_id: str,
        datasource: DataSource,
        title: str = "Model Summary",
        # Style customization parameters
        card_style: Optional[Dict[str, Any]] = None,
        card_className: Optional[str] = None,
        title_style: Optional[Dict[str, Any]] = None,
        title_className: Optional[str] = None,
        content_style: Optional[Dict[str, Any]] = None,
        content_className: Optional[str] = None,
        loading_type: str = "default",
        **kwargs,
    ):
        self.title = title

        # Store style customization parameters
        self.card_style = card_style
        self.card_className = card_className
        self.title_style = title_style
        self.title_className = title_className
        self.content_style = content_style
        self.content_className = content_className
        self.loading_type = loading_type

        super().__init__(block_id, datasource, **kwargs)

    def layout(self) -> html.Div:
        summary_data = self.datasource.get_summary_data()

        if not summary_data:
            return html.Div(dbc.Alert("No summary data available.", color="warning"))

        list_group_items = []
        for key, value in summary_data.items():
            list_group_items.append(dbc.ListGroupItem([html.B(f"{key}: "), str(value)]))

        # Build card props with style overrides
        card_props = {
            "className": self.card_className or "mb-4",
        }
        if self.card_style:
            card_props["style"] = self.card_style

        # Build title props with style overrides
        title_props = {
            "className": self.title_className or "card-header",
        }
        if self.title_style:
            title_props["style"] = self.title_style

        # Build content props with style overrides
        content_props = {}
        if self.content_style:
            content_props["style"] = self.content_style
        if self.content_className:
            content_props["className"] = self.content_className

        return html.Div(
            dbc.Card(
                [
                    dbc.CardHeader(self.title, **title_props),
                    dbc.CardBody(
                        dbc.ListGroup(list_group_items, flush=True), **content_props
                    ),
                ],
                **card_props,
            )
        )


# Register confusion matrix plot
def plot_confusion_matrix(
    df: pd.DataFrame, y_true_col: str, y_pred_col: str, **kwargs
) -> go.Figure:
    """Confusion matrix heatmap."""
    if df.empty or y_true_col not in df.columns or y_pred_col not in df.columns:
        return go.Figure()

    cm = confusion_matrix(df[y_true_col], df[y_pred_col])
    labels = sorted(df[y_true_col].unique())
    fig = px.imshow(
        cm,
        labels=dict(x="Predicted Label", y="True Label", color="Count"),
        x=labels,
        y=labels,
        text_auto=True,
        color_continuous_scale="Blues",
        **kwargs,
    )
    return fig


register_plot_type("confusion_matrix", plot_confusion_matrix)


class ConfusionMatrixPreset(BasePreset):
    """
    Confusion matrix preset using BasePreset.

    Refactored from StaticChartBlock in v0.15.

    :hierarchy: [Presets | ML | ConfusionMatrixPreset]
    :relates-to:
     - motivated_by: "v0.15.0: ML preset using BasePreset"
     - implements: "preset: 'ConfusionMatrixPreset'"
     - uses: ["class: 'BasePreset'"]

    :contract:
     - pre: "Datasource has y_true_col and y_pred_col columns"
     - post: "Renders confusion matrix heatmap"

    :complexity: 2
    """

    def __init__(
        self,
        block_id: str,
        datasource: DataSource,
        y_true_col: str,
        y_pred_col: str,
        title: str = "Confusion Matrix",
        subscribes_to: Union[str, List[str], None] = None,
        controls: bool = False,
        **kwargs,
    ):
        """
        Initialize confusion matrix preset.

        Args:
            block_id: Unique identifier
            datasource: Data source instance
            y_true_col: Column name for true labels
            y_pred_col: Column name for predicted labels
            title: Chart title
            subscribes_to: State ID(s) to subscribe to
            controls: Control configuration (False=no controls, True=default controls)
            **kwargs: Additional styling parameters
        """
        # Store parameters for use in properties
        self._y_true_col = y_true_col
        self._y_pred_col = y_pred_col
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
        Default control definitions for confusion matrix preset.

        Returns:
            Dictionary mapping control names to Control objects
        """
        # Get columns from datasource for control options
        df = self._datasource.get_processed_data()
        categorical_cols = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()

        return {
            "y_true_col": Control(
                component=dcc.Dropdown,
                props={
                    "options": categorical_cols,
                    "value": self._y_true_col,
                    "clearable": False,
                    "style": {"minWidth": "150px"},
                },
            ),
            "y_pred_col": Control(
                component=dcc.Dropdown,
                props={
                    "options": categorical_cols,
                    "value": self._y_pred_col,
                    "clearable": False,
                    "style": {"minWidth": "150px"},
                },
            ),
        }

    @property
    def plot_type(self) -> str:
        """Plot type identifier for confusion matrix."""
        return "confusion_matrix"

    def _validate_datasource(self, datasource: DataSource) -> None:
        """
        Validate datasource requirements for confusion matrix.

        Args:
            datasource: DataSource instance to validate

        Raises:
            ValueError: If datasource doesn't have required columns
        """
        df = datasource.get_processed_data()
        if self._y_true_col not in df.columns:
            raise ValueError(f"Column '{self._y_true_col}' not found in datasource")
        if self._y_pred_col not in df.columns:
            raise ValueError(f"Column '{self._y_pred_col}' not found in datasource")

    def _build_plot_params(
        self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build plot_params for confusion matrix.

        Args:
            final_controls: Final control configuration
            kwargs: Additional parameters and fallback values

        Returns:
            Dictionary of plot parameters
        """
        plot_params = {}

        if "y_true_col" in final_controls:
            plot_params["y_true_col"] = "{{y_true_col}}"
        else:
            plot_params["y_true_col"] = kwargs.get("y_true_col", self._y_true_col)

        if "y_pred_col" in final_controls:
            plot_params["y_pred_col"] = "{{y_pred_col}}"
        else:
            plot_params["y_pred_col"] = kwargs.get("y_pred_col", self._y_pred_col)

        return plot_params

    def _build_plot_kwargs(
        self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build plot_kwargs for confusion matrix.

        Args:
            final_controls: Final control configuration
            kwargs: Additional parameters and fallback values

        Returns:
            Dictionary of plot kwargs
        """
        return {"title": kwargs.get("title", "Confusion Matrix")}

    def _get_plot_title(self, final_controls: Dict[str, Control]) -> Optional[str]:
        """
        Get dynamic plot title for confusion matrix.

        Args:
            final_controls: Final control configuration

        Returns:
            Dynamic title string with placeholders or None
        """
        if "y_true_col" in final_controls and "y_pred_col" in final_controls:
            return "Confusion Matrix: {{y_true_col}} vs {{y_pred_col}}"
        return None


# Register ROC curve plot
def plot_roc_curve(
    df: pd.DataFrame, y_true_col: str, y_score_cols: list, **kwargs
) -> go.Figure:
    """ROC curve plot (binary or multi-class)."""
    if df.empty or y_true_col not in df.columns:
        return go.Figure()

    from sklearn.metrics import auc, roc_curve
    from sklearn.preprocessing import label_binarize

    y_true = df[y_true_col]
    y_score = df[y_score_cols]
    classes = sorted(y_true.unique())

    fig = go.Figure()
    fig.add_shape(type="line", line=dict(dash="dash"), x0=0, x1=1, y0=0, y1=1)

    if len(classes) > 2:  # Multi-class
        y_true_bin = label_binarize(y_true, classes=classes)
        for i, class_name in enumerate(classes):
            fpr, tpr, _ = roc_curve(y_true_bin[:, i], y_score.iloc[:, i])
            roc_auc = auc(fpr, tpr)
            fig.add_trace(
                go.Scatter(
                    x=fpr,
                    y=tpr,
                    name=f"{class_name} (AUC = {roc_auc:.2f})",
                    mode="lines",
                )
            )
    else:  # Binary
        fpr, tpr, _ = roc_curve(y_true, y_score.iloc[:, 0])
        roc_auc = auc(fpr, tpr)
        fig.add_trace(
            go.Scatter(x=fpr, y=tpr, name=f"AUC = {roc_auc:.2f}", mode="lines")
        )

    fig.update_layout(
        xaxis_title="False Positive Rate",
        yaxis_title="True Positive Rate",
        yaxis=dict(scaleanchor="x", scaleratio=1),
        xaxis=dict(constrain="domain"),
    )
    return fig


register_plot_type("roc_curve", plot_roc_curve)


class RocAucCurvePreset(BasePreset):
    """
    ROC curve preset using BasePreset.

    Refactored from StaticChartBlock in v0.15.

    :hierarchy: [Presets | ML | RocAucCurvePreset]
    :relates-to:
     - motivated_by: "v0.15.0: ML preset using BasePreset"
     - implements: "preset: 'RocAucCurvePreset'"
     - uses: ["class: 'BasePreset'"]

    :contract:
     - pre: "Datasource has y_true_col and y_score_cols"
     - post: "Renders ROC curve (binary or multi-class)"

    :complexity: 3
    """

    def __init__(
        self,
        block_id: str,
        datasource: DataSource,
        y_true_col: str,
        y_score_cols: list[str],
        title: str = "ROC Curve",
        subscribes_to: Union[str, List[str], None] = None,
        controls: bool = False,
        **kwargs,
    ):
        """
        Initialize ROC curve preset.

        Args:
            block_id: Unique identifier
            datasource: Data source instance
            y_true_col: Column name for true labels
            y_score_cols: List of column names for prediction scores
            title: Chart title
            subscribes_to: State ID(s) to subscribe to
            controls: Control configuration (False=no controls, True=default controls)
            **kwargs: Additional styling parameters
        """
        # Store parameters for use in properties
        self._y_true_col = y_true_col
        self._y_score_cols = y_score_cols
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
        Default control definitions for ROC curve preset.

        Returns:
            Dictionary mapping control names to Control objects
        """
        # Get columns from datasource for control options
        df = self._datasource.get_processed_data()
        categorical_cols = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()
        numerical_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()

        return {
            "y_true_col": Control(
                component=dcc.Dropdown,
                props={
                    "options": categorical_cols,
                    "value": self._y_true_col,
                    "clearable": False,
                    "style": {"minWidth": "150px"},
                },
            ),
            "y_score_cols": Control(
                component=dcc.Dropdown,
                props={
                    "options": numerical_cols,
                    "value": self._y_score_cols,
                    "multi": True,
                    "clearable": False,
                    "style": {"minWidth": "150px"},
                },
            ),
        }

    @property
    def plot_type(self) -> str:
        """Plot type identifier for ROC curve."""
        return "roc_curve"

    def _validate_datasource(self, datasource: DataSource) -> None:
        """
        Validate datasource requirements for ROC curve.

        Args:
            datasource: DataSource instance to validate

        Raises:
            ValueError: If datasource doesn't have required columns
        """
        df = datasource.get_processed_data()
        if self._y_true_col not in df.columns:
            raise ValueError(f"Column '{self._y_true_col}' not found in datasource")
        for col in self._y_score_cols:
            if col not in df.columns:
                raise ValueError(f"Column '{col}' not found in datasource")

    def _build_plot_params(
        self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build plot_params for ROC curve.

        Args:
            final_controls: Final control configuration
            kwargs: Additional parameters and fallback values

        Returns:
            Dictionary of plot parameters
        """
        plot_params = {}

        if "y_true_col" in final_controls:
            plot_params["y_true_col"] = "{{y_true_col}}"
        else:
            plot_params["y_true_col"] = kwargs.get("y_true_col", self._y_true_col)

        if "y_score_cols" in final_controls:
            plot_params["y_score_cols"] = "{{y_score_cols}}"
        else:
            plot_params["y_score_cols"] = kwargs.get("y_score_cols", self._y_score_cols)

        return plot_params

    def _build_plot_kwargs(
        self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build plot_kwargs for ROC curve.

        Args:
            final_controls: Final control configuration
            kwargs: Additional parameters and fallback values

        Returns:
            Dictionary of plot kwargs
        """
        return {"title": kwargs.get("title", "ROC Curve")}

    def _get_plot_title(self, final_controls: Dict[str, Control]) -> Optional[str]:
        """
        Get dynamic plot title for ROC curve.

        Args:
            final_controls: Final control configuration

        Returns:
            Dynamic title string with placeholders or None
        """
        if "y_true_col" in final_controls:
            return "ROC Curve: {{y_true_col}}"
        return None


# Register plot function for feature importance
def plot_feature_importance_horizontal(
    df: pd.DataFrame, x: str, y: str, **kwargs
) -> go.Figure:
    """
    Horizontal bar chart for feature importance.

    :hierarchy: [Presets | ML | Plots | FeatureImportance]
    :contract:
     - pre: "df has x (importance) and y (feature) columns"
     - post: "Returns sorted horizontal bar chart"
    """
    if df.empty or x not in df.columns or y not in df.columns:
        return go.Figure()

    df_sorted = df.sort_values(by=x, ascending=True)
    fig = px.bar(df_sorted, x=x, y=y, orientation="h", **kwargs)
    fig.update_layout(yaxis_title="Feature")
    return fig


# Register ML plot types
register_plot_type("feature_importance_horizontal", plot_feature_importance_horizontal)


class FeatureImportancePreset(BasePreset):
    """
    Feature importance preset using BasePreset.

    Refactored from StaticChartBlock in v0.15.

    :hierarchy: [Presets | ML | FeatureImportancePreset]
    :relates-to:
     - motivated_by: "v0.15: Use BasePreset with plot_registry"
     - implements: "preset: 'FeatureImportancePreset'"
     - uses: ["class: 'BasePreset'"]

    :contract:
     - pre: "Datasource returns df with feature_col and importance_col"
     - post: "Renders sorted horizontal bar chart"

    :complexity: 2
    """

    def __init__(
        self,
        block_id: str,
        datasource: DataSource,
        feature_col: str,
        importance_col: str,
        title: str = "Feature Importance",
        subscribes_to: Union[str, List[str], None] = None,
        controls: bool = True,
        **kwargs,
    ):
        """
        Initialize feature importance preset.

        Args:
            block_id: Unique identifier
            datasource: Data source instance
            feature_col: Column name for feature names
            importance_col: Column name for importance values
            title: Chart title
            subscribes_to: State ID(s) to subscribe to
            controls: Control configuration (False=no controls, True=default controls)
            **kwargs: Additional styling parameters
        """
        # Store parameters for use in properties
        self._feature_col = feature_col
        self._importance_col = importance_col
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
        Default control definitions for feature importance preset.

        Returns:
            Dictionary mapping control names to Control objects
        """
        # Get columns from datasource for control options
        df = self._datasource.get_processed_data()
        categorical_cols = df.select_dtypes(
            include=["object", "category"]
        ).columns.tolist()
        numerical_cols = df.select_dtypes(include=["float64", "int64"]).columns.tolist()

        return {
            "feature_col": Control(
                component=dcc.Dropdown,
                props={
                    "options": categorical_cols,
                    "value": self._feature_col,
                    "clearable": False,
                    "style": {"minWidth": "150px"},
                },
            ),
            "importance_col": Control(
                component=dcc.Dropdown,
                props={
                    "options": numerical_cols,
                    "value": self._importance_col,
                    "clearable": False,
                    "style": {"minWidth": "150px"},
                },
            ),
        }

    @property
    def plot_type(self) -> str:
        """Plot type identifier for feature importance."""
        return "feature_importance_horizontal"

    def _validate_datasource(self, datasource: DataSource) -> None:
        """
        Validate datasource requirements for feature importance.

        Args:
            datasource: DataSource instance to validate

        Raises:
            ValueError: If datasource doesn't have required columns
        """
        df = datasource.get_processed_data()
        if self._feature_col not in df.columns:
            raise ValueError(f"Column '{self._feature_col}' not found in datasource")
        if self._importance_col not in df.columns:
            raise ValueError(f"Column '{self._importance_col}' not found in datasource")

    def _build_plot_params(
        self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build plot_params for feature importance.

        Args:
            final_controls: Final control configuration
            kwargs: Additional parameters and fallback values

        Returns:
            Dictionary of plot parameters
        """
        plot_params = {}

        if "importance_col" in final_controls:
            plot_params["x"] = "{{importance_col}}"
        else:
            plot_params["x"] = kwargs.get("importance_col", self._importance_col)

        if "feature_col" in final_controls:
            plot_params["y"] = "{{feature_col}}"
        else:
            plot_params["y"] = kwargs.get("feature_col", self._feature_col)

        return plot_params

    def _build_plot_kwargs(
        self, final_controls: Dict[str, Control], kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Build plot_kwargs for feature importance.

        Args:
            final_controls: Final control configuration
            kwargs: Additional parameters and fallback values

        Returns:
            Dictionary of plot kwargs
        """
        return {"title": kwargs.get("title", "Feature Importance")}

    def _get_plot_title(self, final_controls: Dict[str, Control]) -> Optional[str]:
        """
        Get dynamic plot title for feature importance.

        Args:
            final_controls: Final control configuration

        Returns:
            Dynamic title string with placeholders or None
        """
        if "feature_col" in final_controls:
            return "Feature Importance: {{feature_col}}"
        return None
