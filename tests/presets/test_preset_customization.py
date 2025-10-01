"""
Tests for preset customization parameters.

:hierarchy: [Tests | Presets | Customization]
:covers:
 - object: "EDA and ML presets with customization parameters"
 - requirement: "Phase 2: All presets should support customization parameters"

:scenario: "Verifies that all EDA and ML presets accept and pass through customization parameters."
:strategy: "Uses pytest to test preset initialization with custom parameters."
:contract:
 - pre: "Presets are initialized with customization parameters"
 - post: "Presets accept parameters without errors and pass them to base blocks"

"""

from unittest.mock import Mock

import pytest

from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.presets.eda_presets import (
    BoxPlotPreset,
    CorrelationHeatmapPreset,
    GroupedHistogramPreset,
    MissingValuesPreset,
)
from dashboard_lego.presets.ml_presets import (
    ConfusionMatrixPreset,
    FeatureImportancePreset,
    MetricCardBlock,
    ModelSummaryBlock,
    RocAucCurvePreset,
)


@pytest.fixture
def mock_datasource():
    """Mock datasource for testing presets."""
    mock = Mock(spec=BaseDataSource)
    mock.get_processed_data.return_value = Mock()
    mock.get_kpis.return_value = {"accuracy": 0.95, "precision": 0.92}
    # Add get_summary_data as an additional method (not part of BaseDataSource)
    mock.get_summary_data = Mock(return_value={"model": "RandomForest", "score": 0.95})
    return mock


class TestEDAPresetCustomization:
    """Test EDA presets with customization parameters."""

    def test_correlation_heatmap_customization(self, mock_datasource):
        """Test CorrelationHeatmapPreset accepts customization parameters."""
        preset = CorrelationHeatmapPreset(
            block_id="test",
            datasource=mock_datasource,
            subscribes_to="state",
            title="Custom Title",
            card_style={"backgroundColor": "lightblue"},
            card_className="custom-card",
            title_style={"color": "red"},
            title_className="custom-title",
            loading_type="dot",
            graph_config={"displayModeBar": False},
            graph_style={"height": "400px"},
            figure_layout={"title": {"text": "Custom Figure Title"}},
        )

        assert preset.title == "Custom Title"
        # Verify the preset was created without errors
        assert preset.block_id == "test"

    def test_grouped_histogram_customization(self, mock_datasource):
        """Test GroupedHistogramPreset accepts customization parameters."""
        # Mock dataframe with numerical columns
        mock_df = Mock()
        mock_df.select_dtypes.return_value.columns.tolist.return_value = [
            "col1",
            "col2",
        ]
        mock_datasource.get_processed_data.return_value = mock_df

        preset = GroupedHistogramPreset(
            block_id="test",
            datasource=mock_datasource,
            title="Custom Histogram",
            card_style={"backgroundColor": "lightgreen"},
            controls_row_style={"marginBottom": "20px"},
            figure_layout={"title": {"text": "Custom Histogram Title"}},
        )

        assert preset.title == "Custom Histogram"
        assert preset.block_id == "test"

    def test_missing_values_customization(self, mock_datasource):
        """Test MissingValuesPreset accepts customization parameters."""
        preset = MissingValuesPreset(
            block_id="test",
            datasource=mock_datasource,
            subscribes_to="state",
            title="Custom Missing Values",
            card_className="missing-values-card",
            graph_style={"height": "300px"},
        )

        assert preset.title == "Custom Missing Values"
        assert preset.block_id == "test"

    def test_box_plot_customization(self, mock_datasource):
        """Test BoxPlotPreset accepts customization parameters."""
        # Mock dataframe with both numerical and categorical columns
        mock_df = Mock()
        mock_df.select_dtypes.side_effect = [
            Mock(columns=Mock(tolist=Mock(return_value=["num_col"]))),
            Mock(columns=Mock(tolist=Mock(return_value=["cat_col"]))),
        ]
        mock_datasource.get_processed_data.return_value = mock_df

        preset = BoxPlotPreset(
            block_id="test",
            datasource=mock_datasource,
            title="Custom Box Plot",
            card_style={"backgroundColor": "lightyellow"},
            controls_row_className="box-plot-controls",
            figure_layout={"title": {"text": "Custom Box Plot Title"}},
        )

        assert preset.title == "Custom Box Plot"
        assert preset.block_id == "test"


class TestMLPresetCustomization:
    """Test ML presets with customization parameters."""

    def test_metric_card_customization(self, mock_datasource):
        """Test MetricCardBlock accepts customization parameters."""
        kpi_definitions = [{"key": "accuracy", "label": "Accuracy"}]

        preset = MetricCardBlock(
            block_id="test",
            datasource=mock_datasource,
            kpi_definitions=kpi_definitions,
            subscribes_to="state",
            title="Custom Metrics",
            container_style={"backgroundColor": "lightblue"},
            kpi_card_style={"border": "2px solid blue"},
            value_style={"fontSize": "24px"},
            title_style={"color": "darkblue"},
        )

        assert preset.title == "Custom Metrics"
        assert preset.block_id == "test"

    def test_model_summary_customization(self, mock_datasource):
        """Test ModelSummaryBlock accepts customization parameters."""
        preset = ModelSummaryBlock(
            block_id="test",
            datasource=mock_datasource,
            title="Custom Model Summary",
            card_style={"backgroundColor": "lightgreen"},
            card_className="model-summary-card",
            title_style={"color": "darkgreen"},
            content_style={"fontSize": "14px"},
        )

        assert preset.title == "Custom Model Summary"
        assert preset.block_id == "test"

    def test_confusion_matrix_customization(self, mock_datasource):
        """Test ConfusionMatrixPreset accepts customization parameters."""
        preset = ConfusionMatrixPreset(
            block_id="test",
            datasource=mock_datasource,
            y_true_col="true",
            y_pred_col="pred",
            title="Custom Confusion Matrix",
            card_style={"backgroundColor": "lightcoral"},
            figure_layout={"title": {"text": "Custom Confusion Matrix Title"}},
        )

        assert preset.block_id == "test"

    def test_roc_auc_curve_customization(self, mock_datasource):
        """Test RocAucCurvePreset accepts customization parameters."""
        preset = RocAucCurvePreset(
            block_id="test",
            datasource=mock_datasource,
            y_true_col="true",
            y_score_cols=["score1", "score2"],
            title="Custom ROC Curve",
            card_className="roc-curve-card",
            graph_config={"displayModeBar": True},
        )

        assert preset.block_id == "test"

    def test_feature_importance_customization(self, mock_datasource):
        """Test FeatureImportancePreset accepts customization parameters."""
        preset = FeatureImportancePreset(
            block_id="test",
            datasource=mock_datasource,
            feature_col="feature",
            importance_col="importance",
            title="Custom Feature Importance",
            card_style={"backgroundColor": "lightyellow"},
            figure_layout={"title": {"text": "Custom Feature Importance Title"}},
        )

        assert preset.block_id == "test"
