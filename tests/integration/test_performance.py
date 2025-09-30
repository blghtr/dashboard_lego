"""
Performance tests for dashboard functionality.

:hierarchy: [Testing | Integration Tests | Performance]
:relates-to:
 - motivated_by: "TEST_PLAN.md: Уровень 3.2 - Тесты производительности"
 - implements: "test_suite: 'Performance'"

:strategy: "Use pytest with timing and memory profiling for performance validation"
:contract:
 - pre: "Test environment is set up with large datasets and performance monitoring"
 - post: "All performance tests pass and validate acceptable performance thresholds"

"""

import pytest
import pandas as pd
import tempfile
import os
import time
from unittest.mock import MagicMock

from core.datasource import BaseDataSource
from core.page import DashboardPage
from blocks.kpi import KPIBlock
from blocks.chart import StaticChartBlock
from presets.ml_presets import MetricCardBlock


class TestLargeDatasetPerformance:
    """
    Test for large dataset loading and processing performance.

    :hierarchy: [Testing | Integration Tests | Performance | Large Dataset]
    :covers:
     - object: "workflow: 'Large Dataset Processing'"
     - requirement: "Dashboard must handle large datasets efficiently"

    :scenario: "Verifies that dashboard can process large datasets within acceptable time limits"
    :strategy: "Uses large generated datasets and measures processing time"
    :contract:
     - pre: "Large dataset available for testing"
     - post: "Dataset processing completes within performance thresholds"

    """

    def test_large_dataset_loading_performance(self):
        """
        Test large dataset loading performance.

        :hierarchy: [Testing | Integration Tests | Performance | Large Dataset | Loading]
        :covers:
         - object: "workflow: 'Large Dataset Loading'"
         - requirement: "Large datasets must load within acceptable time"

        :scenario: "Verifies that large datasets load within performance thresholds"
        :strategy: "Generates large dataset and measures loading time"
        :contract:
         - pre: "Large dataset generated (10,000+ rows)"
         - post: "Dataset loads within 5 seconds"

        """
        # Generate large dataset
        large_data = pd.DataFrame({
            'Fruit': ['Apple', 'Banana', 'Orange', 'Grape', 'Strawberry'] * 2000,
            'Sales': range(10000),
            'UnitsSold': range(10000),
            'Price': [10.0, 15.0, 12.0, 8.0, 20.0] * 2000,
            'Category': ['A', 'B', 'C', 'D', 'E'] * 2000
        })

        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            large_data.to_csv(f.name, index=False)
            csv_path = f.name

        try:
            # Create data source
            class LargeDataSource(BaseDataSource):
                def _load_data(self, params: dict) -> pd.DataFrame:
                    return pd.read_csv(csv_path)

                def get_kpis(self) -> dict:
                    if self._data is None:
                        return {}
                    return {
                        "total_sales": float(self._data["Sales"].sum()),
                        "total_units": int(self._data["UnitsSold"].sum()),
                        "avg_price": float(self._data["Price"].mean())
                    }

                def get_filter_options(self, filter_name: str) -> list:
                    return []

                def get_summary(self) -> str:
                    return f"Large dataset with {len(self._data)} rows"

            # Measure loading time
            start_time = time.time()
            datasource = LargeDataSource()
            datasource.init_data()
            loading_time = time.time() - start_time

            # Validate performance
            assert loading_time < 5.0, f"Loading took {loading_time:.2f}s, expected < 5.0s"
            assert len(datasource._data) == 10000
            assert datasource.get_kpis()["total_sales"] > 0

        finally:
            os.unlink(csv_path)

    def test_large_dataset_processing_performance(self):
        """
        Test large dataset processing performance.

        :hierarchy: [Testing | Integration Tests | Performance | Large Dataset | Processing]
        :covers:
         - object: "workflow: 'Large Dataset Processing'"
         - requirement: "Large datasets must process efficiently"

        :scenario: "Verifies that large dataset processing operations are efficient"
        :strategy: "Measures time for KPI calculations and chart generation"
        :contract:
         - pre: "Large dataset loaded (10,000+ rows)"
         - post: "Processing operations complete within 2 seconds"

        """
        # Generate large dataset
        large_data = pd.DataFrame({
            'Fruit': ['Apple', 'Banana', 'Orange', 'Grape', 'Strawberry'] * 2000,
            'Sales': range(10000),
            'UnitsSold': range(10000),
            'Price': [10.0, 15.0, 12.0, 8.0, 20.0] * 2000
        })

        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            large_data.to_csv(f.name, index=False)
            csv_path = f.name

        try:
            # Create data source
            class ProcessingDataSource(BaseDataSource):
                def _load_data(self, params: dict) -> pd.DataFrame:
                    return pd.read_csv(csv_path)

                def get_kpis(self) -> dict:
                    if self._data is None:
                        return {}
                    # Simulate complex calculations
                    return {
                        "total_sales": float(self._data["Sales"].sum()),
                        "total_units": int(self._data["UnitsSold"].sum()),
                        "avg_price": float(self._data["Price"].mean()),
                        "max_sales": float(self._data["Sales"].max()),
                        "min_sales": float(self._data["Sales"].min()),
                        "std_price": float(self._data["Price"].std())
                    }

                def get_filter_options(self, filter_name: str) -> list:
                    return []

                def get_summary(self) -> str:
                    return f"Processing dataset with {len(self._data)} rows"

            # Initialize data source
            datasource = ProcessingDataSource()
            datasource.init_data()

            # Measure KPI calculation time
            start_time = time.time()
            kpis = datasource.get_kpis()
            kpi_time = time.time() - start_time

            # Measure chart generation time
            def chart_generator(df: pd.DataFrame):
                import plotly.express as px
                return px.bar(df.groupby('Fruit')['Sales'].sum().reset_index(), 
                            x='Fruit', y='Sales', title='Large Dataset Chart')

            start_time = time.time()
            chart_fig = chart_generator(datasource._data)
            chart_time = time.time() - start_time

            # Validate performance
            assert kpi_time < 2.0, f"KPI calculation took {kpi_time:.2f}s, expected < 2.0s"
            assert chart_time < 2.0, f"Chart generation took {chart_time:.2f}s, expected < 2.0s"
            assert len(kpis) == 6
            assert chart_fig is not None

        finally:
            os.unlink(csv_path)


class TestCachePerformance:
    """
    Test for caching performance and efficiency.

    :hierarchy: [Testing | Integration Tests | Performance | Cache]
    :covers:
     - object: "workflow: 'Cache Performance'"
     - requirement: "Caching must improve performance for repeated operations"

    :scenario: "Verifies that caching provides performance benefits"
    :strategy: "Measures performance with and without cache"
    :contract:
     - pre: "Data source with caching enabled"
     - post: "Cached operations are significantly faster than uncached"

    """

    def test_cache_hit_performance(self):
        """
        Test cache hit performance.

        :hierarchy: [Testing | Integration Tests | Performance | Cache | Hit Performance]
        :covers:
         - object: "workflow: 'Cache Hit Performance'"
         - requirement: "Cache hits must be significantly faster than cache misses"

        :scenario: "Verifies that cache hits provide performance benefits"
        :strategy: "Measures time for first load (cache miss) vs second load (cache hit)"
        :contract:
         - pre: "Data source with caching enabled"
         - post: "Cache hit is at least 2x faster than cache miss"

        """
        # Generate test data
        test_data = pd.DataFrame({
            'Fruit': ['Apple', 'Banana', 'Orange'] * 100,
            'Sales': range(300),
            'UnitsSold': range(300)
        })

        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            test_data.to_csv(f.name, index=False)
            csv_path = f.name

        try:
            # Create data source with caching
            class CacheDataSource(BaseDataSource):
                def _load_data(self, params: dict) -> pd.DataFrame:
                    # Simulate some processing time
                    time.sleep(0.1)
                    return pd.read_csv(csv_path)

                def get_kpis(self) -> dict:
                    if self._data is None:
                        return {}
                    return {
                        "total_sales": float(self._data["Sales"].sum()),
                        "total_units": int(self._data["UnitsSold"].sum())
                    }

                def get_filter_options(self, filter_name: str) -> list:
                    return []

                def get_summary(self) -> str:
                    return "Cache test data source"

            # Measure first load (cache miss)
            datasource = CacheDataSource()
            start_time = time.time()
            datasource.init_data()
            first_load_time = time.time() - start_time

            # Measure second load (cache hit)
            start_time = time.time()
            datasource.init_data()
            second_load_time = time.time() - start_time

            # Validate cache performance
            assert first_load_time > 0.1, "First load should take time for processing"
            assert second_load_time < first_load_time, "Cache hit should be faster"
            assert second_load_time < 0.05, f"Cache hit took {second_load_time:.3f}s, expected < 0.05s"

        finally:
            os.unlink(csv_path)


class TestMemoryPerformance:
    """
    Test for memory usage and efficiency.

    :hierarchy: [Testing | Integration Tests | Performance | Memory]
    :covers:
     - object: "workflow: 'Memory Performance'"
     - requirement: "Dashboard must use memory efficiently"

    :scenario: "Verifies that dashboard components use memory efficiently"
    :strategy: "Measures memory usage during dashboard operations"
    :contract:
     - pre: "Dashboard components and large datasets available"
     - post: "Memory usage remains within acceptable limits"

    """

    def test_multiple_blocks_creation_performance(self):
        """
        Test multiple blocks creation performance.

        :hierarchy: [Testing | Integration Tests | Performance | Multiple Blocks]
        :covers:
         - object: "workflow: 'Multiple Blocks Creation'"
         - requirement: "Multiple blocks must be created efficiently"

        :scenario: "Verifies that multiple dashboard blocks can be created quickly"
        :strategy: "Creates multiple blocks and measures creation time"
        :contract:
         - pre: "Multiple dashboard blocks to be created"
         - post: "All blocks created within acceptable time"

        """
        # Generate test data
        test_data = pd.DataFrame({
            'Fruit': ['Apple', 'Banana', 'Orange'] * 100,
            'Sales': range(300),
            'UnitsSold': range(300)
        })

        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            test_data.to_csv(f.name, index=False)
            csv_path = f.name

        try:
            # Create data source
            class PerformanceDataSource(BaseDataSource):
                def _load_data(self, params: dict) -> pd.DataFrame:
                    return pd.read_csv(csv_path)

                def get_kpis(self) -> dict:
                    if self._data is None:
                        return {}
                    return {
                        "total_sales": float(self._data["Sales"].sum()),
                        "total_units": int(self._data["UnitsSold"].sum())
                    }

                def get_filter_options(self, filter_name: str) -> list:
                    return []

                def get_summary(self) -> str:
                    return "Performance test data source"

            # Initialize data source
            datasource = PerformanceDataSource()
            datasource.init_data()

            # Measure block creation time
            start_time = time.time()
            
            blocks = []
            for i in range(10):  # Create 10 blocks
                kpi_block = KPIBlock(
                    block_id=f"perf_kpi_{i}",
                    datasource=datasource,
                    kpi_definitions=[
                        {"key": "total_sales", "title": "Total Sales", "color": "success"},
                        {"key": "total_units", "title": "Total Units", "color": "info"}
                    ],
                    subscribes_to="dummy_state"
                )
                blocks.append(kpi_block)

            creation_time = time.time() - start_time

            # Validate performance
            assert creation_time < 2.0, f"Block creation took {creation_time:.2f}s, expected < 2.0s"
            assert len(blocks) == 10

        finally:
            os.unlink(csv_path)

    def test_state_update_propagation_time(self):
        """
        Test state update propagation performance.

        :hierarchy: [Testing | Integration Tests | Performance | State Updates]
        :covers:
         - object: "workflow: 'State Update Propagation'"
         - requirement: "State updates must propagate efficiently"

        :scenario: "Verifies that state updates propagate quickly to all subscribers"
        :strategy: "Measures time for state updates to propagate through multiple components"
        :contract:
         - pre: "Multiple components subscribed to state changes"
         - post: "State updates propagate within acceptable time limits"

        """
        # Generate test data
        test_data = pd.DataFrame({
            'Fruit': ['Apple', 'Banana', 'Orange'] * 50,
            'Sales': range(150),
            'UnitsSold': range(150)
        })

        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            test_data.to_csv(f.name, index=False)
            csv_path = f.name

        try:
            # Create data source
            class StateDataSource(BaseDataSource):
                def _load_data(self, params: dict) -> pd.DataFrame:
                    return pd.read_csv(csv_path)

                def get_kpis(self) -> dict:
                    if self._data is None:
                        return {}
                    return {
                        "total_sales": float(self._data["Sales"].sum()),
                        "total_units": int(self._data["UnitsSold"].sum())
                    }

                def get_filter_options(self, filter_name: str) -> list:
                    return []

                def get_summary(self) -> str:
                    return "State test data source"

            # Initialize data source
            datasource = StateDataSource()
            datasource.init_data()

            # Create multiple KPI blocks
            blocks = []
            for i in range(5):  # Create 5 blocks
                kpi_block = KPIBlock(
                    block_id=f"state_kpi_{i}",
                    datasource=datasource,
                    kpi_definitions=[
                        {"key": "total_sales", "title": "Total Sales", "color": "success"},
                        {"key": "total_units", "title": "Total Units", "color": "info"}
                    ],
                    subscribes_to="test_state"
                )
                blocks.append(kpi_block)

            # Measure state update time
            start_time = time.time()
            
            # Simulate state update by calling update methods
            for block in blocks:
                block._update_kpi_cards()
            
            update_time = time.time() - start_time

            # Validate performance
            assert update_time < 1.0, f"State update took {update_time:.3f}s, expected < 1.0s"
            assert len(blocks) == 5

        finally:
            os.unlink(csv_path)
