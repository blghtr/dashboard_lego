"""
This module defines the base data source with stateless 2-stage pipeline.

:hierarchy: [Core | DataSources | BaseDataSource]
:relates-to:
 - motivated_by: "v0.15.0 Refactor: Stateless architecture with 2-stage pipeline"
 - implements: "interface: 'BaseDataSource' with stateless pipeline"
 - uses: ["library: 'diskcache'", "class: 'DataBuilder'", "class: 'DataFilter'"]

:contract:
 - pre: "data_builder and data_filter provided"
 - post: "get_processed_data(params) runs Build → Filter pipeline"
 - invariant: "NO stored data state, NO abstract methods, only cache"

:complexity: 7
:decision_cache: "2-stage pipeline (Build → Filter) for semantic clarity"
"""

import json
from typing import Any, Callable, Dict, Optional, Union

import pandas as pd
from diskcache import Cache

from dashboard_lego.utils.exceptions import CacheError, DataLoadError
from dashboard_lego.utils.formatting import NumpyEncoder
from dashboard_lego.utils.logger import get_logger


class BaseDataSource:
    """
    Base data source with stateless 2-stage pipeline.

    Pipeline stages (all via cache):
    1. Build (DataBuilder.build) - Load + Process
    2. Filter (DataFilter.filter) - Apply filters

    NO STORED STATE - data computed fresh each call via cache.
    NO ABSTRACT METHODS - fully concrete base class.

    :hierarchy: [Core | DataSources | BaseDataSource]
    :relates-to:
     - motivated_by: "v0.15.0: 2-stage pipeline for semantic clarity"
     - implements: "class: 'BaseDataSource' stateless"
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
    # :hierarchy: [Core | DataSources | BaseDataSource | CacheRegistry]
    # :relates-to:
    #  - motivated_by: "Cache sharing prevents duplicate Stage1 builds when same builder reused across datasources created via with_transform_fn() [Contract-Fix-CacheSharing]"
    #  - implements: "Class-level cache registry for transparent cache reuse based on cache_dir matching"
    # :contract:
    #  - invariant: "Same cache_dir → same Cache instance; All cache_dir=None → single shared in-memory cache"
    # :complexity: 2
    # :decision_cache: "Class-level dict registry over singleton pattern: simpler, transparent, no global state pollution [decision-cache-registry-001]"
    # LLM:END
    _cache_registry: Dict[str, Cache] = {}

    def __init__(
        self,
        data_builder: Optional[Any] = None,
        data_transformer: Optional[Any] = None,
        param_classifier: Optional[Callable[[str], str]] = None,
        cache_dir: Optional[str] = None,
        cache_ttl: int = 300,
        **kwargs,
    ):
        """
        Initialize datasource with 2-stage pipeline.

        :hierarchy: [Core | DataSources | BaseDataSource | Initialization]
        :relates-to:
         - motivated_by: "v0.15.0: 2-stage pipeline configuration"
         - implements: "method: '__init__'"

        :contract:
         - pre: "data_builder and data_transformer optional"
         - post: "2-stage pipeline ready"
         - stages: "Build → Transform"

        Args:
            data_builder: DataBuilder for stage 1 (load + process)
            data_transformer: DataTransformer for stage 2 (filtering/aggregation)
            param_classifier: Routes params: 'build' or 'transform'
                             Default: all params → 'build'
            cache_dir: Directory for disk cache. If None, uses in-memory cache.
            cache_ttl: Time-to-live for cache entries in seconds.
        """
        self.logger = get_logger(__name__, BaseDataSource)

        # LLM:METADATA
        # :hierarchy: [Core | DataSources | BaseDataSource | CacheInitialization]
        # :relates-to:
        #  - motivated_by: "Cache sharing prevents duplicate Stage1 builds by reusing Cache objects for matching cache_dir [Contract-Fix-CacheSharing]"
        #  - implements: "Cache registry lookup and reuse logic in __init__"
        # :contract:
        #  - pre: "cache_dir is str or None, cache_ttl is int"
        #  - post: "self.cache is set to shared or new Cache instance"
        #  - invariant: "Same cache_dir → reuses existing Cache from registry; Different cache_dir → creates new Cache"
        # :complexity: 3
        # LLM:END

        # Initialize cache with transparent sharing
        cache_key = cache_dir if cache_dir else "__in_memory__"

        try:
            if cache_key in BaseDataSource._cache_registry:
                # Reuse existing cache for same cache_dir
                self.cache = BaseDataSource._cache_registry[cache_key]
                self.logger.debug(
                    f"[BaseDataSource|Init] Reused cache | key={cache_key}"
                )
            else:
                # Create new cache and register it
                self.cache = Cache(directory=cache_dir, expire=cache_ttl)
                BaseDataSource._cache_registry[cache_key] = self.cache
                self.logger.debug(
                    f"[BaseDataSource|Init] Created new cache | key={cache_key}"
                )
        except Exception as e:
            self.logger.error(f"[BaseDataSource|Init] Cache failed: {e}")
            raise CacheError(f"Cache initialization failed: {e}") from e

        # Import here to avoid circular imports
        from dashboard_lego.core.data_builder import DataBuilder
        from dashboard_lego.core.data_transformer import DataTransformer

        # Initialize 2-stage pipeline
        self.data_builder = data_builder or DataBuilder(logger=self.logger)
        self.data_transformer = data_transformer or DataTransformer(logger=self.logger)
        self.param_classifier = param_classifier
        self.cache_dir = cache_dir  # Store original cache_dir for cloning
        self.cache_ttl = cache_ttl

        # NO stored state
        self._current_params: Dict[str, Any] = {}

        self.logger.info(
            f"[BaseDataSource|Init] 2-stage pipeline ready | "
            f"builder={type(self.data_builder).__name__} | "
            f"transformer={type(self.data_transformer).__name__}"
        )

    def _get_cache_key(self, stage: str, params: Dict[str, Any]) -> str:
        """
        Create cache key for specific pipeline stage.

        :hierarchy: [Core | DataSources | BaseDataSource | Caching]
        :relates-to:
         - motivated_by: "Stage-specific cache keys INCLUDING handler instance"
         - implements: "method: '_get_cache_key'"

        :contract:
         - pre: "stage is valid string, params is dict"
         - post: "Returns stable cache key unique to stage + params + handler"
         - invariant: "Different builders/transformers get different cache keys; Same cache_dir → shared Cache object"

        :decision_cache: "Use hash(type(handler)) for classes, id() for lambdas"

        Args:
            stage: Pipeline stage ('built', 'filtered')
            params: Parameters relevant to this stage

        Returns:
            Stable cache key string including handler identity
        """
        # Get handler-specific suffix
        if stage == "built":
            handler = self.data_builder
        elif stage == "filtered":
            handler = self.data_transformer
        else:
            handler = None

        # Hash handler type (stable for classes, unique for lambda instances)
        handler_suffix = ""
        if handler:
            # For ChainedTransformer or LambdaTransformer: use id() since each instance is unique
            # For regular classes: use hash(type) for stability
            handler_type_name = type(handler).__name__
            if handler_type_name in ("LambdaTransformer", "ChainedTransformer"):
                handler_suffix = f"_{id(handler)}"
            else:
                try:
                    handler_suffix = f"_{hash(type(handler))}"
                except Exception:
                    handler_suffix = f"_{id(handler)}"

        # Build cache key
        if not params:
            return f"{stage}_default{handler_suffix}"
        params_json = json.dumps(params, sort_keys=True, cls=NumpyEncoder)
        return f"{stage}_{params_json}{handler_suffix}"

    def _get_or_build(self, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Get built data from cache or build fresh.

        Stage 1: Build (load + process).

        :hierarchy: [Core | DataSources | BaseDataSource | Stage1]
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
        key = self._get_cache_key("built", params)

        if key in self.cache:
            self.logger.debug("[Stage1|Build] Cache HIT")
            return self.cache[key]

        self.logger.info("[Stage1|Build] Cache MISS | building")

        # Call DataBuilder.build() - handles load + process
        built_data = self.data_builder.build(params)

        if not isinstance(built_data, pd.DataFrame):
            raise DataLoadError(
                f"DataBuilder.build must return DataFrame, got {type(built_data)}"
            )

        self.cache[key] = built_data
        self.logger.info(f"[Stage1|Build] Complete | rows={len(built_data)}")
        return built_data

    def _get_or_filter(
        self, built_data: pd.DataFrame, params: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Get filtered data from cache or filter fresh.

        Stage 2: Filter.

        :hierarchy: [Core | DataSources | BaseDataSource | Stage2]
        :contract:
         - pre: "built_data is DataFrame, params is dict"
         - post: "Returns filtered DataFrame"
         - cache_key: "Based on filter params only"

        :complexity: 2

        Args:
            built_data: Built DataFrame from stage 1
            params: Filter parameters

        Returns:
            Filtered DataFrame
        """
        key = self._get_cache_key("filtered", params)

        if key in self.cache:
            self.logger.debug("[Stage2|Filter] Cache HIT")
            return self.cache[key]

        self.logger.info("[Stage2|Transform] Cache MISS | transforming")
        filtered_data = self.data_transformer.transform(built_data, params)

        if not isinstance(filtered_data, pd.DataFrame):
            raise DataLoadError(
                f"DataTransformer.transform must return DataFrame, got {type(filtered_data)}"
            )

        self.cache[key] = filtered_data
        self.logger.info(f"[Stage2|Transform] Complete | rows={len(filtered_data)}")
        return filtered_data

    def with_builder(self, builder: Union[Any, Callable]) -> "BaseDataSource":
        """
        Return new datasource with replaced builder.

        Immutable pattern for flexible data pipeline composition.

        :hierarchy: [Core | DataSources | BaseDataSource | WithBuilder]
        :contract:
         - pre: "builder is DataBuilder instance"
         - post: "Returns new BaseDataSource (does NOT modify self)"

        :complexity: 2

        Args:
            builder: DataBuilder instance

        Returns:
            New BaseDataSource with specified builder
        """
        return BaseDataSource(
            data_builder=builder,
            data_transformer=self.data_transformer,
            param_classifier=self.param_classifier,
            cache_dir=self.cache_dir,  # Use original cache_dir for cache sharing
            cache_ttl=self.cache_ttl,
        )

    def with_builder_fn(
        self, build_fn: Callable[[Dict[str, Any]], pd.DataFrame]
    ) -> "BaseDataSource":
        """
        Returns a new datasource instance with a lambda-based builder.

        Convenience factory for simple build logic without creating DataBuilder class.
        Symmetric to with_transform_fn() for consistency.

        :hierarchy: [Core | DataSources | BaseDataSource | WithBuilderFn]
        :relates-to:
         - motivated_by: "v0.15.0: Symmetric API with with_transform_fn()"
         - implements: "method: 'with_builder_fn'"
         - uses: ["class: 'DataBuilder'"]

        :rationale: "Lambda-based builder for simple cases, avoiding class boilerplate"
        :contract:
         - pre: "build_fn is callable: Dict[str, Any] → DataFrame"
         - post: "Returns new BaseDataSource with lambda builder"
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
            New BaseDataSource instance with lambda builder.
            Original datasource is unchanged.

        Example:
            >>> # Create datasource with lambda builder
            >>> ds = BaseDataSource().with_builder_fn(
            ...     lambda params: pd.read_csv('data.csv')
            ... )
            >>>
            >>> # Or with params
            >>> ds = BaseDataSource().with_builder_fn(
            ...     lambda params: pd.read_csv(params.get('file', 'default.csv'))
            ... )
        """
        from dashboard_lego.core.data_builder import DataBuilder

        self.logger.debug(
            "[BaseDataSource|WithBuilderFn] Creating datasource with lambda builder"
        )

        # Wrap lambda in DataBuilder
        class LambdaBuilder(DataBuilder):
            """
            Wraps a simple lambda function as a DataBuilder.

            :hierarchy: [Core | DataSources | LambdaBuilder]
            :relates-to:
             - motivated_by: "Wrap user lambda in DataBuilder interface"
             - implements: "class: 'LambdaBuilder'"

            :contract:
             - pre: "Receives lambda: params → df"
             - post: "Conforms to DataBuilder interface"
            """

            def __init__(
                self, func: Callable[[Dict[str, Any]], pd.DataFrame], **kwargs
            ):
                super().__init__(**kwargs)
                self.func = func

            def build(self, params: Dict[str, Any]) -> pd.DataFrame:
                """Apply the wrapped lambda function."""
                return self.func(params)

        lambda_builder = LambdaBuilder(build_fn, logger=self.logger)

        self.logger.info("[BaseDataSource|WithBuilderFn] Created lambda builder")

        return BaseDataSource(
            data_builder=lambda_builder,
            data_transformer=self.data_transformer,
            param_classifier=self.param_classifier,
            cache_dir=self.cache_dir,  # Use original cache_dir for cache sharing
            cache_ttl=self.cache_ttl,
        )

    def with_transformer(self, transformer: Any) -> "BaseDataSource":
        """
        Return new datasource with replaced transformer.

        Immutable pattern for flexible data pipeline composition.

        :hierarchy: [Core | DataSources | BaseDataSource | WithTransformer]
        :contract:
         - pre: "transformer is DataTransformer instance"
         - post: "Returns new BaseDataSource (does NOT modify self)"

        :complexity: 2

        Args:
            transformer: DataTransformer instance

        Returns:
            New BaseDataSource with specified transformer
        """
        return BaseDataSource(
            data_builder=self.data_builder,
            data_transformer=transformer,
            param_classifier=self.param_classifier,
            cache_dir=self.cache_dir,  # Use original cache_dir for cache sharing
            cache_ttl=self.cache_ttl,
        )

    def with_transform_fn(
        self, transform_fn: Callable[[pd.DataFrame], pd.DataFrame]
    ) -> "BaseDataSource":
        """
        Returns a new datasource instance with an additional transformation step
        chained AFTER the main data transformer.

        Factory method for creating specialized datasources with block-specific
        transformations. The new transformer is chained after the existing one,
        preserving the global filter → block transform order.

        :hierarchy: [Core | DataSources | BaseDataSource | WithTransform]
        :relates-to:
         - motivated_by: "v0.15.0: Block-specific data transformations"
         - implements: "method: 'with_transform_fn'"
         - uses: ["class: 'ChainedTransformer'"]

        :rationale: "Immutable pattern creates specialized clone without modifying original"
        :contract:
         - pre: "transform_fn is callable: DataFrame → DataFrame"
         - post: "Returns new BaseDataSource with chained transformer"
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
            New BaseDataSource instance with chained transformer.
            Original datasource is unchanged.

        Example:
            >>> # Original datasource with global filter
            >>> main_ds = BaseDataSource(
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
        from dashboard_lego.core.data_transformer import (
            ChainedTransformer,
            DataTransformer,
        )

        self.logger.debug(
            "[BaseDataSource|WithTransform] Creating specialized datasource clone"
        )

        # 1. Create a new transformer from the provided function
        class LambdaTransformer(DataTransformer):
            """
            Wraps a simple lambda function as a DataTransformer.

            :hierarchy: [Core | DataSources | LambdaTransformer]
            :relates-to:
             - motivated_by: "Wrap user lambda in DataTransformer interface"
             - implements: "class: 'LambdaTransformer'"

            :contract:
             - pre: "Receives simple lambda: df → df"
             - post: "Conforms to DataTransformer interface"
             - invariant: "Ignores params (block transforms don't need them)"
            """

            def __init__(self, func: Callable[[pd.DataFrame], pd.DataFrame], **kwargs):
                super().__init__(**kwargs)
                self.func = func

            def transform(
                self, data: pd.DataFrame, params: Dict[str, Any]
            ) -> pd.DataFrame:
                """Apply the wrapped lambda function."""
                # Block-specific transforms don't use params
                return self.func(data)

        block_specific_transformer = LambdaTransformer(transform_fn, logger=self.logger)

        # 2. Chain it with the existing global transformer
        chained_transformer = ChainedTransformer(
            self.data_transformer,  # Global filter (first)
            block_specific_transformer,  # Block transform (second)
            logger=self.logger,
        )

        self.logger.info(
            f"[BaseDataSource|WithTransform] Chained: "
            f"{type(self.data_transformer).__name__} → LambdaTransformer"
        )

        # 3. Return a new datasource instance (clone) with the new chained transformer
        # Use stored cache_dir to ensure cache registry key matches parent
        return BaseDataSource(
            data_builder=self.data_builder,
            data_transformer=chained_transformer,
            param_classifier=self.param_classifier,
            cache_dir=self.cache_dir,  # Use original cache_dir for cache sharing
            cache_ttl=self.cache_ttl,
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
        """
        params = params or {}
        self._current_params = params

        self.logger.info(f"[get_processed_data] Called | params={list(params.keys())}")

        try:
            # Classify params
            from dashboard_lego.core.processing_context import DataProcessingContext

            context = DataProcessingContext.from_params(params, self.param_classifier)

            # Stage 1: Build (load + process)
            built_data = self._get_or_build(context.preprocessing_params)

            # Stage 2: Filter
            filtered_data = self._get_or_filter(built_data, context.filtering_params)

            self.logger.info(
                f"[get_processed_data] Pipeline complete | rows={len(filtered_data)}"
            )
            return filtered_data

        except Exception as e:
            self.logger.error(f"[get_processed_data] Error: {e}", exc_info=True)
            return pd.DataFrame()
