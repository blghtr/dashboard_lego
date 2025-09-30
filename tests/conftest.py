"""
This file contains shared fixtures for the test suite.

"""
from unittest.mock import MagicMock

import pandas as pd
import pytest

from core.datasource import BaseDataSource

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
        if 'get_processed_data' not in kwargs:
            mock_ds.get_processed_data.return_value = pd.DataFrame()

        return mock_ds

    return _factory
