"""
Unit tests for the BaseDataSource class.

"""

import shutil
import time
from typing import Any, Dict, List

import pandas as pd
import pytest
from diskcache import Cache
from pandas.testing import assert_frame_equal

from dashboard_lego.core.datasource import BaseDataSource


@pytest.fixture
def temp_cache(tmp_path):
    """
    A pytest fixture that creates, yields, and properly closes a diskcache.Cache object
    in a temporary directory.
    """
    cache_dir = tmp_path / "test_cache"
    cache = Cache(directory=str(cache_dir))
    yield cache
    cache.close()


@pytest.fixture
def temp_ttl_cache(tmp_path):
    """
    A pytest fixture for a cache with a very short TTL for expiration tests.
    """
    cache_dir = tmp_path / "test_ttl_cache"
    cache = Cache(directory=str(cache_dir), expire=0.1)
    yield cache
    cache.close()


# A concrete implementation of the abstract BaseDataSource for testing.
class ConcreteDataSource(BaseDataSource):
    """
    A concrete test implementation of BaseDataSource.
    It implements the abstract methods and allows us to test the base class logic.

        :hierarchy: [Tests | Core | DataSource]
        :covers:
          - object: "class: BaseDataSource"

    """

    def __init__(self, cache_obj: Cache = None, **kwargs):
        # Allow injecting a cache object for testing purposes
        if cache_obj:
            self.cache = cache_obj
            self._data = None
        else:
            super().__init__(**kwargs)

    def _load_data(self, params: Dict[str, Any]) -> pd.DataFrame:
        """
        A mock data loading method.
        Returns a DataFrame with a value from the params for testing.

        """
        # This method will be spied on to check call counts.
        val = params.get("value", 0)
        return pd.DataFrame({"A": [val]})

    def get_kpis(self) -> Dict[str, Any]:
        return {"test_kpi": 1}

    def get_filter_options(self, filter_name: str) -> List[Dict[str, Any]]:
        return [{"label": "Test", "value": "test"}]

    def get_summary(self) -> str:
        return "Test Summary"


def test_datasource_in_memory_caching_hit(mocker):
    """
    Tests that the _load_data method is only called once for identical params with in-memory cache.

        :scenario: Call `init_data` twice with the same parameters.
        :strategy: Use `mocker.spy` to track calls to `_load_data`.     :contract:
      - pre: "`init_data` is called multiple times with identical `params`."
      - post: "`_load_data` is executed only on the first call."

    """
    source = ConcreteDataSource()
    spy = mocker.spy(source, "_load_data")

    params = {"value": 100}

    source.init_data(params)
    source.init_data(params)

    spy.assert_called_once_with(params)


def test_datasource_disk_caching_hit(mocker, temp_cache):
    """
    Tests that the _load_data method is only called once for identical params with disk cache.

        :scenario: Call `init_data` twice with the same parameters on a disk-cached source.
        :strategy: Use `mocker.spy` and a temporary directory for the cache.     :contract:
      - pre: "`init_data` is called multiple times with identical `params` on a disk-cached source."
      - post: "`_load_data` is executed only on the first call."

    """
    source = ConcreteDataSource(cache_obj=temp_cache)
    spy = mocker.spy(source, "_load_data")
    params = {"value": 200}

    # First call, should hit the disk
    source.init_data(params)

    # Second call, should be a cache hit
    source.init_data(params)
    data2 = source.get_processed_data()

    spy.assert_called_once_with(params)
    assert data2["A"][0] == 200


def test_datasource_caching_miss(mocker):
    """
    Tests that the _load_data method is called again for different params.

        :scenario: Call `init_data` with two different sets of parameters.
        :strategy: Use `mocker.spy` to track calls to `_load_data`.     :contract:
      - pre: "`init_data` is called with different `params`."
      - post: "`_load_data` is executed for each unique set of `params`."

    """
    source = ConcreteDataSource()
    spy = mocker.spy(source, "_load_data")

    params1 = {"value": 1}
    params2 = {"value": 2}

    source.init_data(params1)
    source.init_data(params2)

    assert spy.call_count == 2


def test_datasource_cache_ttl_configuration():
    """
    Tests that the cache_ttl parameter is correctly passed to the underlying cache object.
    """
    # Test with a specific TTL
    source = ConcreteDataSource(cache_ttl=123)
    assert source.cache.expire == 123
    source.cache.close()

    # Test with default TTL
    source_default = ConcreteDataSource()
    assert source_default.cache.expire == 300  # Default value in BaseDataSource
    source_default.cache.close()


def test_datasource_load_error_handling(mocker):
    """
    Tests that the datasource handles errors during data loading gracefully.

        :scenario: The `_load_data` method raises an exception.
        :strategy: Use `mocker.patch` to make `_load_data` raise an error.     :contract:
      - pre: "`_load_data` throws an exception."
      - post: "`init_data` returns `False` and `get_processed_data` returns an empty DataFrame."

    """
    source = ConcreteDataSource()
    mocker.patch.object(source, "_load_data", side_effect=ValueError("Failed to load"))

    result = source.init_data({"value": 1})
    data = source.get_processed_data()

    assert result is False
    assert isinstance(data, pd.DataFrame)
    assert data.empty


def test_get_processed_data_before_init():
    """
    Tests that get_processed_data returns an empty DataFrame if called before init_data.

        :scenario: Call `get_processed_data` on a new datasource instance.
        :strategy: Direct call and assertion.     :contract:
      - pre: "`init_data` has not been called."
      - post: "`get_processed_data` returns an empty DataFrame."

    """
    source = ConcreteDataSource()
    data = source.get_processed_data()
    assert isinstance(data, pd.DataFrame)
    assert data.empty
