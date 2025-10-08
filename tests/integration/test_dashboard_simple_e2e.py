"""
Simplified End-to-End tests for dashboard functionality.

:hierarchy: [Testing | Integration Tests | Simple E2E]
:relates-to:
 - motivated_by: "Architectural Conclusion: End-to-end tests validate
   complete dashboard functionality and user workflows"
 - implements: "test_suite: 'SimpleDashboardE2E'"

:strategy: "Use pytest with real data but simplified state management"
:contract:
 - pre: "Test environment is set up with sample data and fixtures"
 - post: "All simplified E2E tests pass and validate basic dashboard workflows"

"""

import os
import tempfile
from unittest.mock import MagicMock, patch

import pandas as pd
import pytest

from dashboard_lego.blocks.chart import StaticChartBlock
from dashboard_lego.blocks.kpi import KPIBlock
from dashboard_lego.blocks.text import TextBlock
from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.core.page import DashboardPage
from dashboard_lego.presets.eda_presets import CorrelationHeatmapPreset
from dashboard_lego.presets.ml_presets import MetricCardBlock, ModelSummaryBlock


class TestSimpleDashboardE2E:
    """
    Test for simple dashboard creation and functionality.

    :hierarchy: [Testing | Integration Tests | Simple E2E | Dashboard Creation]
    :covers:
     - object: "workflow: 'Simple Dashboard Creation'"
     - requirement: "Basic dashboard workflow from data source to rendering"

    :scenario: "Verifies that a simple dashboard can be created and rendered"
    :strategy: "Uses real data source and dashboard components with minimal state management"
    :contract:
     - pre: "Valid data source and dashboard components provided"
     - post: "Dashboard is created and basic structure is validated"

    """

    def test_simple_dashboard_creation(self, sample_csv_data):
        """
        Test simple dashboard creation workflow.

        :hierarchy: [Testing | Integration Tests | Simple E2E | Dashboard Creation | Basic]
        :covers:
         - object: "workflow: 'Dashboard Creation'"
         - requirement: "Dashboard must be created with basic components"

        :scenario: "Verifies that a simple dashboard with basic components can be created"
        :strategy: "Creates dashboard with real data source and validates basic structure"
        :contract:
         - pre: "Sample CSV data and dashboard components available"
         - post: "Dashboard is created with proper basic structure"

        """
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            sample_csv_data.to_csv(f.name, index=False)
            csv_path = f.name

        try:
            # Create custom data source
            class TestDataSource(BaseDataSource):
                def _load_raw_data(self, params: dict) -> pd.DataFrame:
                    return pd.read_csv(csv_path)

                def get_kpis(self) -> dict:
                    if self._data is None:
                        return {}
                    return {
                        "total_sales": self._data["Sales"].sum(),
                        "total_units": self._data["UnitsSold"].sum(),
                    }

                def get_filter_options(self, filter_name: str) -> list:
                    return []

                def get_summary(self) -> str:
                    return "Test data source"

            # Initialize data source
            datasource = TestDataSource()
            datasource.init_data()

            # Validate data source works
            kpis = datasource.get_kpis()
            assert "total_sales" in kpis
            assert "total_units" in kpis
            assert kpis["total_sales"] > 0
            assert kpis["total_units"] > 0

            # Create dashboard blocks with dummy state
            kpi_block = KPIBlock(
                block_id="test_kpis",
                datasource=datasource,
                kpi_definitions=[
                    {"key": "total_sales", "title": "Total Sales", "color": "success"},
                    {"key": "total_units", "title": "Total Units", "color": "info"},
                ],
                subscribes_to="dummy_state",
            )

            def chart_generator(df: pd.DataFrame):
                import plotly.express as px

                return px.bar(df, x="Fruit", y="Sales", title="Sales by Fruit")

            chart_block = StaticChartBlock(
                block_id="test_chart",
                datasource=datasource,
                title="Sales Chart",
                chart_generator=chart_generator,
                subscribes_to="dummy_state",
            )

            # Validate blocks are created correctly
            assert kpi_block.block_id == "test_kpis"
            assert chart_block.block_id == "test_chart"
            assert len(kpi_block.kpi_definitions) == 2

        finally:
            # Clean up temporary file
            os.unlink(csv_path)

    def test_dashboard_with_real_csv_data(self, sample_csv_data):
        """
        Test dashboard with real CSV data processing.

        :hierarchy: [Testing | Integration Tests | Simple E2E | Data Processing]
        :covers:
         - object: "workflow: 'CSV Data Processing'"
         - requirement: "Dashboard must process real CSV data correctly"

        :scenario: "Verifies that dashboard correctly processes real CSV data"
        :strategy: "Uses real CSV data and validates data processing pipeline"
        :contract:
         - pre: "Real CSV data with known structure provided"
         - post: "Dashboard processes data and displays correct values"

        """
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            sample_csv_data.to_csv(f.name, index=False)
            csv_path = f.name

        try:
            # Create data source
            class CSVDataSource(BaseDataSource):
                def _load_raw_data(self, params: dict) -> pd.DataFrame:
                    return pd.read_csv(csv_path)

                def get_kpis(self) -> dict:
                    if self._data is None:
                        return {}
                    return {
                        "total_sales": float(self._data["Sales"].sum()),
                        "total_units": int(self._data["UnitsSold"].sum()),
                    }

                def get_filter_options(self, filter_name: str) -> list:
                    return []

                def get_summary(self) -> str:
                    return f"CSV with {len(self._data)} rows"

            # Initialize and test data source
            datasource = CSVDataSource()
            datasource.init_data()

            # Validate data processing
            kpis = datasource.get_kpis()
            assert "total_sales" in kpis
            assert "total_units" in kpis
            assert isinstance(kpis["total_sales"], float)
            assert isinstance(kpis["total_units"], int)

            # Test that data is loaded correctly
            assert len(datasource._data) == len(sample_csv_data)
            assert list(datasource._data.columns) == list(sample_csv_data.columns)

        finally:
            os.unlink(csv_path)

    def test_dashboard_with_multiple_blocks(self, sample_csv_data):
        """
        Test dashboard with multiple different blocks.

        :hierarchy: [Testing | Integration Tests | Simple E2E | Multiple Blocks]
        :covers:
         - object: "workflow: 'Multiple Blocks Integration'"
         - requirement: "Dashboard must integrate multiple block types"

        :scenario: "Verifies that dashboard can handle multiple different block types"
        :strategy: "Creates dashboard with KPI, chart, and text blocks"
        :contract:
         - pre: "Various block types and data source available"
         - post: "Dashboard can create all block types correctly"

        """
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            sample_csv_data.to_csv(f.name, index=False)
            csv_path = f.name

        try:
            # Create comprehensive data source
            class MultiBlockDataSource(BaseDataSource):
                def _load_raw_data(self, params: dict) -> pd.DataFrame:
                    return pd.read_csv(csv_path)

                def get_kpis(self) -> dict:
                    if self._data is None:
                        return {}
                    return {
                        "total_sales": float(self._data["Sales"].sum()),
                        "total_units": int(self._data["UnitsSold"].sum()),
                        "avg_price": float(self._data["Sales"].mean()),
                    }

                def get_filter_options(self, filter_name: str) -> list:
                    return []

                def get_summary(self) -> str:
                    return f"Multi-block data with {len(self._data)} rows"

            # Initialize data source
            datasource = MultiBlockDataSource()
            datasource.init_data()

            # Create various blocks
            kpi_block = KPIBlock(
                block_id="multi_kpis",
                datasource=datasource,
                kpi_definitions=[
                    {"key": "total_sales", "title": "Total Sales", "color": "success"},
                    {"key": "total_units", "title": "Total Units", "color": "info"},
                    {"key": "avg_price", "title": "Average Price", "color": "warning"},
                ],
                subscribes_to="dummy_state",
            )

            def chart_generator(df: pd.DataFrame):
                import plotly.express as px

                return px.bar(df, x="Fruit", y="Sales", title="Sales Analysis")

            chart_block = StaticChartBlock(
                block_id="multi_chart",
                datasource=datasource,
                title="Sales Chart",
                chart_generator=chart_generator,
                subscribes_to="dummy_state",
            )

            def text_generator(df: pd.DataFrame):
                return "This is a comprehensive dashboard with multiple block types."

            text_block = TextBlock(
                block_id="multi_text",
                datasource=datasource,
                subscribes_to="dummy_state",
                content_generator=text_generator,
                title="Dashboard Info",
            )

            # Validate all blocks are properly created
            assert kpi_block.block_id == "multi_kpis"
            assert chart_block.block_id == "multi_chart"
            assert text_block.block_id == "multi_text"
            assert len(kpi_block.kpi_definitions) == 3
            assert chart_block.title == "Sales Chart"
            assert text_block.title == "Dashboard Info"

        finally:
            os.unlink(csv_path)


class TestPresetDashboardE2E:
    """
    Test for preset dashboard functionality.

    :hierarchy: [Testing | Integration Tests | Simple E2E | Preset Dashboard]
    :covers:
     - object: "workflow: 'Preset Dashboard'"
     - requirement: "Dashboard with EDA and ML presets"

    :scenario: "Verifies that dashboard with presets works"
    :strategy: "Uses EDA and ML presets to test preset functionality"
    :contract:
     - pre: "Preset components and data available"
     - post: "Preset dashboard components are created correctly"

    """

    def test_eda_preset_dashboard(self, sample_csv_data):
        """
        Test dashboard with EDA presets.

        :hierarchy: [Testing | Integration Tests | Simple E2E | Preset Dashboard | EDA Presets]
        :covers:
         - object: "workflow: 'EDA Preset Dashboard'"
         - requirement: "Dashboard must work with EDA presets"

        :scenario: "Verifies that EDA presets work in dashboard context"
        :strategy: "Creates dashboard with EDA presets and validates functionality"
        :contract:
         - pre: "EDA presets and appropriate data available"
         - post: "EDA preset components are created correctly"

        """
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            sample_csv_data.to_csv(f.name, index=False)
            csv_path = f.name

        try:
            # Create data source for EDA
            class EDADataSource(BaseDataSource):
                def _load_raw_data(self, params: dict) -> pd.DataFrame:
                    return pd.read_csv(csv_path)

                def get_kpis(self) -> dict:
                    return {}

                def get_filter_options(self, filter_name: str) -> list:
                    return []

                def get_summary(self) -> str:
                    return "EDA test data source"

            # Initialize data source
            datasource = EDADataSource()
            datasource.init_data()

            # Create EDA preset
            correlation_preset = CorrelationHeatmapPreset(
                block_id="eda_correlation",
                datasource=datasource,
                subscribes_to="dummy_state",
            )

            # Validate EDA preset
            assert correlation_preset.block_id == "eda_correlation"
            assert correlation_preset.datasource == datasource

        finally:
            os.unlink(csv_path)

    def test_ml_preset_dashboard(self, sample_csv_data):
        """
        Test dashboard with ML presets.

        :hierarchy: [Testing | Integration Tests | Simple E2E | Preset Dashboard | ML Presets]
        :covers:
         - object: "workflow: 'ML Preset Dashboard'"
         - requirement: "Dashboard must work with ML presets"

        :scenario: "Verifies that ML presets work in dashboard context"
        :strategy: "Creates dashboard with ML presets and validates functionality"
        :contract:
         - pre: "ML presets and appropriate data available"
         - post: "ML preset components are created correctly"

        """
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            sample_csv_data.to_csv(f.name, index=False)
            csv_path = f.name

        try:
            # Create data source for ML
            class MLDataSource(BaseDataSource):
                def _load_raw_data(self, params: dict) -> pd.DataFrame:
                    return pd.read_csv(csv_path)

                def get_kpis(self) -> dict:
                    return {"accuracy": 0.95, "precision": 0.87, "recall": 0.92}

                def get_filter_options(self, filter_name: str) -> list:
                    return []

                def get_summary(self) -> str:
                    return "ML test data source"

                def get_summary_data(self) -> dict:
                    return {
                        "algorithm": "Random Forest",
                        "n_estimators": 100,
                        "max_depth": 10,
                    }

            # Initialize data source
            datasource = MLDataSource()
            datasource.init_data()

            # Create ML presets
            metric_block = MetricCardBlock(
                block_id="ml_metrics",
                datasource=datasource,
                kpi_definitions=[
                    {"key": "accuracy", "title": "Accuracy"},
                    {"key": "precision", "title": "Precision"},
                    {"key": "recall", "title": "Recall"},
                ],
                subscribes_to="dummy_state",
            )

            summary_block = ModelSummaryBlock(
                block_id="ml_summary", datasource=datasource, title="Model Summary"
            )

            # Validate ML presets
            assert metric_block.block_id == "ml_metrics"
            assert summary_block.block_id == "ml_summary"
            assert len(metric_block.kpi_definitions) == 3
            assert summary_block.title == "Model Summary"

        finally:
            os.unlink(csv_path)
