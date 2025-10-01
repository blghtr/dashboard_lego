import dash
import dash_bootstrap_components as dbc
import pandas as pd

from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.core.page import DashboardPage
from dashboard_lego.presets.ml_presets import (
    ConfusionMatrixPreset,
    FeatureImportancePreset,
    MetricCardBlock,
    ModelSummaryBlock,
    RocAucCurvePreset,
)

# 1. Create dummy ML results dataframes
# In a real scenario, this would come from a file or a database
results_data = {
    "y_true": ["Cat", "Dog", "Cat", "Bird", "Dog", "Bird", "Cat", "Dog", "Bird", "Cat"],
    "y_pred": ["Cat", "Dog", "Dog", "Bird", "Cat", "Bird", "Cat", "Dog", "Bird", "Dog"],
    # Add prediction probabilities for each class
    "y_score_cat": [0.8, 0.1, 0.6, 0.1, 0.4, 0.2, 0.9, 0.2, 0.1, 0.5],
    "y_score_dog": [0.1, 0.8, 0.3, 0.1, 0.5, 0.1, 0.05, 0.7, 0.1, 0.4],
    "y_score_bird": [0.1, 0.1, 0.1, 0.8, 0.1, 0.7, 0.05, 0.1, 0.8, 0.1],
}
df_results = pd.DataFrame(results_data)

feature_importance_data = {
    "feature": ["Feat1", "Feat2", "Feat3", "Feat4", "Feat5"],
    "importance": [0.3, 0.25, 0.2, 0.15, 0.1],
}
df_importance = pd.DataFrame(feature_importance_data)

model_summary_data = {
    "Model Type": "Random Forest Classifier",
    "n_estimators": 100,
    "max_depth": 10,
    "criterion": "gini",
}

metrics_data = {"Accuracy": 0.85, "Precision": 0.88, "Recall": 0.85, "F1-Score": 0.86}


# 2. Define a data source for the ML results
class GenericDataSource(BaseDataSource):
    def __init__(self, df=None, summary=None, kpis=None):
        self._df = df
        self._summary = summary
        self._kpis = kpis
        super().__init__()

    def _load_data(self, params: dict) -> pd.DataFrame:
        # If no DataFrame is provided, return empty DataFrame
        if self._df is None:
            return pd.DataFrame()
        return self._df

    def get_summary_data(self) -> dict:
        return self._summary

    def get_kpis(self) -> dict:
        return self._kpis

    def get_filter_options(self, filter_name: str) -> list:
        return []

    def get_summary(self) -> str:
        return ""


# 3. Instantiate the data sources
results_datasource = GenericDataSource(df=df_results)
results_datasource.init_data()

importance_datasource = GenericDataSource(df=df_importance)
importance_datasource.init_data()

summary_datasource = GenericDataSource(summary=model_summary_data)
summary_datasource.init_data()

metrics_datasource = GenericDataSource(kpis=metrics_data)
metrics_datasource.init_data()

# 4. Define the dashboard blocks using the new presets
model_summary_block = ModelSummaryBlock(
    block_id="model_summary", datasource=summary_datasource, title="Model Summary"
)

metric_card_block = MetricCardBlock(
    block_id="metric_cards",
    datasource=metrics_datasource,
    kpi_definitions=[
        {"key": "Accuracy", "title": "Accuracy"},
        {"key": "Precision", "title": "Precision"},
        {"key": "Recall", "title": "Recall"},
        {"key": "F1-Score", "title": "F1-Score"},
    ],
    subscribes_to="dummy_state",
    title="Overall Metrics",
)

feature_importance_block = FeatureImportancePreset(
    block_id="feature_importance",
    datasource=importance_datasource,
    feature_col="feature",
    importance_col="importance",
    title="Feature Importance",
)

confusion_matrix_block = ConfusionMatrixPreset(
    block_id="confusion_matrix",
    datasource=results_datasource,
    y_true_col="y_true",
    y_pred_col="y_pred",
    title="Model Performance: Confusion Matrix",
)

roc_auc_block = RocAucCurvePreset(
    block_id="roc_auc_curve",
    datasource=results_datasource,
    y_true_col="y_true",
    y_score_cols=["y_score_cat", "y_score_dog", "y_score_bird"],
    title="Model Performance: ROC Curve",
)

# 5. Create the Dashboard Page
dashboard_page = DashboardPage(
    title="Machine Learning Dashboard",
    blocks=[
        [model_summary_block, metric_card_block],
        [feature_importance_block],
        [confusion_matrix_block, roc_auc_block],
    ],
    theme=dbc.themes.CYBORG,
)

# 6. Set up and run the Dash app
app = dash.Dash(__name__, external_stylesheets=[dashboard_page.theme])
app.layout = dashboard_page.build_layout()
dashboard_page.register_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)
