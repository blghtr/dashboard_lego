# 05_logging_demo.py

"""
Demonstration of the logging system in dashboard_lego.

This example shows:
1. How to configure logging with different levels
2. How hierarchy is automatically extracted from docstrings
3. How INFO and DEBUG logs work differently
4. How logging works across different modules

"""
import os

import pandas as pd

from blocks.kpi import KPIBlock
from core.datasource import BaseDataSource
from core.datasources.csv_source import CsvDataSource
from core.page import DashboardPage
from utils.logger import get_logger, setup_logging


def demonstrate_logging():
    """
    Demonstrates the logging functionality.

        :hierarchy: [Examples | Logging Demo | demonstrate_logging]
        :relates-to:
         - motivated_by: "User requirement: Demonstrate logging functionality"
         - implements: "function: 'demonstrate_logging'"
         - uses: ["class: 'CsvDataSource'", "class: 'KPIBlock'"]

        :rationale: "Function demonstrates both INFO and DEBUG logging with
         automatic hierarchy extraction."
        :contract:
         - pre: "Sample data file exists."
         - post: "Logging demonstration is complete with visible output."

    """
    # Setup logging with DEBUG level to see hierarchy
    setup_logging(level="DEBUG")
    logger = get_logger(__name__, demonstrate_logging)

    logger.info("=== Dashboard Lego Logging Demo ===")
    logger.debug("This is a DEBUG message - you should see hierarchy above")

    # Create a custom datasource to show logging
    class DemoDataSource(BaseDataSource):
        """
        A demo datasource for logging demonstration.

            :hierarchy: [Examples | Logging Demo | DemoDataSource]
            :relates-to:
             - motivated_by: "User requirement: Show logging in custom datasource"
             - implements: "class: 'DemoDataSource'"
             - uses: ["class: 'BaseDataSource'"]

            :rationale: "Custom datasource demonstrates logging integration."
            :contract:
             - pre: "Valid data is provided."
             - post: "Data is processed with logging."

        """

        def __init__(self, data: pd.DataFrame):
            super().__init__()
            self.logger = get_logger(__name__, DemoDataSource)
            self.logger.info("DemoDataSource initialized")
            self._data = data

        def _load_data(self, params: dict) -> pd.DataFrame:
            self.logger.debug(f"Loading data with params: {params}")
            self.logger.info(f"Data loaded: {len(self._data)} rows")
            return self._data

        def get_kpis(self) -> dict:
            self.logger.debug("Calculating KPIs")
            return {"total_rows": len(self._data)}

        def get_filter_options(self, filter_name: str) -> list:
            return []

        def get_summary(self) -> str:
            return f"Demo data with {len(self._data)} rows"

    # Create sample data
    logger.info("Creating sample data")
    sample_data = pd.DataFrame(
        {
            "Category": ["A", "B", "A", "B", "A"],
            "Value": [10, 20, 15, 25, 12],
            "Sales": [100, 200, 150, 250, 120],
        }
    )

    # Test CSV datasource logging
    logger.info("Testing CSV datasource logging")
    csv_file = "examples/sample_data.csv"
    if os.path.exists(csv_file):
        csv_datasource = CsvDataSource(csv_file)
        csv_datasource.init_data()
        logger.info("CSV datasource test completed")
    else:
        logger.warning(f"Sample CSV file not found: {csv_file}")

    # Test custom datasource
    logger.info("Testing custom datasource")
    demo_datasource = DemoDataSource(sample_data)
    demo_datasource.init_data()

    # Test KPI block logging
    logger.info("Testing KPI block logging")
    kpi_block = KPIBlock(
        block_id="demo_kpis",
        datasource=demo_datasource,
        kpi_definitions=[{"key": "total_rows", "title": "Total Rows"}],
    )

    # Test page creation logging
    logger.info("Testing page creation logging")
    page = DashboardPage(title="Logging Demo", blocks=[[kpi_block]])

    logger.info("=== Logging Demo Complete ===")
    logger.info("Check the console output above to see:")
    logger.info("1. INFO messages (user-friendly)")
    logger.info("2. DEBUG messages with [Hierarchy] prefixes")
    logger.info("3. Automatic hierarchy extraction from docstrings")
    logger.info("4. Logging across different modules")


if __name__ == "__main__":
    demonstrate_logging()
