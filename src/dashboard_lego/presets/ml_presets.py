"""
This module provides preset blocks for machine learning visualization.

"""

from typing import Any, Dict, Optional

import dash_bootstrap_components as dbc
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from dash import html
from sklearn.metrics import confusion_matrix

from dashboard_lego.blocks.base import BaseBlock
from dashboard_lego.blocks.chart import StaticChartBlock
from dashboard_lego.blocks.kpi import KPIBlock
from dashboard_lego.core.datasource import BaseDataSource


class MetricCardBlock(KPIBlock):
    """
    An extension of KPIBlock for displaying ML metrics in a compact list.

        :hierarchy: [Presets | ML | MetricCardBlock]
        :relates-to:
          - motivated_by: "Architectural Conclusion: Metric cards provide a standardized
            way to display key performance indicators in ML dashboards"
          - implements: "block: 'MetricCardBlock'"
          - uses: ["block: 'KPIBlock'"]

        :rationale: "Subclassed KPIBlock to reuse its data-handling logic while providing a more compact, list-based layout suitable for displaying multiple ML metrics."
        :contract:
          - pre: "Inherits the contract from KPIBlock."
          - post: "The block renders a card with a list of metrics."

    """

    def __init__(
        self,
        block_id: str,
        datasource: BaseDataSource,
        kpi_definitions: list[dict[str, str]],
        subscribes_to: str,
        title: str = "Metrics",
        **kwargs,
    ):
        self.title = title
        super().__init__(block_id, datasource, kpi_definitions, subscribes_to, **kwargs)

    def _update_kpi_cards(self, *args) -> html.Div:
        kpi_data = self.datasource.get_kpis()
        if not kpi_data:
            return html.Div(dbc.Alert("No KPI data available.", color="warning"))

        list_group_items = []
        for definition in self.kpi_definitions:
            key = definition["key"]
            value = kpi_data.get(key, "N/A")
            formatted_value = (
                f"{value:.3f}" if isinstance(value, (int, float)) else str(value)
            )
            list_group_items.append(
                dbc.ListGroupItem(
                    [html.B(f"{definition['title']}: "), formatted_value],
                    className="d-flex justify-content-between align-items-center",
                )
            )

        return html.Div(
            dbc.Card(
                [
                    dbc.CardHeader(self.title),
                    dbc.CardBody(dbc.ListGroup(list_group_items, flush=True)),
                ]
            )
        )


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
        datasource: BaseDataSource,
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


class ConfusionMatrixPreset(StaticChartBlock):
    """
    A preset block for displaying a confusion matrix.

    This block automatically calculates and displays a confusion matrix from
    true and predicted labels.

        :hierarchy: [Presets | ML | ConfusionMatrixPreset]
        :relates-to:
          - motivated_by: "Architectural Conclusion: Confusion matrices are fundamental
            for evaluating classification model performance"
          - implements: "preset: 'ConfusionMatrixPreset'"
          - uses: ["block: 'StaticChartBlock'"]

        :rationale: "Implemented as a subclass of StaticChartBlock with internal plotting logic to provide a simple user experience."
        :contract:
          - pre: "Datasource must contain columns specified by y_true_col and y_pred_col."
          - post: "The block renders a heatmap of the confusion matrix."

    """

    def __init__(
        self,
        block_id: str,
        datasource: BaseDataSource,
        y_true_col: str,
        y_pred_col: str,
        title: str = "Confusion Matrix",
        **kwargs,
    ):
        self.y_true_col = y_true_col
        self.y_pred_col = y_pred_col
        super().__init__(
            block_id=block_id,
            datasource=datasource,
            title=title,
            chart_generator=self._generate_chart,
            subscribes_to="dummy_state",  # This preset is static for now
            **kwargs,
        )

    def _generate_chart(self, df: pd.DataFrame, ctx) -> go.Figure:
        """
        Generates the confusion matrix heatmap.

        """
        cm = confusion_matrix(df[self.y_true_col], df[self.y_pred_col])
        labels = sorted(df[self.y_true_col].unique())
        fig = px.imshow(
            cm,
            labels=dict(x="Predicted Label", y="True Label", color="Count"),
            x=labels,
            y=labels,
            text_auto=True,
            color_continuous_scale="Blues",
        )
        fig.update_layout(title_text=self.title)
        return fig


class RocAucCurvePreset(StaticChartBlock):
    """
    A preset block for displaying a Receiver Operating Characteristic (ROC) curve.

    This block automatically calculates and displays an ROC curve and AUC score.
    It supports both binary and multi-class classification (using One-vs-Rest).

        :hierarchy: [Presets | ML | RocAucCurvePreset]
        :relates-to:
          - motivated_by: "Architectural Conclusion: ROC curves are essential for
            evaluating binary classification model performance and thresholds"
          - implements: "preset: 'RocAucCurvePreset'"
          - uses: ["block: 'StaticChartBlock'"]

        :rationale: "Implemented as a subclass of StaticChartBlock with internal plotting logic for simplicity. Uses a One-vs-Rest approach for multi-class problems as a robust default."
        :contract:
          - pre: "Datasource must contain columns specified by y_true_col and y_score_cols."
          - post: "The block renders a plot of the ROC curve(s)."

    """

    def __init__(
        self,
        block_id: str,
        datasource: BaseDataSource,
        y_true_col: str,
        y_score_cols: list[str],
        title: str = "ROC Curve",
        **kwargs,
    ):
        self.y_true_col = y_true_col
        self.y_score_cols = y_score_cols
        super().__init__(
            block_id=block_id,
            datasource=datasource,
            title=title,
            chart_generator=self._generate_chart,
            subscribes_to="dummy_state",
            **kwargs,
        )

    def _generate_chart(self, df: pd.DataFrame, ctx) -> go.Figure:
        """
        Generates the ROC curve plot.

        """
        from sklearn.metrics import auc, roc_curve
        from sklearn.preprocessing import label_binarize

        y_true = df[self.y_true_col]
        y_score = df[self.y_score_cols]
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
            title_text=self.title,
        )
        return fig


class FeatureImportancePreset(StaticChartBlock):
    """
    A preset block for displaying feature importances.

    This block creates a sorted, horizontal bar chart of feature importances.

        :hierarchy: [Presets | ML | FeatureImportancePreset]
        :relates-to:
          - motivated_by: "Architectural Conclusion: Feature importance visualization
            is crucial for understanding model interpretability and feature relevance"
          - implements: "preset: 'FeatureImportancePreset'"
          - uses: ["block: 'StaticChartBlock'"]

        :rationale: "Implemented as a subclass of StaticChartBlock that expects a datasource with feature and importance columns. This is a clean, decoupled approach."
        :contract:
          - pre: "Datasource must contain columns specified by feature_col and importance_col."
          - post: "The block renders a sorted horizontal bar chart."

    """

    def __init__(
        self,
        block_id: str,
        datasource: BaseDataSource,
        feature_col: str,
        importance_col: str,
        title: str = "Feature Importance",
        **kwargs,
    ):
        self.feature_col = feature_col
        self.importance_col = importance_col
        super().__init__(
            block_id=block_id,
            datasource=datasource,
            title=title,
            chart_generator=self._generate_chart,
            subscribes_to="dummy_state",
            **kwargs,
        )

    def _generate_chart(self, df: pd.DataFrame, ctx) -> go.Figure:
        """
        Generates the feature importance bar chart.

        """
        df_sorted = df.sort_values(by=self.importance_col, ascending=True)
        fig = px.bar(
            df_sorted,
            x=self.importance_col,
            y=self.feature_col,
            orientation="h",
            title=self.title,
        )
        fig.update_layout(yaxis_title="Feature")
        return fig
