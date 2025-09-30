"""
This module defines the abstract interface for data sources.

"""
import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd
from diskcache import Cache

class BaseDataSource(ABC):
    """
    An abstract base class that defines the contract for data sources.
    This base class includes a transparent caching layer to prevent re-loading data.

        :hierarchy: [Core | DataSources | BaseDataSource]
        :relates-to:
          - motivated_by: "plan.md: Фаза 5.3 - Улучшение кэширования"
          - implements: "interface: 'BaseDataSource'"
          - uses: ["library: 'diskcache'"]

        :rationale: "Replaced cachetools with diskcache to support both in-memory and persistent disk-based caching, configured via constructor arguments."
        :contract:
          - pre: "A concrete implementation of this class must be provided."
          - post: "Dashboard blocks can reliably request data, benefiting from a configurable caching layer."

    """
    def __init__(self, cache_dir: Optional[str] = None, cache_ttl: int = 300, **kwargs):
        """
        Initializes the BaseDataSource with a configurable cache.

        Args:
            cache_dir: Directory for the disk cache. If None, an in-memory cache is used.
            cache_ttl: The time-to-live for each item in seconds.

        """
        self.cache = Cache(directory=cache_dir, expire=cache_ttl)
        self._data: Optional[pd.DataFrame] = None

    def _get_cache_key(self, params: Dict[str, Any]) -> str:
        """
        Creates a stable, hashable cache key from a dictionary of parameters.

        """
        if not params:
            return "default"
        return json.dumps(params, sort_keys=True)

    def init_data(self, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Initializes or recalculates the data based on the given parameters.
        This method acts as a caching wrapper around the `_load_data` method.

        Args:
            params: A dictionary containing all necessary parameters for data processing.

        Returns:
            True if initialization was successful, False otherwise.

        """
        params = params or {}
        cache_key = self._get_cache_key(params)

        if cache_key in self.cache:
            # Cache Hit
            self._data = self.cache[cache_key]
            return True
        else:
            # Cache Miss
            try:
                loaded_data = self._load_data(params)
                self._data = loaded_data
                self.cache[cache_key] = loaded_data
                return True
            except Exception as e:
                print(f"Error loading data for key {cache_key}: {e}")
                self._data = pd.DataFrame() # Ensure data is empty on error
                return False

    @abstractmethod
    def _load_data(self, params: Dict[str, Any]) -> pd.DataFrame:
        """
        The method that concrete subclasses must implement to load data.

        Args:
            params: A dictionary containing all necessary parameters for data processing.

        Returns:
            A pandas DataFrame with the loaded data.

        """
        pass

    def get_processed_data(self) -> pd.DataFrame:
        """
        Returns the main processed pandas DataFrame.

        """
        if self._data is None:
            # This case handles when get_processed_data is called before init_data
            # We can attempt a default load, but it might be better to enforce init_data first.
            # For now, we return an empty DataFrame to avoid errors.
            return pd.DataFrame()
        return self._data

    @abstractmethod
    def get_kpis(self) -> Dict[str, Any]:
        """
        Returns a dictionary of key performance indicators (KPIs).

        """
        pass

    @abstractmethod
    def get_filter_options(self, filter_name: str) -> List[Dict[str, Any]]:
        """
        Returns a list of options for a given filter control.

        """
        pass

    @abstractmethod
    def get_summary(self) -> str:
        """
        Returns a short text summary of the loaded data.

        """
        pass
