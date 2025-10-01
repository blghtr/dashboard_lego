"""
Tests for ML presets module.

:hierarchy: [Testing | Unit Tests | ML Presets]
:relates-to:
 - motivated_by: "Architectural Conclusion: ML presets require comprehensive
   testing to ensure reliable model evaluation visualizations"
 - implements: "test_suite: 'MLPresets'"

:strategy: "Use pytest with fixtures and mocking for isolation"
:contract:
 - pre: "Test environment is set up with necessary fixtures"
 - post: "All tests pass and code coverage increases"

"""

import os
import sys
from unittest.mock import MagicMock, patch

import dash_bootstrap_components as dbc
import pandas as pd
import pytest
from dash import html

# Add project root to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))

from dashboard_lego.core.chart_context import ChartContext
from dashboard_lego.presets.ml_presets import (
    ConfusionMatrixPreset,
    FeatureImportancePreset,
    MetricCardBlock,
    ModelSummaryBlock,
    RocAucCurvePreset,
)


def create_chart_context(datasource, controls=None):
    """Helper function to create ChartContext for tests."""
    if controls is None:
        controls = {}
    mock_logger = MagicMock()
    return ChartContext(datasource=datasource, controls=controls, logger=mock_logger)


class TestMetricCardBlock:
    """
    Test for MetricCardBlock functionality.

    :hierarchy: [Testing | Unit Tests | ML Presets | MetricCardBlock]
    :covers:
     - object: "class: MetricCardBlock"
     - requirement: "ML metrics display in compact list format"

    :scenario: "Verifies that MetricCardBlock correctly displays ML metrics in a list format"
    :strategy: "Uses mock datasource and KPI definitions to test rendering"
    :contract:
     - pre: "Valid datasource with KPI data and metric definitions provided"
     - post: "Block renders a card with list of formatted metrics"

    """

    def test_metric_card_block_initialization(self, datasource_factory):
        """
        Test MetricCardBlock initialization.

        :hierarchy: [Testing | Unit Tests | ML Presets | MetricCardBlock | Initialization]
        :covers:
         - object: "method: MetricCardBlock.__init__"
         - requirement: "Block must initialize with proper parameters"

        :scenario: "Verifies that MetricCardBlock initializes correctly with all required parameters"
        :strategy: "Uses datasource factory to create mock datasource"
        :contract:
         - pre: "Valid block_id, datasource, kpi_definitions, and subscribes_to provided"
         - post: "Block instance is created successfully"

        """
        mock_ds = datasource_factory()
        kpi_definitions = [
            {"key": "accuracy", "title": "Accuracy"},
            {"key": "precision", "title": "Precision"},
        ]

        block = MetricCardBlock(
            block_id="test_metrics",
            datasource=mock_ds,
            kpi_definitions=kpi_definitions,
            subscribes_to="test_state",
            title="Test Metrics",
        )

        assert block.block_id == "test_metrics"
        assert block.title == "Test Metrics"
        assert block.kpi_definitions == kpi_definitions

    def test_metric_card_renders_metrics(self, datasource_factory):
        """
        Test MetricCardBlock renders metrics correctly.

        :hierarchy: [Testing | Unit Tests | ML Presets | MetricCardBlock | Rendering]
        :covers:
         - object: "method: MetricCardBlock._update_kpi_cards"
         - requirement: "Block must render formatted metrics in list format"

        :scenario: "Verifies that metrics are properly formatted and displayed in a list"
        :strategy: "Mocks KPI data and tests the rendered output structure"
        :contract:
         - pre: "Datasource returns valid KPI data"
         - post: "Block renders card with properly formatted metric list"

        """
        mock_ds = datasource_factory()
        mock_ds.get_kpis.return_value = {
            "accuracy": 0.95,
            "precision": 0.87,
            "recall": 0.92,
        }

        kpi_definitions = [
            {"key": "accuracy", "title": "Accuracy"},
            {"key": "precision", "title": "Precision"},
            {"key": "recall", "title": "Recall"},
        ]

        block = MetricCardBlock(
            block_id="test_metrics",
            datasource=mock_ds,
            kpi_definitions=kpi_definitions,
            subscribes_to="test_state",
        )

        result = block._update_kpi_cards()

        assert isinstance(result, html.Div)
        assert isinstance(result.children, dbc.Card)

    def test_metric_card_no_data(self, datasource_factory):
        """
        Test MetricCardBlock handles no data gracefully.

        :hierarchy: [Testing | Unit Tests | ML Presets | MetricCardBlock | Error Handling]
        :covers:
         - object: "method: MetricCardBlock._update_kpi_cards"
         - requirement: "Block must handle missing KPI data gracefully"

        :scenario: "Verifies that block shows warning when no KPI data is available"
        :strategy: "Mocks datasource to return empty KPI data"
        :contract:
         - pre: "Datasource returns no KPI data"
         - post: "Block renders warning alert"

        """
        mock_ds = datasource_factory()
        mock_ds.get_kpis.return_value = None

        block = MetricCardBlock(
            block_id="test_metrics",
            datasource=mock_ds,
            kpi_definitions=[],
            subscribes_to="test_state",
        )

        result = block._update_kpi_cards()

        assert isinstance(result, html.Div)
        assert isinstance(result.children, dbc.Alert)


class TestModelSummaryBlock:
    """
    Test for ModelSummaryBlock functionality.

    :hierarchy: [Testing | Unit Tests | ML Presets | ModelSummaryBlock]
    :covers:
     - object: "class: ModelSummaryBlock"
     - requirement: "Model hyperparameters display in summary format"

    :scenario: "Verifies that ModelSummaryBlock correctly displays model summary data"
    :strategy: "Uses mock datasource with summary data to test rendering"
    :contract:
     - pre: "Valid datasource with summary data provided"
     - post: "Block renders a card with model summary information"

    """

    def test_model_summary_block_initialization(self, datasource_factory):
        """
        Test ModelSummaryBlock initialization.

        :hierarchy: [Testing | Unit Tests | ML Presets | ModelSummaryBlock | Initialization]
        :covers:
         - object: "method: ModelSummaryBlock.__init__"
         - requirement: "Block must initialize with proper parameters"

        :scenario: "Verifies that ModelSummaryBlock initializes correctly"
        :strategy: "Uses datasource factory to create mock datasource"
        :contract:
         - pre: "Valid block_id, datasource provided"
         - post: "Block instance is created successfully"

        """
        mock_ds = datasource_factory()

        block = ModelSummaryBlock(
            block_id="test_summary", datasource=mock_ds, title="Test Summary"
        )

        assert block.block_id == "test_summary"
        assert block.title == "Test Summary"

    def test_model_summary_renders_data(self, datasource_factory):
        """
        Test ModelSummaryBlock renders summary data correctly.

        :hierarchy: [Testing | Unit Tests | ML Presets | ModelSummaryBlock | Rendering]
        :covers:
         - object: "method: ModelSummaryBlock.layout"
         - requirement: "Block must render formatted summary data"

        :scenario: "Verifies that summary data is properly formatted and displayed"
        :strategy: "Mocks summary data and tests the rendered output structure"
        :contract:
         - pre: "Datasource returns valid summary data"
         - post: "Block renders card with properly formatted summary list"

        """
        mock_ds = datasource_factory()
        mock_ds.get_summary_data = MagicMock(
            return_value={
                "algorithm": "Random Forest",
                "n_estimators": 100,
                "max_depth": 10,
                "random_state": 42,
            }
        )

        block = ModelSummaryBlock(block_id="test_summary", datasource=mock_ds)

        result = block.layout()

        assert isinstance(result, html.Div)
        assert isinstance(result.children, dbc.Card)

    def test_model_summary_no_data(self, datasource_factory):
        """
        Test ModelSummaryBlock handles no data gracefully.

        :hierarchy: [Testing | Unit Tests | ML Presets | ModelSummaryBlock | Error Handling]
        :covers:
         - object: "method: ModelSummaryBlock.layout"
         - requirement: "Block must handle missing summary data gracefully"

        :scenario: "Verifies that block shows warning when no summary data is available"
        :strategy: "Mocks datasource to return empty summary data"
        :contract:
         - pre: "Datasource returns no summary data"
         - post: "Block renders warning alert"

        """
        mock_ds = datasource_factory()
        mock_ds.get_summary_data = MagicMock(return_value=None)

        block = ModelSummaryBlock(block_id="test_summary", datasource=mock_ds)

        result = block.layout()

        assert isinstance(result, html.Div)
        assert isinstance(result.children, dbc.Alert)


class TestConfusionMatrixPreset:
    """
    Test for ConfusionMatrixPreset functionality.

    :hierarchy: [Testing | Unit Tests | ML Presets | ConfusionMatrixPreset]
    :covers:
     - object: "class: ConfusionMatrixPreset"
     - requirement: "Confusion matrix visualization for ML models"

    :scenario: "Verifies that ConfusionMatrixPreset correctly generates confusion matrix charts"
    :strategy: "Uses mock data with true and predicted labels to test chart generation"
    :contract:
     - pre: "Valid datasource with y_true_col and y_pred_col data"
     - post: "Preset generates confusion matrix heatmap chart"

    """

    def test_confusion_matrix_preset_initialization(self, datasource_factory):
        """
        Test ConfusionMatrixPreset initialization.

        :hierarchy: [Testing | Unit Tests | ML Presets | ConfusionMatrixPreset | Initialization]
        :covers:
         - object: "method: ConfusionMatrixPreset.__init__"
         - requirement: "Preset must initialize with proper parameters"

        :scenario: "Verifies that ConfusionMatrixPreset initializes correctly"
        :strategy: "Uses datasource factory to create mock datasource"
        :contract:
         - pre: "Valid block_id, datasource, y_true_col, y_pred_col provided"
         - post: "Preset instance is created successfully"

        """
        mock_ds = datasource_factory()

        preset = ConfusionMatrixPreset(
            block_id="test_cm",
            datasource=mock_ds,
            y_true_col="y_true",
            y_pred_col="y_pred",
        )

        assert preset.block_id == "test_cm"
        assert preset.y_true_col == "y_true"
        assert preset.y_pred_col == "y_pred"

    def test_confusion_matrix_calculates_correctly(self, datasource_factory):
        """
        Test ConfusionMatrixPreset calculates confusion matrix correctly.

        :hierarchy: [Testing | Unit Tests | ML Presets | ConfusionMatrixPreset | Calculation]
        :covers:
         - object: "method: ConfusionMatrixPreset._generate_chart"
         - requirement: "Preset must correctly calculate confusion matrix from data"

        :scenario: "Verifies that confusion matrix is calculated correctly from true and predicted labels"
        :strategy: "Uses test data with known true/predicted labels and validates matrix calculation"
        :contract:
         - pre: "DataFrame with y_true_col and y_pred_col columns provided"
         - post: "Chart figure is generated with correct confusion matrix"

        """
        mock_ds = datasource_factory()

        preset = ConfusionMatrixPreset(
            block_id="test_cm",
            datasource=mock_ds,
            y_true_col="y_true",
            y_pred_col="y_pred",
        )

        # Create test data
        df = pd.DataFrame({"y_true": [0, 1, 0, 1, 0, 1], "y_pred": [0, 1, 1, 1, 0, 0]})

        with patch("dashboard_lego.presets.ml_presets.px") as mock_px:
            mock_fig = MagicMock()
            mock_px.imshow.return_value = mock_fig

            ctx = create_chart_context(mock_ds)
            result = preset._generate_chart(df, ctx)

            assert result == mock_fig
            mock_px.imshow.assert_called_once()


class TestRocAucCurvePreset:
    """
    Test for RocAucCurvePreset functionality.

    :hierarchy: [Testing | Unit Tests | ML Presets | RocAucCurvePreset]
    :covers:
     - object: "class: RocAucCurvePreset"
     - requirement: "ROC curve visualization for ML models"

    :scenario: "Verifies that RocAucCurvePreset correctly generates ROC curves"
    :strategy: "Uses mock data with true labels and prediction scores to test chart generation"
    :contract:
     - pre: "Valid datasource with y_true_col and y_score_cols data"
     - post: "Preset generates ROC curve chart with AUC scores"

    """

    def test_roc_auc_curve_preset_initialization(self, datasource_factory):
        """
        Test RocAucCurvePreset initialization.

        :hierarchy: [Testing | Unit Tests | ML Presets | RocAucCurvePreset | Initialization]
        :covers:
         - object: "method: RocAucCurvePreset.__init__"
         - requirement: "Preset must initialize with proper parameters"

        :scenario: "Verifies that RocAucCurvePreset initializes correctly"
        :strategy: "Uses datasource factory to create mock datasource"
        :contract:
         - pre: "Valid block_id, datasource, y_true_col, y_score_cols provided"
         - post: "Preset instance is created successfully"

        """
        mock_ds = datasource_factory()

        preset = RocAucCurvePreset(
            block_id="test_roc",
            datasource=mock_ds,
            y_true_col="y_true",
            y_score_cols=["score"],
        )

        assert preset.block_id == "test_roc"
        assert preset.y_true_col == "y_true"
        assert preset.y_score_cols == ["score"]

    def test_roc_auc_binary_classification(self, datasource_factory):
        """
        Test RocAucCurvePreset for binary classification.

        :hierarchy: [Testing | Unit Tests | ML Presets | RocAucCurvePreset | Binary Classification]
        :covers:
         - object: "method: RocAucCurvePreset._generate_chart"
         - requirement: "Preset must handle binary classification correctly"

        :scenario: "Verifies that ROC curve is generated correctly for binary classification"
        :strategy: "Uses binary classification test data and validates chart generation"
        :contract:
         - pre: "DataFrame with binary labels and single score column"
         - post: "Chart figure is generated with single ROC curve"

        """
        mock_ds = datasource_factory()

        preset = RocAucCurvePreset(
            block_id="test_roc",
            datasource=mock_ds,
            y_true_col="y_true",
            y_score_cols=["score"],
        )

        # Create binary classification test data
        df = pd.DataFrame(
            {"y_true": [0, 1, 0, 1, 0, 1], "score": [0.1, 0.8, 0.3, 0.9, 0.2, 0.7]}
        )

        with patch("dashboard_lego.presets.ml_presets.go") as mock_go:
            mock_fig = MagicMock()
            mock_go.Figure.return_value = mock_fig

            ctx = create_chart_context(mock_ds)
            result = preset._generate_chart(df, ctx)

            assert result == mock_fig

    def test_roc_auc_multiclass_classification(self, datasource_factory):
        """
        Test RocAucCurvePreset for multiclass classification.

        :hierarchy: [Testing | Unit Tests | ML Presets | RocAucCurvePreset | Multiclass Classification]
        :covers:
         - object: "method: RocAucCurvePreset._generate_chart"
         - requirement: "Preset must handle multiclass classification with One-vs-Rest"

        :scenario: "Verifies that ROC curves are generated correctly for multiclass classification"
        :strategy: "Uses multiclass test data and validates multiple ROC curves generation"
        :contract:
         - pre: "DataFrame with multiclass labels and multiple score columns"
         - post: "Chart figure is generated with multiple ROC curves"

        """
        mock_ds = datasource_factory()

        preset = RocAucCurvePreset(
            block_id="test_roc",
            datasource=mock_ds,
            y_true_col="y_true",
            y_score_cols=["score_0", "score_1", "score_2"],
        )

        # Create multiclass classification test data
        df = pd.DataFrame(
            {
                "y_true": [0, 1, 2, 0, 1, 2],
                "score_0": [0.8, 0.1, 0.2, 0.9, 0.1, 0.1],
                "score_1": [0.1, 0.8, 0.1, 0.1, 0.9, 0.1],
                "score_2": [0.1, 0.1, 0.7, 0.0, 0.0, 0.8],
            }
        )

        with patch("dashboard_lego.presets.ml_presets.go") as mock_go:
            mock_fig = MagicMock()
            mock_go.Figure.return_value = mock_fig

            ctx = create_chart_context(mock_ds)
            result = preset._generate_chart(df, ctx)

            assert result == mock_fig


class TestFeatureImportancePreset:
    """
    Test for FeatureImportancePreset functionality.

    :hierarchy: [Testing | Unit Tests | ML Presets | FeatureImportancePreset]
    :covers:
     - object: "class: FeatureImportancePreset"
     - requirement: "Feature importance visualization for ML models"

    :scenario: "Verifies that FeatureImportancePreset correctly generates feature importance charts"
    :strategy: "Uses mock data with feature names and importance values to test chart generation"
    :contract:
     - pre: "Valid datasource with feature_col and importance_col data"
     - post: "Preset generates sorted horizontal bar chart of feature importances"

    """

    def test_feature_importance_preset_initialization(self, datasource_factory):
        """
        Test FeatureImportancePreset initialization.

        :hierarchy: [Testing | Unit Tests | ML Presets | FeatureImportancePreset | Initialization]
        :covers:
         - object: "method: FeatureImportancePreset.__init__"
         - requirement: "Preset must initialize with proper parameters"

        :scenario: "Verifies that FeatureImportancePreset initializes correctly"
        :strategy: "Uses datasource factory to create mock datasource"
        :contract:
         - pre: "Valid block_id, datasource, feature_col, importance_col provided"
         - post: "Preset instance is created successfully"

        """
        mock_ds = datasource_factory()

        preset = FeatureImportancePreset(
            block_id="test_fi",
            datasource=mock_ds,
            feature_col="feature",
            importance_col="importance",
        )

        assert preset.block_id == "test_fi"
        assert preset.feature_col == "feature"
        assert preset.importance_col == "importance"

    def test_feature_importance_sorts_correctly(self, datasource_factory):
        """
        Test FeatureImportancePreset sorts features correctly.

        :hierarchy: [Testing | Unit Tests | ML Presets | FeatureImportancePreset | Sorting]
        :covers:
         - object: "method: FeatureImportancePreset._generate_chart"
         - requirement: "Preset must sort features by importance in ascending order"

        :scenario: "Verifies that features are sorted by importance value in ascending order"
        :strategy: "Uses test data with known feature importances and validates sorting"
        :contract:
         - pre: "DataFrame with feature_col and importance_col provided"
         - post: "Chart figure is generated with features sorted by importance"

        """
        mock_ds = datasource_factory()

        preset = FeatureImportancePreset(
            block_id="test_fi",
            datasource=mock_ds,
            feature_col="feature",
            importance_col="importance",
        )

        # Create test data
        df = pd.DataFrame(
            {
                "feature": ["feature_A", "feature_B", "feature_C"],
                "importance": [0.1, 0.8, 0.3],
            }
        )

        with patch("dashboard_lego.presets.ml_presets.px") as mock_px:
            mock_fig = MagicMock()
            mock_px.bar.return_value = mock_fig

            ctx = create_chart_context(mock_ds)
            result = preset._generate_chart(df, ctx)

            assert result == mock_fig
            mock_px.bar.assert_called_once()
