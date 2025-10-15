"""
This file contains shared fixtures for the test suite.

"""

from unittest.mock import MagicMock

import pandas as pd
import pytest

from dashboard_lego.core.datasource import BaseDataSource


@pytest.fixture(autouse=True)
def clear_cache_registry():
    """
    Clear cache registry before each test to prevent test interference.

    :hierarchy: [Testing | Fixtures | Cache Management]
    :relates-to:
     - motivated_by: "Tests fail due to shared cache registry between tests causing data contamination"
     - implements: "fixture: 'clear_cache_registry'"
    :contract:
     - pre: "Test is starting"
     - post: "Cache registry is cleared, no shared state between tests"
    """
    # Clear cache registry before test
    BaseDataSource._cache_registry.clear()

    yield

    # Clear cache registry after test
    BaseDataSource._cache_registry.clear()


@pytest.fixture
def datasource_factory():
    """
    A factory fixture that creates mock BaseDataSource objects.

    This allows tests to easily configure the data that a block will receive.

        :hierarchy: [Testing | Fixtures]
        :rationale: "Chosen a factory returning a MagicMock for maximum flexibility in tests."

    """

    def _factory(**kwargs):
        """
        Creates a mock datasource.

        Args:
            **kwargs: Key-value pairs where the key is the method to mock
                      and the value is the return value.
                      Example: `get_kpis={"sales": 100}`

        """
        mock_ds = MagicMock(spec=BaseDataSource)
        for method_name, return_value in kwargs.items():
            # Set the return_value for the mocked method
            setattr(mock_ds, method_name, MagicMock(return_value=return_value))

        # Ensure get_processed_data returns a DataFrame by default if not specified
        if "get_processed_data" not in kwargs:
            mock_ds.get_processed_data.return_value = pd.DataFrame()

        return mock_ds

    return _factory


@pytest.fixture
def sample_csv_data():
    """
    Sample CSV data for integration tests.

    :hierarchy: [Testing | Fixtures | Sample Data]
    :relates-to:
     - motivated_by: "Integration tests need realistic data for E2E testing"
     - implements: "fixture: 'sample_csv_data'"

    :rationale: "Provides consistent test data across integration tests"
    :contract:
     - pre: "Test environment is set up"
     - post: "Returns DataFrame with sample sales data"

    """
    return pd.DataFrame(
        {
            "Fruit": [
                "Apple",
                "Banana",
                "Orange",
                "Apple",
                "Banana",
                "Orange",
                "Apple",
                "Banana",
            ],
            "Sales": [100, 150, 120, 110, 160, 130, 105, 155],
            "UnitsSold": [10, 15, 12, 11, 16, 13, 10, 15],
            "Price": [10.0, 10.0, 10.0, 10.0, 10.0, 10.0, 10.5, 9.7],
        }
    )
