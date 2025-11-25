"""
This module defines the base data source with stateless 2-stage pipeline.

:hierarchy: [Core | DataSources | DataSource]
:relates-to:
 - motivated_by: "v0.15.0 Refactor: Stateless architecture with 2-stage pipeline + optional lambda functions"
 - implements: "interface: 'DataSource' with stateless pipeline and lambda function support"
 - uses: ["library: 'diskcache'", "class: 'DataBuilder'", "class: 'DataFilter'"]

:contract:
 - pre: "data_builder and data_filter provided OR build_fn/transform_fn for simple cases"
 - post: "get_processed_data(params) runs Build → Filter pipeline"
 - invariant: "NO stored data state, NO abstract methods, only cache"

:complexity: 7
:decision_cache: "2-stage pipeline (Build → Filter) for semantic clarity + lambda functions for simplicity"

Example usage with lambda functions:
    >>> # Simple datasource with lambda functions
    >>> ds = DataSource(
    ...     build_fn=lambda params: pd.DataFrame({'x': [1, 2, 3]}),
    ...     transform_fn=lambda df: df * 2
    ... )
    >>> result = ds.get_processed_data()
    >>>
    >>> # More complex with parameters
    >>> ds = DataSource(
    ...     build_fn=lambda params: pd.read_csv(params.get('file', 'default.csv')),
    ...     transform_fn=lambda df: df.groupby('category').sum().reset_index()
    ... )
    >>> result = ds.get_processed_data({'file': 'sales.csv'})
    >>>
    >>> # With cache prewarming
    >>> ds = DataSource(
    ...     build_fn=lambda params: pd.read_csv(params.get('file', 'default.csv')),
    ...     transform_fn=lambda df: df.groupby('category').sum().reset_index(),
    ...     cache_prewarm_params=[
    ...         {'file': 'sales.csv', 'category': 'Electronics'},
    ...         {'file': 'sales.csv', 'category': 'Home'}
    ...     ]
    ... )
    >>> # Cache is now prewarmed for these parameter combinations
"""

import asyncio
import inspect
import json
from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd
from pandas.util import hash_pandas_object

from dashboard_lego.core.exceptions import (
    AsyncSyncMismatchError,
    CacheError,
    DataLoadError,
)
from dashboard_lego.core.lambda_handlers import LambdaBuilder, LambdaTransformer
from dashboard_lego.utils.formatting import NumpyEncoder
from dashboard_lego.utils.hashing import get_stable_handler_id
from dashboard_lego.utils.logger import get_logger


class DataSource:
    """
    Base data source with stateless 2-stage pipeline.

    Pipeline stages (all via cache):
    1. Build (DataBuilder.build) - Load + Process
    2. Filter (DataFilter.filter) - Apply filters

    NO STORED STATE - data computed fresh each call via cache.
    NO ABSTRACT METHODS - fully concrete base class.

    :hierarchy: [Core | DataSources | DataSource]
    :relates-to:
     - motivated_by: "v0.15.0: 2-stage pipeline for semantic clarity"
     - implements: "class: 'DataSource' stateless"
     - uses: ["library: 'diskcache'", "class: 'DataBuilder'", "class: 'DataFilter'"]

    :rationale: "2-stage pipeline (Build → Filter) simpler than 3-stage"
    :contract:
     - pre: "data_builder and data_filter provided"
     - post: "get_processed_data(params) returns filtered data via cache"
     - invariant: "No stored data attributes, no abstract methods"

    :complexity: 7
    :decision_cache: "Chose 2-stage over 3-stage for semantic clarity"
    """

    # LLM:METADATA
    # :hierarchy: [Core | DataSources | DataSource | CacheRegistry]
    # :relates-to:
    #  - motivated_by: "Cache sharing prevents duplicate Stage1 builds when same builder reused across datasources created via with_transform_fn() [Contract-Fix-CacheSharing]"
    #  - implements: "Class-level cache registry for transparent cache reuse based on backend config matching"
    # :contract:
    #  - invariant: "Same backend config → same backend instance; All cache_backend=None → single shared disk cache"
    # :complexity: 2
    # :decision_cache: "Class-level dict registry over singleton pattern: simpler, transparent, no global state pollution [decision-cache-registry-001]"
    # LLM:END
    _cache_registry: Dict[str, Any] = {}

    def __init__(
        self,
        data_builder: Optional[Any] = None,
        data_transformer: Optional[Any] = None,
        param_classifier: Optional[Callable[[str], str]] = None,
        cache_dir: Optional[str] = None,
        cache_ttl: int = 300,
        cache_backend: Optional[Union[str, Any]] = None,
        build_fn: Optional[Callable[[Dict[str, Any]], pd.DataFrame]] = None,
        transform_fn: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,
        cache_prewarm_params: Optional[List[Dict[str, Any]]] = None,
        **kwargs,
    ):
        """
        Initialize datasource with 2-stage pipeline.

        :hierarchy: [Core | DataSources | DataSource | Initialization]
        :relates-to:
         - motivated_by: "v0.15.0: 2-stage pipeline configuration with optional lambda functions"
         - implements: "method: '__init__'"

        :contract:
         - pre: "data_builder, data_transformer, build_fn, transform_fn are optional"
         - post: "2-stage pipeline ready with handlers created from functions if provided"
         - stages: "Build → Transform"

        Args:
            data_builder: DataBuilder for stage 1 (load + process). If None and build_fn provided, creates LambdaBuilder.
            data_transformer: DataTransformer for stage 2 (filtering/aggregation). If None and transform_fn provided, creates LambdaTransformer.
            param_classifier: Routes params: 'build' or 'transform'. Default: 'build__' → 'build', 'transform__' → 'transform'.
            cache_dir: Directory for disk cache. If None, uses in-memory cache. Ignored if cache_backend is provided.
            cache_ttl: Time-to-live for cache entries in seconds.
            cache_backend: Cache backend to use. Can be:
                          - 'disk' or None: DiskCacheBackend (default, uses cache_dir)
                          - 'redis': RedisCacheBackend (localhost:6379)
                          - 'memory': InMemoryCacheBackend
                          - CacheBackend instance: Custom backend
            build_fn: Optional lambda function for simple data building: Dict[str, Any] → DataFrame.
                     If provided, creates LambdaBuilder automatically. Signature: lambda params: df
            transform_fn: Optional lambda function for simple data transformation: DataFrame → DataFrame.
                         If provided, creates LambdaTransformer automatically. Signature: lambda df: df
            cache_prewarm_params: Optional list of parameter dictionaries to prewarm cache during initialization.
                                 Each dict will be processed through the 2-stage pipeline to populate cache.
        """

        def _default_param_classifier(k: str) -> str:
            if "__" not in k:
                return "build", k
            category, key = k.split("__")
            if category not in ("build", "transform"):
                category = "build"
            return category, key

        self.logger = get_logger(__name__, DataSource)

        # LLM:METADATA
        # :hierarchy: [Core | DataSources | DataSource | CacheInitialization]
        # :relates-to:
        #  - motivated_by: "Contract 2: Support multiple cache backends (disk/Redis/memory)"
        #  - implements: "Cache backend initialization with pluggable backends"
        # :contract:
        #  - pre: "cache_backend is str or CacheBackend instance or None"
        #  - post: "self.cache is set to appropriate backend instance"
        #  - invariant: "Same backend config → reuses existing backend from registry"
        # :complexity: 5
        # LLM:END

        # Initialize cache backend
        try:
            from dashboard_lego.core.cache import (
                DiskCacheBackend,
                InMemoryCacheBackend,
                RedisCacheBackend,
            )
        except ImportError as e:
            self.logger.error(f"[DataSource|Init] Cache backend module not found: {e}")
            raise CacheError(f"Cache backend module not found: {e}") from e

        # Determine backend type and create instance
        if cache_backend is None or cache_backend == "disk":
            # Default: disk cache
            backend_key = f"disk:{cache_dir if cache_dir else '__in_memory__'}"
            if backend_key in DataSource._cache_registry:
                self.cache = DataSource._cache_registry[backend_key]
                self.logger.debug(f"[DataSource|Init] Reused cache | key={backend_key}")
            else:
                self.cache = DiskCacheBackend(directory=cache_dir, expire=cache_ttl)
                DataSource._cache_registry[backend_key] = self.cache
                self.logger.debug(
                    f"[DataSource|Init] Created DiskCacheBackend | key={backend_key}"
                )
        elif cache_backend == "redis":
            # Redis cache (default localhost)
            backend_key = "redis:localhost:6379:0"
            if backend_key in DataSource._cache_registry:
                self.cache = DataSource._cache_registry[backend_key]
                self.logger.debug(f"[DataSource|Init] Reused cache | key={backend_key}")
            else:
                try:
                    self.cache = RedisCacheBackend(expire=cache_ttl)
                    # Ping to validate connection
                    if hasattr(self.cache, "_redis"):
                        self.cache._redis.ping()
                    DataSource._cache_registry[backend_key] = self.cache
                    self.logger.debug(
                        f"[DataSource|Init] Created RedisCacheBackend | key={backend_key}"
                    )
                except Exception as e:
                    self.logger.error(
                        f"[DataSource|Init] Redis backend initialization failed: {e}"
                    )
                    raise CacheError(f"Redis connection failed: {e}") from e
        elif cache_backend == "memory":
            # In-memory cache
            backend_key = "memory:__shared__"
            if backend_key in DataSource._cache_registry:
                self.cache = DataSource._cache_registry[backend_key]
                self.logger.debug(f"[DataSource|Init] Reused cache | key={backend_key}")
            else:
                self.cache = InMemoryCacheBackend(expire=cache_ttl)
                DataSource._cache_registry[backend_key] = self.cache
                self.logger.debug(
                    f"[DataSource|Init] Created InMemoryCacheBackend | key={backend_key}"
                )
        else:
            # Custom backend instance
            self.cache = cache_backend
            backend_key = f"custom:{id(cache_backend)}"
            DataSource._cache_registry[backend_key] = self.cache
            self.logger.debug(
                f"[DataSource|Init] Using custom backend | key={backend_key}"
            )

        # Store backend config for cloning
        self.cache_backend = cache_backend
        self.cache_dir = cache_dir
        self.cache_ttl = cache_ttl

        # Import here to avoid circular imports
        from dashboard_lego.core.data_builder import DataBuilder
        from dashboard_lego.core.data_transformer import DataFilter

        # LLM:METADATA
        # :hierarchy: [Core | DataSources | DataSource | HandlerCreation]
        # :relates-to:
        #  - motivated_by: "Create handlers from lambda functions if provided in constructor"
        #  - implements: "Lambda handler creation logic in __init__"
        # :contract:
        #  - pre: "build_fn and transform_fn are optional callables"
        #  - post: "data_builder and data_transformer are set (either provided or created from functions)"
        # :complexity: 3
        # LLM:END
        # Create handlers from lambda functions if provided
        final_data_builder = data_builder
        final_data_transformer = data_transformer

        if build_fn is not None:
            # Create LambdaBuilder from build_fn (imported from lambda_handlers)
            final_data_builder = LambdaBuilder(build_fn, logger=self.logger)
            self.logger.debug("[DataSource|Init] Created LambdaBuilder from build_fn")

        if transform_fn is not None:
            # Create LambdaTransformer from transform_fn (imported from lambda_handlers)
            final_data_transformer = LambdaTransformer(transform_fn, logger=self.logger)
            self.logger.debug(
                "[DataSource|Init] Created LambdaTransformer from transform_fn"
            )

        # Initialize 2-stage pipeline
        self.data_builder = final_data_builder or DataBuilder(logger=self.logger)
        # Default to DataFilter instead of DataTransformer
        self.data_transformer = final_data_transformer or DataFilter(logger=self.logger)

        if param_classifier is None:
            param_classifier = _default_param_classifier
        self._param_classifier = param_classifier
        self.cache_dir = cache_dir  # Store original cache_dir for cloning
        self.cache_ttl = cache_ttl

        # NO stored state
        self._current_params: Dict[str, Any] = {}

        self.logger.info(
            f"[DataSource|Init] 2-stage pipeline ready | "
            f"builder={type(self.data_builder).__name__} | "
            f"transformer={type(self.data_transformer).__name__}"
        )

        # Prewarm cache if parameters provided
        if cache_prewarm_params:
            self._prewarm_cache(cache_prewarm_params)

    def _prewarm_cache(self, prewarm_list: List[Dict[str, Any]]) -> None:
        """
        Prewarm cache with provided parameter sets.

        :hierarchy: [Core | DataSources | DataSource | CachePrewarm]
        :relates-to:
         - motivated_by: "v0.15.0: Cache prewarming for faster first access"
         - implements: "method: '_prewarm_cache'"

        :contract:
         - pre: "prewarm_list is list of parameter dictionaries"
         - post: "Cache populated with Stage 1 (and Stage 2 if transform params present)"
         - invariant: "Errors are logged but do not stop prewarming process"

        :complexity: 3

        Args:
            prewarm_list: List of parameter dictionaries to prewarm cache with
        """
        self.logger.info(
            f"[DataSource|Prewarm] Starting cache prewarm with {len(prewarm_list)} parameter sets"
        )

        for idx, raw_params in enumerate(prewarm_list):
            try:
                _ = self.get_processed_data(raw_params)
                self.logger.debug(
                    f"[DataSource|Prewarm] Prewarmed item #{idx}: {raw_params}"
                )

            except Exception as e:
                self.logger.warning(f"[DataSource|Prewarm] Skipped item #{idx}: {e}")
                continue
        self.logger.info("[DataSource|Prewarm] Cache prewarm completed")

    def _get_cache_key(
        self, stage: str, params: Dict[str, Any], handler: Optional[Any] = None
    ) -> str:
        """
        Create cache key for specific pipeline stage.

        :hierarchy: [Core | DataSources | DataSource | Caching]
        :relates-to:
         - motivated_by: "Stage-specific cache keys INCLUDING handler instance for proper cache isolation"
         - implements: "method: '_get_cache_key'"

        :contract:
         - pre: "stage is valid string, params is dict"
         - post: "Returns stable cache key unique to stage + params + handler"
         - invariant: "Different builders/transformers get different cache keys; Same handler + params → same cache key"

        :decision_cache: "Use get_stable_handler_id for stable handler identification (Contract 3)"

        Args:
            stage: Pipeline stage ('build', 'transform')
            params: Parameters relevant to this stage
            handler: Optional handler (DataBuilder or DataTransformer) for handler-specific suffix

        Returns:
            Stable cache key string including handler identity
        """
        # Get handler-specific suffix if not provided
        if handler is None:
            if stage == "build":
                handler = self.data_builder
            elif stage == "transform":
                handler = self.data_transformer

        # Get stable handler ID using hashing utility (Contract 3)
        handler_suffix = ""
        if handler:
            handler_suffix = f"_{get_stable_handler_id(handler)}"

        # Build cache key
        # For in-memory cache (cache_dir is None), omit instance_id to allow sharing across instances
        if not params:
            return f"{stage}_default{handler_suffix}"
        # Normalize params to ensure pandas objects are hashed and complex types are serializable
        normalized_params = self._normalize_params_for_cache(params)
        params_json = json.dumps(normalized_params, sort_keys=True, cls=NumpyEncoder)
        # Include instance_id only when using a persistent cache (disk) to avoid collisions
        if self.cache_dir:
            instance_id = id(self)
            return f"{stage}_{params_json}_{instance_id}{handler_suffix}"
        else:
            return f"{stage}_{params_json}{handler_suffix}"

    def _normalize_params_for_cache(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Prepare params for cache key generation by:
        - Recursively traversing dict/list/tuple/set structures
        - Replacing pandas objects (DataFrame/Series/Index) with stable content hashes
        - Leaving other values as-is for JSON serialization via NumpyEncoder

        Returns a JSON-serializable structure representing the params and any pandas content.
        """

        def to_serializable(value: Any) -> Any:
            if (
                isinstance(value, pd.DataFrame)
                or isinstance(value, pd.Series)
                or isinstance(value, pd.Index)
            ):
                try:
                    series_hash = hash_pandas_object(value, index=True)
                    # Combine into a single deterministic integer
                    combined = int(series_hash.sum())
                except Exception:
                    # Fallback: for DataFrame, hash per-column series and combine
                    if isinstance(value, pd.DataFrame):
                        try:
                            col_hashes = []
                            for col in value.columns:
                                s_hash = hash_pandas_object(value[col], index=True)
                                col_hashes.append(int(s_hash.sum()))
                            combined = hash(tuple(col_hashes))
                        except Exception:
                            combined = hash(value.shape)
                    else:
                        combined = hash(len(value))
                return {"__pandas_hash__": combined}

            # Collections
            if isinstance(value, dict):
                return {k: to_serializable(v) for k, v in value.items()}
            if isinstance(value, (list, tuple)):
                return [to_serializable(v) for v in value]
            if isinstance(value, set):
                return sorted([to_serializable(v) for v in value])

            # Default: leave as-is (NumpyEncoder will handle numpy types)
            return value

        return to_serializable(params)

    def _get_or_build(self, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Get built data from cache or build fresh.

        Stage 1: Build (load + process).

        :hierarchy: [Core | DataSources | DataSource | Stage1]
        :contract:
         - pre: "params is dict"
         - post: "Returns complete built DataFrame"
         - cache_key: "Based on build params only"

        :complexity: 2

        Args:
            params: Build parameters

        Returns:
            Complete built DataFrame
        """
        if not params:
            self.logger.warning(f"[Stage1|Build] No params | params={params}")

        key = self._get_cache_key("build", params, self.data_builder)

        if key in self.cache:
            self.logger.debug("[Stage1|Build] Cache HIT")
            return self.cache[key]

        self.logger.info("[Stage1|Build] Cache MISS | building")

        # Call DataBuilder.build() - handles load + process
        built_data = self.data_builder.build(**params)

        if not isinstance(built_data, pd.DataFrame):
            raise DataLoadError(
                f"DataBuilder.build must return DataFrame, got {type(built_data)}"
            )

        self.cache[key] = built_data
        self.logger.info(f"[Stage1|Build] Complete | rows={len(built_data)}")
        return built_data

    def _get_or_transform(
        self, built_data: pd.DataFrame, params: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Get filtered data from cache or filter fresh.

        Stage 2: Filter.

        :hierarchy: [Core | DataSources | DataSource | Stage2]
        :contract:
         - pre: "built_data is DataFrame, params is dict"
         - post: "Returns filtered DataFrame"
         - cache_key: "Based on filter params + built_data content hash"

        :complexity: 2

        Args:
            built_data: Built DataFrame from stage 1
            params: Filter parameters

        Returns:
            Filtered DataFrame
        """
        if built_data is None or built_data.empty:
            self.logger.warning(
                f"[Stage2|Transform] No built_data | built_data={built_data}"
            )
            return built_data
        # Include built_data in cache key via hashed representation without mutating original params
        params_for_key = dict(params)
        params_for_key["__built_data__"] = built_data
        key = self._get_cache_key("transform", params_for_key, self.data_transformer)

        if key in self.cache:
            self.logger.debug("[Stage2|Filter] Cache HIT")
            return self.cache[key]

        self.logger.info("[Stage2|Transform] Cache MISS | transforming")
        filtered_data = self.data_transformer.transform(built_data, **params)

        if not isinstance(filtered_data, pd.DataFrame):
            raise DataLoadError(
                f"DataTransformer.transform must return DataFrame, got {type(filtered_data)}"
            )

        self.cache[key] = filtered_data
        self.logger.info(f"[Stage2|Transform] Complete | rows={len(filtered_data)}")
        return filtered_data

    def with_builder(self, builder: Union[Any, Callable]) -> "DataSource":
        """
        Return new datasource with replaced builder.

        Immutable pattern for flexible data pipeline composition.

        :hierarchy: [Core | DataSources | DataSource | WithBuilder]
        :contract:
         - pre: "builder is DataBuilder instance"
         - post: "Returns new DataSource (does NOT modify self)"

        :complexity: 2

        Args:
            builder: DataBuilder instance

        Returns:
            New DataSource with specified builder
        """
        return DataSource(
            data_builder=builder,
            data_transformer=self.data_transformer,
            param_classifier=self._param_classifier,
            cache_dir=self.cache_dir,
            cache_ttl=self.cache_ttl,
            cache_backend=self.cache_backend,  # Propagate backend for cache sharing
        )

    def with_builder_fn(
        self, build_fn: Callable[[Dict[str, Any]], pd.DataFrame]
    ) -> "DataSource":
        """
        Returns a new datasource instance with a lambda-based builder.

        Convenience factory for simple build logic without creating DataBuilder class.
        Symmetric to with_transform_fn() for consistency.

        :hierarchy: [Core | DataSources | DataSource | WithBuilderFn]
        :relates-to:
         - motivated_by: "v0.15.0: Symmetric API with with_transform_fn()"
         - implements: "method: 'with_builder_fn'"
         - uses: ["class: 'DataBuilder'"]

        :rationale: "Lambda-based builder for simple cases, avoiding class boilerplate"
        :contract:
         - pre: "build_fn is callable: Dict[str, Any] → DataFrame"
         - post: "Returns new DataSource with lambda builder"
         - invariant: "Original datasource unchanged (immutable)"

        :complexity: 2
        :decision_cache: "Symmetric with_builder_fn/with_transform_fn API for consistency"

        Args:
            build_fn: Function that builds DataFrame from params.
                     Signature: lambda params: df
                     Examples:
                     - lambda p: pd.read_csv(p['file_path'])
                     - lambda p: generate_sample_data(n=p.get('rows', 100))

        Returns:
            New DataSource instance with lambda builder.
            Original datasource is unchanged.

        Example:
            >>> # Create datasource with lambda builder
            >>> ds = DataSource().with_builder_fn(
            ...     lambda params: pd.read_csv('data.csv')
            ... )
            >>>
            >>> # Or with params
            >>> ds = DataSource().with_builder_fn(
            ...     lambda params: pd.read_csv(params.get('file', 'default.csv'))
            ... )
        """
        self.logger.debug(
            "[DataSource|WithBuilderFn] Creating datasource with lambda builder"
        )

        # Create LambdaBuilder from build_fn (imported from lambda_handlers)
        lambda_builder = LambdaBuilder(build_fn, logger=self.logger)

        self.logger.info("[DataSource|WithBuilderFn] Created lambda builder")

        return DataSource(
            data_builder=lambda_builder,
            data_transformer=self.data_transformer,
            param_classifier=self._param_classifier,
            cache_dir=self.cache_dir,
            cache_ttl=self.cache_ttl,
            cache_backend=self.cache_backend,  # Propagate backend for cache sharing
            # Explicitly pass None for lambda functions since we're setting data_builder
            build_fn=None,
            transform_fn=None,
        )

    def with_transformer(self, transformer: Any) -> "DataSource":
        """
        Return new datasource with replaced transformer.

        Immutable pattern for flexible data pipeline composition.

        :hierarchy: [Core | DataSources | DataSource | WithTransformer]
        :contract:
         - pre: "transformer is DataTransformer instance"
         - post: "Returns new DataSource (does NOT modify self)"

        :complexity: 2

        Args:
            transformer: DataTransformer instance

        Returns:
            New DataSource with specified transformer
        """
        return DataSource(
            data_builder=self.data_builder,
            data_transformer=transformer,
            param_classifier=self._param_classifier,
            cache_dir=self.cache_dir,
            cache_ttl=self.cache_ttl,
            cache_backend=self.cache_backend,  # Propagate backend for cache sharing
            # Explicitly pass None for lambda functions since we're setting data_transformer
            build_fn=None,
            transform_fn=None,
        )

    def with_transform_fn(
        self, transform_fn: Callable[[pd.DataFrame], pd.DataFrame]
    ) -> "DataSource":
        """
        Returns a new datasource instance with an additional transformation step
        chained AFTER the main data transformer.

        Factory method for creating specialized datasources with block-specific
        transformations. The new transformer is chained after the existing one,
        preserving the global filter → block transform order.

        :hierarchy: [Core | DataSources | DataSource | WithTransform]
        :relates-to:
         - motivated_by: "v0.15.0: Block-specific data transformations"
         - implements: "method: 'with_transform_fn'"
         - uses: ["class: 'ChainedTransformer'"]

        :rationale: "Immutable pattern creates specialized clone without modifying original"
        :contract:
         - pre: "transform_fn is callable: DataFrame → DataFrame"
         - post: "Returns new DataSource with chained transformer"
         - invariant: "Original datasource unchanged (immutable)"
         - cache: "New datasource has independent cache keys"

        :complexity: 4
        :decision_cache: "Use ChainedTransformer for global filter → block transform pipeline"

        Args:
            transform_fn: Function that transforms a DataFrame.
                         Signature: lambda df: df (no params needed)
                         Examples:
                         - lambda df: df.groupby('category').sum()
                         - lambda df: df.pivot_table(...)
                         - lambda df: df.query("price > 100")

        Returns:
            New DataSource instance with chained transformer.
            Original datasource is unchanged.

        Example:
            >>> # Original datasource with global filter
            >>> main_ds = DataSource(
            ...     data_builder=CSVBuilder("sales.csv"),
            ...     data_transformer=CategoryFilter()  # Global filter
            ... )
            >>>
            >>> # Create specialized datasource for aggregation
            >>> agg_ds = main_ds.with_transform_fn(
            ...     lambda df: df.groupby('category')['sales'].sum().reset_index()
            ... )
            >>>
            >>> # Original datasource unchanged, agg_ds has chained transformer
            >>> data = agg_ds.get_processed_data({'category': 'Electronics'})
            >>> # Flow: Build → CategoryFilter(category='Electronics') → GroupBy Aggregation
        """
        from dashboard_lego.core.data_transformer import ChainedTransformer

        self.logger.debug(
            "[DataSource|WithTransform] Creating specialized datasource clone"
        )

        # 1. Create a new transformer from the provided function (imported from lambda_handlers)
        block_specific_transformer = LambdaTransformer(transform_fn, logger=self.logger)

        # 2. Chain it with the existing global transformer
        chained_transformer = ChainedTransformer(
            self.data_transformer,  # Global filter (first)
            block_specific_transformer,  # Block transform (second)
            logger=self.logger,
        )

        self.logger.info(
            f"[DataSource|WithTransform] Chained: "
            f"{type(self.data_transformer).__name__} → LambdaTransformer"
        )

        # 3. Return a new datasource instance (clone) with the new chained transformer
        # Use stored cache_dir to ensure cache registry key matches parent
        return DataSource(
            data_builder=self.data_builder,
            data_transformer=chained_transformer,
            param_classifier=self._param_classifier,
            cache_dir=self.cache_dir,
            cache_ttl=self.cache_ttl,
            cache_backend=self.cache_backend,  # Propagate backend for cache sharing
            # Explicitly pass None for lambda functions since we're setting data_transformer
            build_fn=None,
            transform_fn=None,
        )

    def get_processed_data(
        self, params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Run 2-stage pipeline and return filtered data.

        :contract:
         - pre: "params is dict or None"
         - post: "Returns filtered DataFrame"
         - stages: "Build → Filter (2 stages)"
         - invariant: "Stateless (no stored data)"

        :complexity: 6

        Args:
            params: Parameters for build + filter

        Returns:
            Filtered DataFrame from 2-stage pipeline

        Raises:
            DataLoadError: If data loading/building fails
            CacheError: If cache operations fail (warning only, retries without cache)
            AsyncSyncMismatchError: If async build_fn used with sync method
        """
        params = params or {}
        self._current_params = params

        # Check for async/sync mismatch
        # For LambdaBuilder, check the underlying func attribute
        is_async_build = False
        if hasattr(self.data_builder, "func"):
            is_async_build = inspect.iscoroutinefunction(self.data_builder.func)
        else:
            is_async_build = inspect.iscoroutinefunction(self.data_builder.build)

        if is_async_build:
            raise AsyncSyncMismatchError(
                "Cannot call get_processed_data() with async build_fn. "
                "Use await get_processed_data_async() instead."
            )

        self.logger.info(f"[get_processed_data] Called | params={list(params.keys())}")

        try:
            # Classify params
            from dashboard_lego.core.processing_context import DataProcessingContext

            context = DataProcessingContext.from_params(params, self._param_classifier)

            # Stage 1: Build (load + process)
            built_data = self._get_or_build(context.preprocessing_params)

            # Stage 2: Filter
            filtered_data = self._get_or_transform(built_data, context.filtering_params)

            self.logger.info(
                f"[get_processed_data] Pipeline complete | rows={len(filtered_data)}"
            )
            return filtered_data

        except CacheError as e:
            self.logger.warning(f"[get_processed_data] Cache error: {e}")
            # Retry without cache
            self.logger.info("[get_processed_data] Retrying without cache")
            built_data = self.data_builder.build(**context.preprocessing_params)
            filtered_data = self.data_transformer.transform(
                built_data, **context.filtering_params
            )
            return filtered_data

        except DataLoadError:
            # Re-raise with context
            raise

        except Exception as e:
            # Wrap unexpected errors
            self.logger.error(
                f"[get_processed_data] Unexpected error: {e}", exc_info=True
            )
            raise DataLoadError(f"Data processing failed: {e}") from e

    async def get_processed_data_async(
        self, params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Async version of get_processed_data for use with async frameworks.

        Supports both async and sync build_fn:
        - If build_fn is async (coroutine), awaits it directly
        - If build_fn is sync, runs it in executor to avoid blocking event loop

        :contract:
         - pre: "params is dict or None"
         - post: "Returns filtered DataFrame (async)"
         - stages: "Build (async-aware) → Filter (sync for now)"
         - invariant: "Stateless (no stored data)"

        :complexity: 7

        Args:
            params: Parameters for build + filter

        Returns:
            Filtered DataFrame from 2-stage pipeline

        Raises:
            DataLoadError: If data loading/building fails
            CacheError: If cache operations fail (warning only, retries without cache)

        Example:
            >>> async def fetch_api_data(params):
            ...     async with httpx.AsyncClient() as client:
            ...         response = await client.get('/api/data')
            ...     return pd.DataFrame(response.json())
            >>>
            >>> ds = DataSource(build_fn=fetch_api_data)
            >>> df = await ds.get_processed_data_async({'limit': 100})
        """
        params = params or {}
        self._current_params = params

        self.logger.info(
            f"[get_processed_data_async] Called | params={list(params.keys())}"
        )

        try:
            # Classify params
            from dashboard_lego.core.processing_context import DataProcessingContext

            context = DataProcessingContext.from_params(params, self._param_classifier)

            # Stage 1: Build (async-aware)
            built_data = await self._get_or_build_async(context.preprocessing_params)

            # Stage 2: Filter (sync for now, per implementation plan)
            filtered_data = self._get_or_transform(built_data, context.filtering_params)

            self.logger.info(
                f"[get_processed_data_async] Pipeline complete | rows={len(filtered_data)}"
            )
            return filtered_data

        except CacheError as e:
            self.logger.warning(f"[get_processed_data_async] Cache error: {e}")
            # Retry without cache
            self.logger.info("[get_processed_data_async] Retrying without cache")

            # Detect if build function is async
            is_async_build = False
            if hasattr(self.data_builder, "func"):
                is_async_build = inspect.iscoroutinefunction(self.data_builder.func)
            else:
                is_async_build = inspect.iscoroutinefunction(self.data_builder.build)

            # Check if build is async
            if is_async_build:
                if hasattr(self.data_builder, "func"):
                    # LambdaBuilder: call func directly
                    built_data = await self.data_builder.func(
                        context.preprocessing_params
                    )
                else:
                    # Regular async DataBuilder
                    built_data = await self.data_builder.build(
                        **context.preprocessing_params
                    )
            else:
                # Run sync build in executor
                loop = asyncio.get_event_loop()

                def _sync_build_wrapper():
                    return self.data_builder.build(**context.preprocessing_params)

                built_data = await loop.run_in_executor(None, _sync_build_wrapper)

            filtered_data = self.data_transformer.transform(
                built_data, **context.filtering_params
            )
            return filtered_data

        except DataLoadError:
            # Re-raise with context
            raise

        except Exception as e:
            # Wrap unexpected errors
            self.logger.error(
                f"[get_processed_data_async] Unexpected error: {e}", exc_info=True
            )
            raise DataLoadError(f"Async data processing failed: {e}") from e

    async def _get_or_build_async(
        self, params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Async version of _get_or_build.

        Checks cache first, then builds data using async-aware logic:
        - If build_fn is async coroutine, awaits it
        - If build_fn is sync, runs in executor to avoid blocking

        Args:
            params: Build parameters

        Returns:
            Built DataFrame (from cache or fresh build)
        """
        params = params or {}
        cache_key = self._get_cache_key("build", params, self.data_builder)

        # Try cache first
        if cache_key in self.cache:
            self.logger.info(f"[_get_or_build_async] Cache HIT | key={cache_key[:50]}")
            return self.cache[cache_key]

        self.logger.info(f"[_get_or_build_async] Cache MISS | key={cache_key[:50]}")

        # Detect if build function is async
        # For LambdaBuilder, check the underlying func attribute
        is_async_build = False
        if hasattr(self.data_builder, "func"):
            # LambdaBuilder case - check the wrapped function
            is_async_build = inspect.iscoroutinefunction(self.data_builder.func)
        else:
            # Regular DataBuilder case - check the build method
            is_async_build = inspect.iscoroutinefunction(self.data_builder.build)

        # Build data (async-aware)
        if is_async_build:
            # Async build_fn - call directly and await
            self.logger.debug("[_get_or_build_async] Using async build_fn")
            if hasattr(self.data_builder, "func"):
                # LambdaBuilder: call func directly
                data = await self.data_builder.func(params)
            else:
                # Regular async DataBuilder
                data = await self.data_builder.build(**params)
        else:
            # Sync build_fn - run in executor
            # Need to wrap the call to unpack params as kwargs
            self.logger.debug("[_get_or_build_async] Using sync build_fn in executor")
            loop = asyncio.get_event_loop()

            def _sync_build_wrapper():
                return self.data_builder.build(**params)

            data = await loop.run_in_executor(None, _sync_build_wrapper)

        # Cache result
        try:
            self.cache.set(cache_key, data, expire=self.cache_ttl)
            self.logger.info(
                f"[_get_or_build_async] Cached | key={cache_key[:50]} | rows={len(data)}"
            )
        except Exception as e:
            self.logger.warning(f"[_get_or_build_async] Cache write failed: {e}")
            # Continue without caching

        return data
