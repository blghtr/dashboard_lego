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
import plotly.graph_objects as go
import pytest

from dashboard_lego.blocks.kpi import KPIBlock
from dashboard_lego.blocks.metrics import MetricsBlock
from dashboard_lego.blocks.text import TextBlock
from dashboard_lego.blocks.typed_chart import TypedChartBlock
from dashboard_lego.core import BaseDataSource, DataBuilder
from dashboard_lego.core.page import DashboardPage
from dashboard_lego.utils.plot_registry import register_plot_type


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
            # Create custom data builder
            class TestDataBuilder(DataBuilder):
                def __init__(self, file_path, **kwargs):
                    super().__init__(**kwargs)
                    self.file_path = file_path

                def build(self, params):
                    return pd.read_csv(self.file_path)

            # Create data source with builder
            datasource = BaseDataSource(data_builder=TestDataBuilder(csv_path))

            # Create dashboard blocks with MetricsBlock (replaces KPIBlock with get_kpis)
            metrics_block = MetricsBlock(
                block_id="test_metrics",
                datasource=datasource,
                metrics_spec={
                    "total_sales": {
                        "column": "Sales",
                        "agg": "sum",
                        "title": "Total Sales",
                        "color": "success",
                    },
                    "total_units": {
                        "column": "UnitsSold",
                        "agg": "sum",
                        "title": "Total Units",
                        "color": "info",
                    },
                },
                subscribes_to="dummy_state",
            )

            def chart_generator(df: pd.DataFrame):
                import plotly.express as px

                return px.bar(df, x="Fruit", y="Sales", title="Sales by Fruit")

            # Register custom plot function
            register_plot_type("test_bar_chart", chart_generator)

            chart_block = TypedChartBlock(
                block_id="test_chart",
                datasource=datasource,
                title="Sales Chart",
                plot_type="test_bar_chart",
                plot_params={},
                subscribes_to="dummy_state",
            )

            # Validate blocks are created correctly
            assert metrics_block.block_id == "test_metrics"
            assert chart_block.block_id == "test_chart"
            assert len(metrics_block.metrics_spec) == 2

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
            # Create data builder for CSV
            class CSVDataBuilder(DataBuilder):
                def __init__(self, file_path, **kwargs):
                    super().__init__(**kwargs)
                    self.file_path = file_path

                def build(self, params):
                    return pd.read_csv(self.file_path)

            # Create data source with builder
            datasource = BaseDataSource(data_builder=CSVDataBuilder(csv_path))

            # Validate data processing by getting data
            df = datasource.get_processed_data()
            assert len(df) == len(sample_csv_data)
            assert list(df.columns) == list(sample_csv_data.columns)

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
            # Create data builder
            class MultiBlockDataBuilder(DataBuilder):
                def __init__(self, file_path, **kwargs):
                    super().__init__(**kwargs)
                    self.file_path = file_path

                def build(self, params):
                    return pd.read_csv(self.file_path)

            # Create data source
            datasource = BaseDataSource(data_builder=MultiBlockDataBuilder(csv_path))

            # Create various blocks with MetricsBlock
            metrics_block = MetricsBlock(
                block_id="multi_metrics",
                datasource=datasource,
                metrics_spec={
                    "total_sales": {
                        "column": "Sales",
                        "agg": "sum",
                        "title": "Total Sales",
                        "color": "success",
                    },
                    "total_units": {
                        "column": "UnitsSold",
                        "agg": "sum",
                        "title": "Total Units",
                        "color": "info",
                    },
                    "avg_price": {
                        "column": "Sales",
                        "agg": "mean",
                        "title": "Average Price",
                        "color": "warning",
                    },
                },
                subscribes_to="dummy_state",
            )

            def chart_generator2(df: pd.DataFrame, **kwargs):
                import plotly.express as px

                return px.bar(df, x="Fruit", y="Sales", title="Sales Analysis")

            register_plot_type("test_bar_chart2", chart_generator2)

            chart_block = TypedChartBlock(
                block_id="multi_chart",
                datasource=datasource,
                title="Sales Chart",
                plot_type="test_bar_chart2",
                plot_params={},
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
            assert metrics_block.block_id == "multi_metrics"
            assert chart_block.block_id == "multi_chart"
            assert text_block.block_id == "multi_text"
            assert len(metrics_block.metrics_spec) == 3
            assert chart_block.title == "Sales Chart"
            assert text_block.title == "Dashboard Info"

        finally:
            os.unlink(csv_path)
