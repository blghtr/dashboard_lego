"""
This module defines the abstract interface for data sources.

"""

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional

import pandas as pd
from diskcache import Cache

from dashboard_lego.utils.exceptions import CacheError, DataLoadError
from dashboard_lego.utils.logger import get_logger


class BaseDataSource(ABC):
    """
    An abstract base class that defines the contract for data sources.
    This base class includes a transparent caching layer to prevent
    re-loading data.

        :hierarchy: [Core | DataSources | BaseDataSource]
        :relates-to:
          - motivated_by: "Architectural Conclusion: Disk-based caching improves
            performance by avoiding repeated data loading operations"
          - implements: "interface: 'BaseDataSource'"
          - uses: ["library: 'diskcache'"]

        :rationale: "Replaced cachetools with diskcache to support both
         in-memory and persistent disk-based caching, configured via
         constructor arguments."
        :contract:
          - pre: "A concrete implementation of this class must be provided."
          - post: "Dashboard blocks can reliably request data,
           benefiting from a configurable caching layer."

    """

    def __init__(self, cache_dir: Optional[str] = None, cache_ttl: int = 300, **kwargs):
        """
        Initializes the BaseDataSource with a configurable cache.

        Args:
            cache_dir: Directory for the disk cache. If None, an in-memory
                       cache is used.
            cache_ttl: The time-to-live for each item in seconds.

        """
        self.logger = get_logger(__name__, BaseDataSource)
        self.logger.info(
            f"Initializing datasource with cache_dir={cache_dir}, " f"ttl={cache_ttl}s"
        )
        try:
            self.cache = Cache(directory=cache_dir, expire=cache_ttl)
            self.logger.debug("Cache initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize cache: {e}")
            raise CacheError(f"Cache initialization failed: {e}") from e
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
            params: A dictionary containing all necessary parameters for
                    data processing.

        Returns:
            True if initialization was successful, False otherwise.

        """
        params = params or {}
        cache_key = self._get_cache_key(params)
        self.logger.debug(f"init_data called with cache_key={cache_key}")

        try:
            if cache_key in self.cache:
                # Cache Hit
                self.logger.info(f"Cache hit for key={cache_key}")
                self._data = self.cache[cache_key]
                self.logger.debug(f"Loaded {len(self._data)} rows from cache")
                return True
            else:
                # Cache Miss
                self.logger.info(f"Cache miss for key={cache_key}, loading data")
                loaded_data = self._load_data(params)
                if not isinstance(loaded_data, pd.DataFrame):
                    raise DataLoadError(
                        f"_load_data must return a DataFrame, got "
                        f"{type(loaded_data)}"
                    )
                self._data = loaded_data
                self.cache[cache_key] = loaded_data
                self.logger.info(
                    f"Data loaded successfully: {len(loaded_data)} rows, "
                    f"{len(loaded_data.columns)} columns"
                )
                self.logger.debug(f"Data cached with key={cache_key}")
                return True
        except DataLoadError as e:
            # Log the error and set empty data
            self.logger.error(f"DataLoadError loading data for key {cache_key}: {e}")
            self._data = pd.DataFrame()  # Ensure data is empty on error
            return False
        except Exception as e:
            self.logger.error(
                f"Error loading data for key {cache_key}: {e}", exc_info=True
            )
            self._data = pd.DataFrame()  # Ensure data is empty on error
            return False

    @abstractmethod
    def _load_data(self, params: Dict[str, Any]) -> pd.DataFrame:
        """
        The method that concrete subclasses must implement to load data.

        Args:
            params: A dictionary containing all necessary parameters for
                     data processing.

        Returns:
            A pandas DataFrame with the loaded data.

        """
        pass

    def get_processed_data(self) -> pd.DataFrame:
        """
        Returns the main processed pandas DataFrame.

        """
        if self._data is None:
            # This case handles when get_processed_data is called before
            # init_data. For now, we return an empty DataFrame to avoid errors.
            self.logger.warning(
                "get_processed_data called before init_data, "
                "returning empty DataFrame"
            )
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
