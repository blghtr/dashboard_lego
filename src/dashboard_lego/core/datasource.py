"""
This module defines the abstract interface for data sources with pipeline architecture.

:hierarchy: [Core | DataSources | BaseDataSource]
:relates-to:
 - motivated_by: "Refactor: Implement staged data processing pipeline (Load -> Preprocess -> Filter)"
 - implements: "interface: 'BaseDataSource' with pipeline"
 - uses: ["library: 'diskcache'", "class: 'PreProcessor'", "class: 'DataFilter'"]

:contract:
 - pre: "Subclass implements _load_raw_data() instead of _load_data()"
 - post: "Data flows through: load → preprocess → filter → cache"
 - invariant: "Each stage has separate caching based on relevant params only"

:complexity: 8
:decision_cache: "Chose staged pipeline over monolithic _load_data for better caching and separation of concerns"
"""

import json
from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

import pandas as pd
from diskcache import Cache

from dashboard_lego.utils.exceptions import CacheError, DataLoadError
from dashboard_lego.utils.formatting import NumpyEncoder
from dashboard_lego.utils.logger import get_logger


class BaseDataSource(ABC):
    """
    Abstract base class with data processing pipeline.

    Pipeline stages:
    1. Load raw data (_load_raw_data)
    2. Preprocess (PreProcessor.process)
    3. Filter (DataFilter.filter)
    4. Cache result at each stage

    Each stage can be cached independently based on its relevant params only,
    enabling efficient updates when only filtering changes.

    :hierarchy: [Core | DataSources | BaseDataSource]
    :relates-to:
     - motivated_by: "Refactor: Staged pipeline for better caching and separation of concerns"
     - implements: "interface: 'BaseDataSource' with pipeline"
     - uses: ["library: 'diskcache'", "class: 'PreProcessor'", "class: 'DataFilter'"]

    :rationale: "Staged pipeline allows caching at each level, so filtering changes don't trigger preprocessing"
    :contract:
     - pre: "Subclass implements _load_raw_data()"
     - post: "Data flows through 3-stage pipeline with independent caching"
     - invariant: "get_processed_data() always returns filtered data"
    """

    def __init__(
        self,
        cache_dir: Optional[str] = None,
        cache_ttl: int = 300,
        preprocessor: Optional[Any] = None,
        data_filter: Optional[Any] = None,
        param_classifier: Optional[Callable[[str], str]] = None,
        **kwargs,
    ):
        """
        Initialize datasource with pipeline components.

        :hierarchy: [Core | DataSources | BaseDataSource | Initialization]
        :relates-to:
         - motivated_by: "Need configurable pipeline components"
         - implements: "method: '__init__' with pipeline support"

        :contract:
         - pre: "All parameters are optional with sensible defaults"
         - post: "DataSource ready with complete pipeline"

        Args:
            cache_dir: Directory for disk cache. If None, uses in-memory cache.
            cache_ttl: Time-to-live for cache entries in seconds.
            preprocessor: PreProcessor instance for data transformation.
                        If None, creates default (no-op) preprocessor.
            data_filter: DataFilter instance for data filtering.
                       If None, creates default (no-op) filter.
            param_classifier: Function to classify params as 'preprocess' or 'filter'.
                            Signature: (param_key: str) -> str
                            If None, all params treated as preprocessing params.
        """
        self.logger = get_logger(__name__, BaseDataSource)
        self.logger.info("Initializing datasource with pipeline architecture")

        # Initialize cache
        try:
            self.cache = Cache(directory=cache_dir, expire=cache_ttl)
            self.logger.debug("Cache initialized successfully")
        except Exception as e:
            self.logger.error(f"Failed to initialize cache: {e}")
            raise CacheError(f"Cache initialization failed: {e}") from e

        # Import here to avoid circular imports
        from dashboard_lego.core.data_filter import DataFilter
        from dashboard_lego.core.preprocessor import PreProcessor

        # Initialize pipeline components
        self.preprocessor = preprocessor or PreProcessor(logger=self.logger)
        self.data_filter = data_filter or DataFilter(logger=self.logger)
        self.param_classifier = param_classifier

        # Data storage for each pipeline stage
        self._raw_data: Optional[pd.DataFrame] = None
        self._preprocessed_data: Optional[pd.DataFrame] = None
        self._filtered_data: Optional[pd.DataFrame] = None

        # Legacy support: keep _data attribute pointing to filtered data
        self._data: Optional[pd.DataFrame] = None

        self.logger.info(
            f"DataSource initialized: cache_dir={cache_dir}, ttl={cache_ttl}s, "
            f"preprocessor={type(self.preprocessor).__name__}, "
            f"filter={type(self.data_filter).__name__}"
        )

    def _get_cache_key(self, stage: str, params: Dict[str, Any]) -> str:
        """
        Create cache key for specific pipeline stage.

        :hierarchy: [Core | DataSources | BaseDataSource | Caching]
        :relates-to:
         - motivated_by: "Need stage-specific cache keys for independent caching"
         - implements: "method: '_get_cache_key' with stage support"

        :contract:
         - pre: "stage is valid string, params is dict"
         - post: "Returns stable cache key unique to stage + params"
         - invariant: "Same stage + params always produces same key"

        Args:
            stage: Pipeline stage ('raw', 'preprocessed', 'filtered')
            params: Parameters relevant to this stage

        Returns:
            Stable cache key string
        """
        if not params:
            return f"{stage}_default"
        params_json = json.dumps(params, sort_keys=True, cls=NumpyEncoder)
        return f"{stage}_{params_json}"

    def init_data(self, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Initialize data through 3-stage pipeline with staged caching.

        Pipeline flow:
        1. Classify params → preprocessing_params, filtering_params
        2. Load raw data (cached by preprocessing params)
        3. Preprocess (cached by preprocessing params)
        4. Filter (cached by all params for final result)

        :hierarchy: [Core | DataSources | BaseDataSource | Pipeline Orchestration]
        :relates-to:
         - motivated_by: "Refactor: Implement staged pipeline for better caching"
         - implements: "method: 'init_data' with 3-stage pipeline"
         - uses: ["class: 'DataProcessingContext'", "class: 'PreProcessor'", "class: 'DataFilter'"]

        :contract:
         - pre: "params can be None or dict"
         - post: "Data flows through complete pipeline; _filtered_data is set"
         - invariant: "Filtering changes don't trigger preprocessing"

        :complexity: 7
        :decision_cache: "Staged caching enables efficient filter-only updates"

        Args:
            params: Control parameters from UI. Can contain both preprocessing
                   and filtering parameters, which will be classified automatically.

        Returns:
            True if successful, False otherwise
        """
        params = params or {}
        self.logger.info(f"🔄 init_data called with params: {list(params.keys())}")

        try:
            # Import here to avoid circular imports
            from dashboard_lego.core.processing_context import DataProcessingContext

            # Create processing context to classify params
            context = DataProcessingContext.from_params(params, self.param_classifier)
            self.logger.debug(
                f"Context created: preprocess={list(context.preprocessing_params.keys())}, "
                f"filter={list(context.filtering_params.keys())}"
            )

            # Stage 1: Load raw data (cached by preprocessing params only)
            raw_cache_key = self._get_cache_key("raw", context.preprocessing_params)
            if raw_cache_key in self.cache:
                self.logger.info(f"✅ Stage 1 cache hit: raw data ({raw_cache_key})")
                self._raw_data = self.cache[raw_cache_key]
                self.logger.debug(f"Loaded {len(self._raw_data)} rows from cache")
            else:
                self.logger.info("📥 Stage 1 cache miss: loading raw data")
                self._raw_data = self._load_raw_data(context.preprocessing_params)
                if not isinstance(self._raw_data, pd.DataFrame):
                    raise DataLoadError(
                        f"_load_raw_data must return DataFrame, got {type(self._raw_data)}"
                    )
                self.cache[raw_cache_key] = self._raw_data
                self.logger.info(
                    f"Raw data loaded: {len(self._raw_data)} rows, "
                    f"{len(self._raw_data.columns)} columns"
                )

            # Stage 2: Preprocess (cached by preprocessing params)
            preprocess_cache_key = self._get_cache_key(
                "preprocessed", context.preprocessing_params
            )
            if preprocess_cache_key in self.cache:
                self.logger.info(
                    f"✅ Stage 2 cache hit: preprocessed data ({preprocess_cache_key})"
                )
                self._preprocessed_data = self.cache[preprocess_cache_key]
                self.logger.debug(
                    f"Loaded {len(self._preprocessed_data)} rows from cache"
                )
            else:
                self.logger.info("⚙️ Stage 2 cache miss: preprocessing data")
                self._preprocessed_data = self.preprocessor.process(
                    self._raw_data, context.preprocessing_params
                )
                if not isinstance(self._preprocessed_data, pd.DataFrame):
                    raise DataLoadError(
                        f"PreProcessor.process must return DataFrame, "
                        f"got {type(self._preprocessed_data)}"
                    )
                self.cache[preprocess_cache_key] = self._preprocessed_data
                self.logger.info(
                    f"Data preprocessed: {len(self._preprocessed_data)} rows"
                )

            # Stage 3: Filter (cached by ALL params)
            filter_cache_key = self._get_cache_key("filtered", context.raw_params)
            if filter_cache_key in self.cache:
                self.logger.info(
                    f"✅ Stage 3 cache hit: filtered data ({filter_cache_key})"
                )
                self._filtered_data = self.cache[filter_cache_key]
                self.logger.debug(f"Loaded {len(self._filtered_data)} rows from cache")
            else:
                self.logger.info("🔍 Stage 3 cache miss: filtering data")
                self._filtered_data = self.data_filter.filter(
                    self._preprocessed_data, context.filtering_params
                )
                if not isinstance(self._filtered_data, pd.DataFrame):
                    raise DataLoadError(
                        f"DataFilter.filter must return DataFrame, "
                        f"got {type(self._filtered_data)}"
                    )
                self.cache[filter_cache_key] = self._filtered_data
                self.logger.info(
                    f"Data filtered: {len(self._filtered_data)} rows "
                    f"(from {len(self._preprocessed_data)})"
                )

            # Legacy support: keep _data pointing to filtered data
            self._data = self._filtered_data

            self.logger.info(
                f"✅ Pipeline complete: {len(self._filtered_data)} rows in final dataset"
            )
            return True

        except DataLoadError as e:
            self.logger.error(f"DataLoadError in pipeline: {e}")
            self._raw_data = pd.DataFrame()
            self._preprocessed_data = pd.DataFrame()
            self._filtered_data = pd.DataFrame()
            self._data = pd.DataFrame()
            return False
        except Exception as e:
            self.logger.error(f"Error in pipeline: {e}", exc_info=True)
            self._raw_data = pd.DataFrame()
            self._preprocessed_data = pd.DataFrame()
            self._filtered_data = pd.DataFrame()
            self._data = pd.DataFrame()
            return False

    @abstractmethod
    def _load_raw_data(self, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Load raw data from source (NO filtering, NO preprocessing).

        :hierarchy: [Core | DataSources | BaseDataSource | Load Stage]
        :relates-to:
         - motivated_by: "Refactor: Separate raw data loading from transformation"
         - implements: "abstract method: '_load_raw_data'"

        :contract:
         - pre: "params contains preprocessing params only"
         - post: "Returns raw DataFrame from data source"
         - invariant: "Does NOT apply filters - that's DataFilter's job"

        Args:
            params: Parameters that affect data loading (NOT filtering params).
                   For example: file path, SQL query parameters, column selection.
                   Filtering params like category or price range should be handled
                   by DataFilter, not here.

        Returns:
            Raw pandas DataFrame

        Raises:
            DataLoadError: If loading fails

        Note:
            This replaces the old _load_data() method.
            ONLY handle data LOADING here, not filtering or transformation.

        Example:
            >>> def _load_raw_data(self, params):
            ...     # Good: Just load the data
            ...     return pd.read_csv(self.file_path)
            ...
            ...     # Bad: Don't do filtering here
            ...     # df = pd.read_csv(self.file_path)
            ...     # if 'category' in params:
            ...     #     df = df[df['Category'] == params['category']]  # NO!
            ...     # return df
        """
        pass

    def get_data(self) -> pd.DataFrame:
        """
        Get currently loaded raw data.

        :hierarchy: [Core | DataSources | BaseDataSource | Data Access]
        :relates-to:
         - motivated_by: "Need access to raw data before preprocessing"
         - implements: "method: 'get_data'"

        :contract:
         - pre: "init_data() may or may not have been called"
         - post: "Returns raw DataFrame or empty DataFrame"

        Returns:
            Raw DataFrame or empty DataFrame if not initialized
        """
        if self._raw_data is None:
            self.logger.warning(
                "get_data called before init_data, returning empty DataFrame"
            )
            return pd.DataFrame()
        return self._raw_data

    def get_preprocessed_data(self) -> pd.DataFrame:
        """
        Get preprocessed data (after PreProcessor, before DataFilter).

        :hierarchy: [Core | DataSources | BaseDataSource | Data Access]
        :relates-to:
         - motivated_by: "Need access to preprocessed data before filtering"
         - implements: "method: 'get_preprocessed_data'"

        :contract:
         - pre: "init_data() may or may not have been called"
         - post: "Returns preprocessed DataFrame or empty DataFrame"

        Returns:
            Preprocessed DataFrame or empty DataFrame if not initialized

        Note:
            Useful for operations that need the full dataset before filtering,
            such as generating filter options from all available values.
        """
        if self._preprocessed_data is None:
            self.logger.warning(
                "get_preprocessed_data called before init_data, returning empty DataFrame"
            )
            return pd.DataFrame()
        return self._preprocessed_data

    def get_processed_data(self) -> pd.DataFrame:
        """
        Get final filtered data (end of pipeline).

        :hierarchy: [Core | DataSources | BaseDataSource | Data Access]
        :relates-to:
         - motivated_by: "Primary data access method for blocks"
         - implements: "method: 'get_processed_data'"

        :contract:
         - pre: "init_data() may or may not have been called"
         - post: "Returns filtered DataFrame or empty DataFrame"
         - invariant: "Returns final pipeline output"

        Returns:
            Filtered DataFrame or empty DataFrame if not initialized

        Note:
            This is the primary method blocks should use to get data.
            It returns the fully processed result after all pipeline stages.
        """
        if self._filtered_data is None:
            self.logger.warning(
                "get_processed_data called before init_data, returning empty DataFrame"
            )
            return pd.DataFrame()
        return self._filtered_data

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
