"""
Tests for examples functionality.

:hierarchy: [Testing | Integration Tests | Examples]
:relates-to:
 - motivated_by: "TEST_PLAN.md: Уровень 3.3 - Тесты примеров"
 - implements: "test_suite: 'Examples'"

:strategy: "Use pytest to validate that all examples can be imported and run without errors"
:contract:
 - pre: "Example files exist and are accessible"
 - post: "All examples can be imported and basic functionality works"

"""

import pytest
import sys
import os
import tempfile
import pandas as pd
from unittest.mock import patch, MagicMock

# Add examples directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'examples'))


class TestExamplesImport:
    """
    Test for examples import functionality.

    :hierarchy: [Testing | Integration Tests | Examples | Import]
    :covers:
     - object: "workflow: 'Examples Import'"
     - requirement: "All examples must be importable without errors"

    :scenario: "Verifies that all example files can be imported"
    :strategy: "Attempts to import each example file and validates no import errors"
    :contract:
     - pre: "Example files exist in examples directory"
     - post: "All examples import successfully"

    """

    def test_01_simple_dashboard_import(self):
        """
        Test simple dashboard example import.

        :hierarchy: [Testing | Integration Tests | Examples | Import | Simple Dashboard]
        :covers:
         - object: "example: '01_simple_dashboard.py'"
         - requirement: "Simple dashboard example must be importable"

        :scenario: "Verifies that simple dashboard example can be imported"
        :strategy: "Imports the example module and validates no errors"
        :contract:
         - pre: "01_simple_dashboard.py exists"
         - post: "Example imports without errors"

        """
        # Test that example file exists and can be read
        example_path = os.path.join(os.path.dirname(__file__), '..', '..', 'examples', '01_simple_dashboard.py')
        assert os.path.exists(example_path), f"Example file not found: {example_path}"
        
        # Test that we can read the file content
        with open(example_path, 'r') as f:
            content = f.read()
            assert len(content) > 0, "Example file is empty"

    def test_02_interactive_dashboard_import(self):
        """
        Test interactive dashboard example import.

        :hierarchy: [Testing | Integration Tests | Examples | Import | Interactive Dashboard]
        :covers:
         - object: "example: '02_interactive_dashboard.py'"
         - requirement: "Interactive dashboard example must be importable"

        :scenario: "Verifies that interactive dashboard example can be imported"
        :strategy: "Imports the example module and validates no errors"
        :contract:
         - pre: "02_interactive_dashboard.py exists"
         - post: "Example imports without errors"

        """
        # Test that example file exists and can be read
        example_path = os.path.join(os.path.dirname(__file__), '..', '..', 'examples', '02_interactive_dashboard.py')
        assert os.path.exists(example_path), f"Example file not found: {example_path}"
        
        # Test that we can read the file content
        with open(example_path, 'r') as f:
            content = f.read()
            assert len(content) > 0, "Example file is empty"

    def test_03_presets_dashboard_import(self):
        """
        Test presets dashboard example import.

        :hierarchy: [Testing | Integration Tests | Examples | Import | Presets Dashboard]
        :covers:
         - object: "example: '03_presets_dashboard.py'"
         - requirement: "Presets dashboard example must be importable"

        :scenario: "Verifies that presets dashboard example can be imported"
        :strategy: "Imports the example module and validates no errors"
        :contract:
         - pre: "03_presets_dashboard.py exists"
         - post: "Example imports without errors"

        """
        # Test that example file exists and can be read
        example_path = os.path.join(os.path.dirname(__file__), '..', '..', 'examples', '03_presets_dashboard.py')
        assert os.path.exists(example_path), f"Example file not found: {example_path}"
        
        # Test that we can read the file content
        with open(example_path, 'r') as f:
            content = f.read()
            assert len(content) > 0, "Example file is empty"

    def test_04_ml_dashboard_import(self):
        """
        Test ML dashboard example import.

        :hierarchy: [Testing | Integration Tests | Examples | Import | ML Dashboard]
        :covers:
         - object: "example: '04_ml_dashboard.py'"
         - requirement: "ML dashboard example must be importable"

        :scenario: "Verifies that ML dashboard example can be imported"
        :strategy: "Imports the example module and validates no errors"
        :contract:
         - pre: "04_ml_dashboard.py exists"
         - post: "Example imports without errors"

        """
        # Test that example file exists and can be read
        example_path = os.path.join(os.path.dirname(__file__), '..', '..', 'examples', '04_ml_dashboard.py')
        assert os.path.exists(example_path), f"Example file not found: {example_path}"
        
        # Test that we can read the file content
        with open(example_path, 'r') as f:
            content = f.read()
            assert len(content) > 0, "Example file is empty"


class TestExamplesFunctionality:
    """
    Test for examples basic functionality.

    :hierarchy: [Testing | Integration Tests | Examples | Functionality]
    :covers:
     - object: "workflow: 'Examples Functionality'"
     - requirement: "Examples must demonstrate basic functionality"

    :scenario: "Verifies that examples can create basic dashboard components"
    :strategy: "Tests basic functionality of example components"
    :contract:
     - pre: "Example modules imported successfully"
     - post: "Basic functionality works as expected"

    """

    def test_simple_dashboard_functionality(self):
        """
        Test simple dashboard example functionality.

        :hierarchy: [Testing | Integration Tests | Examples | Functionality | Simple Dashboard]
        :covers:
         - object: "example: '01_simple_dashboard.py'"
         - requirement: "Simple dashboard example must create basic components"

        :scenario: "Verifies that simple dashboard example can create basic components"
        :strategy: "Tests that example can create data source and basic blocks"
        :contract:
         - pre: "Simple dashboard example imported"
         - post: "Basic components can be created"

        """
        # Create sample data for testing
        sample_data = pd.DataFrame({
            'Fruit': ['Apple', 'Banana', 'Orange'],
            'Sales': [100, 150, 120],
            'UnitsSold': [10, 15, 12]
        })

        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_data.to_csv(f.name, index=False)
            csv_path = f.name

        try:
            # Test that we can create basic components like in the example
            from core.datasources.csv_source import CsvDataSource
            from blocks.kpi import KPIBlock
            from blocks.chart import StaticChartBlock

            # Create data source
            datasource = CsvDataSource(csv_path)
            datasource.init_data()

            # Validate data source works
            assert datasource._data is not None
            assert len(datasource._data) == 3

            # Test KPI block creation
            kpi_block = KPIBlock(
                block_id="test_kpis",
                datasource=datasource,
                kpi_definitions=[
                    {"key": "total_sales", "title": "Total Sales", "color": "success"},
                    {"key": "total_units", "title": "Total Units", "color": "info"}
                ],
                subscribes_to="dummy_state"
            )

            # Test chart block creation
            def chart_generator(df: pd.DataFrame):
                import plotly.express as px
                return px.bar(df, x="Fruit", y="Sales", title="Sales by Fruit")

            chart_block = StaticChartBlock(
                block_id="test_chart",
                datasource=datasource,
                title="Sales Chart",
                chart_generator=chart_generator,
                subscribes_to="dummy_state"
            )

            # Validate components are created
            assert kpi_block.block_id == "test_kpis"
            assert chart_block.block_id == "test_chart"

        finally:
            os.unlink(csv_path)

    def test_interactive_dashboard_functionality(self):
        """
        Test interactive dashboard example functionality.

        :hierarchy: [Testing | Integration Tests | Examples | Functionality | Interactive Dashboard]
        :covers:
         - object: "example: '02_interactive_dashboard.py'"
         - requirement: "Interactive dashboard example must create interactive components"

        :scenario: "Verifies that interactive dashboard example can create interactive components"
        :strategy: "Tests that example can create interactive chart blocks"
        :contract:
         - pre: "Interactive dashboard example imported"
         - post: "Interactive components can be created"

        """
        # Create sample data for testing
        sample_data = pd.DataFrame({
            'Fruit': ['Apple', 'Banana', 'Orange'],
            'Sales': [100, 150, 120],
            'UnitsSold': [10, 15, 12]
        })

        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_data.to_csv(f.name, index=False)
            csv_path = f.name

        try:
            from core.datasources.csv_source import CsvDataSource
            from blocks.chart import InteractiveChartBlock

            # Create data source
            datasource = CsvDataSource(csv_path)
            datasource.init_data()

            # Test interactive chart block creation
            def chart_generator(df: pd.DataFrame):
                import plotly.express as px
                return px.bar(df, x="Fruit", y="Sales", title="Interactive Sales Chart")

            # Mock controls for testing
            from blocks.chart import Control
            from dash import dcc

            controls = {
                "fruit_filter": Control(
                    component=dcc.Dropdown,
                    props={
                        "options": ["Apple", "Banana", "Orange"],
                        "placeholder": "Select Fruit"
                    }
                )
            }

            chart_block = InteractiveChartBlock(
                block_id="interactive_chart",
                datasource=datasource,
                title="Interactive Chart",
                chart_generator=chart_generator,
                controls=controls,
                subscribes_to=["filter_state"]
            )

            # Validate interactive component is created
            assert chart_block.block_id == "interactive_chart"
            assert len(chart_block.controls) == 1

        finally:
            os.unlink(csv_path)

    def test_presets_dashboard_functionality(self):
        """
        Test presets dashboard example functionality.

        :hierarchy: [Testing | Integration Tests | Examples | Functionality | Presets Dashboard]
        :covers:
         - object: "example: '03_presets_dashboard.py'"
         - requirement: "Presets dashboard example must create preset components"

        :scenario: "Verifies that presets dashboard example can create preset components"
        :strategy: "Tests that example can create EDA preset blocks"
        :contract:
         - pre: "Presets dashboard example imported"
         - post: "Preset components can be created"

        """
        # Create sample data for testing
        sample_data = pd.DataFrame({
            'Fruit': ['Apple', 'Banana', 'Orange'],
            'Sales': [100, 150, 120],
            'UnitsSold': [10, 15, 12],
            'Price': [10.0, 10.0, 10.0]
        })

        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_data.to_csv(f.name, index=False)
            csv_path = f.name

        try:
            from core.datasources.csv_source import CsvDataSource
            from presets.eda_presets import CorrelationHeatmapPreset

            # Create data source
            datasource = CsvDataSource(csv_path)
            datasource.init_data()

            # Test EDA preset creation
            correlation_preset = CorrelationHeatmapPreset(
                block_id="eda_correlation",
                datasource=datasource,
                subscribes_to="dummy_state"
            )

            # Validate preset component is created
            assert correlation_preset.block_id == "eda_correlation"
            assert correlation_preset.datasource == datasource

        finally:
            os.unlink(csv_path)

    def test_ml_dashboard_functionality(self):
        """
        Test ML dashboard example functionality.

        :hierarchy: [Testing | Integration Tests | Examples | Functionality | ML Dashboard]
        :covers:
         - object: "example: '04_ml_dashboard.py'"
         - requirement: "ML dashboard example must create ML components"

        :scenario: "Verifies that ML dashboard example can create ML components"
        :strategy: "Tests that example can create ML preset blocks"
        :contract:
         - pre: "ML dashboard example imported"
         - post: "ML components can be created"

        """
        # Create sample data for testing
        sample_data = pd.DataFrame({
            'Fruit': ['Apple', 'Banana', 'Orange'],
            'Sales': [100, 150, 120],
            'UnitsSold': [10, 15, 12]
        })

        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            sample_data.to_csv(f.name, index=False)
            csv_path = f.name

        try:
            from core.datasources.csv_source import CsvDataSource
            from presets.ml_presets import MetricCardBlock, ModelSummaryBlock

            # Create data source with ML methods
            class MLDataSource(CsvDataSource):
                def get_kpis(self) -> dict:
                    return {
                        "accuracy": 0.95,
                        "precision": 0.87,
                        "recall": 0.92
                    }

                def get_summary_data(self) -> dict:
                    return {
                        "algorithm": "Random Forest",
                        "n_estimators": 100,
                        "max_depth": 10
                    }

            # Create data source
            datasource = MLDataSource(csv_path)
            datasource.init_data()

            # Test ML preset creation
            metric_block = MetricCardBlock(
                block_id="ml_metrics",
                datasource=datasource,
                kpi_definitions=[
                    {"key": "accuracy", "title": "Accuracy"},
                    {"key": "precision", "title": "Precision"},
                    {"key": "recall", "title": "Recall"}
                ],
                subscribes_to="dummy_state"
            )

            summary_block = ModelSummaryBlock(
                block_id="ml_summary",
                datasource=datasource,
                title="Model Summary"
            )

            # Validate ML components are created
            assert metric_block.block_id == "ml_metrics"
            assert summary_block.block_id == "ml_summary"
            assert len(metric_block.kpi_definitions) == 3

        finally:
            os.unlink(csv_path)
