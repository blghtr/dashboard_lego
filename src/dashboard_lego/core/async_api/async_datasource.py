"""
This module defines the AsyncDataSource for asynchronous data processing.

:hierarchy: [Core | DataSources | AsyncDataSource]
:relates-to:
 - motivated_by: "v0.15.0 Refactor: Separate async capabilities from base DataSource"
 - implements: "class: 'AsyncDataSource'"
 - uses: ["class: 'DataSource'", "class: 'AsyncDataBuilder'", "class: 'AsyncDataTransformer'"]

:contract:
 - pre: "build_fn/transform_fn can be async or sync, builders/transformers auto-wrapped"
 - post: "get_processed_data_async() runs pipeline asynchronously"
 - invariant: "Inherits stateless 2-stage pipeline from DataSource"
"""

from typing import Any, Dict, Optional

import pandas as pd

from dashboard_lego.core.async_api.async_data_builder import (
    AsyncDataBuilder,
    AsyncDfHandler,
)
from dashboard_lego.core.async_api.async_data_transformer import (
    AsyncDataFilter,
    AsyncDataTransformer,
)
from dashboard_lego.core.async_api.async_lambda_handlers import (
    AsyncLambdaBuilder,
    AsyncLambdaTransformer,
)
from dashboard_lego.core.data_builder import DataBuilder
from dashboard_lego.core.data_transformer import DataTransformer
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.core.exceptions import CacheError, DataLoadError
from dashboard_lego.core.processing_context import DataProcessingContext


class AsyncDataSource(DataSource):
    """
    Async version of DataSource for use with async frameworks.

    Supports both async and sync builders/transformers:
    - If AsyncDataBuilder/AsyncDataTransformer provided, uses them directly
    - If sync DataBuilder/DataTransformer provided, auto-wraps them in async wrappers
    - If build_fn/transform_fn provided, creates appropriate async handlers

    :hierarchy: [Core | DataSources | AsyncDataSource]
    :relates-to:
     - motivated_by: "Separate async logic from synchronous DataSource"
     - implements: "class: 'AsyncDataSource'"
     - uses: ["class: 'AsyncDataBuilder'", "class: 'AsyncDataTransformer'"]

    :contract:
     - pre: "params is dict or None"
     - post: "Returns filtered DataFrame (async)"
     - stages: "Build (async) → Transform (async)"
     - invariant: "Stateless (no stored data)"

    :complexity: 7

    Example:
        >>> async def fetch_api_data(params):
        ...     async with httpx.AsyncClient() as client:
        ...         response = await client.get('/api/data')
        ...     return pd.DataFrame(response.json())
        >>>
        >>> ds = AsyncDataSource(build_fn=fetch_api_data)
        >>> df = await ds.get_processed_data_async({'limit': 100})
    """

    def __init__(
        self,
        data_builder: Optional[Any] = None,
        data_transformer: Optional[Any] = None,
        param_classifier: Optional[Any] = None,
        cache_dir: Optional[str] = None,
        cache_ttl: int = 300,
        cache_backend: Optional[Any] = None,
        build_fn: Optional[Any] = None,
        transform_fn: Optional[Any] = None,
        cache_prewarm_params: Optional[Any] = None,
        df: Optional[pd.DataFrame] = None,
        **kwargs,
    ):
        """
        Initialize AsyncDataSource with async-aware handlers.

        Creates AsyncLambdaBuilder/AsyncLambdaTransformer from build_fn/transform_fn.
        Creates AsyncDfHandler from df. Auto-wraps sync builders/transformers if provided.

        Args:
            data_builder: AsyncDataBuilder or DataBuilder (auto-wrapped if sync)
            data_transformer: AsyncDataTransformer or DataTransformer (auto-wrapped if sync)
            build_fn: Async or sync lambda function (creates AsyncLambdaBuilder)
            transform_fn: Async or sync lambda function (creates AsyncLambdaTransformer)
            df: DataFrame (creates AsyncDfHandler)
            Other args: Same as DataSource.__init__
        """
        # Import logger utility
        from dashboard_lego.utils.logger import get_logger

        temp_logger = get_logger(__name__, AsyncDataSource)

        # Create async handlers from lambda functions or DataFrame
        final_data_builder = data_builder
        final_data_transformer = data_transformer

        if df is not None:
            # Create AsyncDfHandler from DataFrame (highest priority)
            if data_builder is not None:
                temp_logger.warning(
                    "[AsyncDataSource|Init] Both 'df' and 'data_builder' provided, using 'df' (AsyncDfHandler)"
                )
            if build_fn is not None:
                temp_logger.warning(
                    "[AsyncDataSource|Init] Both 'df' and 'build_fn' provided, using 'df' (AsyncDfHandler)"
                )
            final_data_builder = AsyncDfHandler(df, logger=None)  # Logger set by parent
            temp_logger.debug("[AsyncDataSource|Init] Created AsyncDfHandler from df")

        elif build_fn is not None:
            # Create AsyncLambdaBuilder from build_fn (second priority)
            if data_builder is not None:
                temp_logger.warning(
                    "[AsyncDataSource|Init] Both 'build_fn' and 'data_builder' provided, using 'build_fn' (AsyncLambdaBuilder)"
                )
            final_data_builder = AsyncLambdaBuilder(
                build_fn, logger=None
            )  # Logger set by parent
            temp_logger.debug(
                "[AsyncDataSource|Init] Created AsyncLambdaBuilder from build_fn"
            )

        if transform_fn is not None:
            # Create AsyncLambdaTransformer from transform_fn
            final_data_transformer = AsyncLambdaTransformer(
                transform_fn, logger=None
            )  # Logger set by parent
            temp_logger.debug(
                "[AsyncDataSource|Init] Created AsyncLambdaTransformer from transform_fn"
            )

        # Call parent __init__ with async handlers (or sync ones that will be auto-wrapped)
        super().__init__(
            data_builder=final_data_builder,
            data_transformer=final_data_transformer or AsyncDataFilter(logger=None),
            param_classifier=param_classifier,
            cache_dir=cache_dir,
            cache_ttl=cache_ttl,
            cache_backend=cache_backend,
            build_fn=None,  # Already handled above
            transform_fn=None,  # Already handled above
            cache_prewarm_params=cache_prewarm_params,
            df=None,  # Already handled above
            **kwargs,
        )

        # Override with async defaults if not provided
        if not isinstance(self.data_builder, AsyncDataBuilder):
            self.logger.debug(
                "[AsyncDataSource|Init] Wrapping sync builder in AsyncDataBuilder"
            )
            self.data_builder = AsyncDataBuilder.wrap_sync_builder(self.data_builder)

        if not isinstance(self.data_transformer, AsyncDataTransformer):
            self.logger.debug(
                "[AsyncDataSource|Init] Wrapping sync transformer in AsyncDataTransformer"
            )
            self.data_transformer = AsyncDataTransformer.wrap_sync_transformer(
                self.data_transformer
            )

    async def get_processed_data_async(
        self, params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Run 2-stage pipeline asynchronously.

        Uses AsyncDataBuilder and AsyncDataTransformer when available.
        Auto-wraps sync builders/transformers if needed.

        Args:
            params: Parameters for build + transform

        Returns:
            Transformed DataFrame from 2-stage pipeline

        Raises:
            DataLoadError: If data loading/building fails
            CacheError: If cache operations fail (warning only, retries without cache)
        """
        params = params or {}
        self._current_params = params

        self.logger.info(
            f"[get_processed_data_async] Called | params={list(params.keys())}"
        )

        try:
            # Classify params
            context = DataProcessingContext.from_params(params, self._param_classifier)

            # Stage 1: Build (async)
            built_data = await self._get_or_build_async(context.preprocessing_params)

            # Stage 2: Transform (async)
            filtered_data = await self._get_or_transform_async(
                built_data, context.filtering_params
            )

            self.logger.info(
                f"[get_processed_data_async] Pipeline complete | rows={len(filtered_data)}"
            )
            return filtered_data

        except CacheError as e:
            self.logger.warning(f"[get_processed_data_async] Cache error: {e}")
            # Retry without cache
            self.logger.info("[get_processed_data_async] Retrying without cache")

            # Get async builder/transformer (auto-wrap if needed)
            async_builder = self._get_async_builder()
            async_transformer = self._get_async_transformer()

            # Build without cache
            built_data = await async_builder.build_async(**context.preprocessing_params)

            # Transform without cache
            filtered_data = await async_transformer.transform_async(
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

    def _get_async_builder(self) -> AsyncDataBuilder:
        """
        Get async builder, auto-wrapping sync builder if needed.

        Returns:
            AsyncDataBuilder instance (wrapped if needed)
        """
        if isinstance(self.data_builder, AsyncDataBuilder):
            return self.data_builder
        elif isinstance(self.data_builder, DataBuilder):
            # Wrap sync builder
            self.logger.debug(
                "[AsyncDataSource] Wrapping sync DataBuilder in AsyncDataBuilder"
            )
            return AsyncDataBuilder.wrap_sync_builder(self.data_builder)
        else:
            raise DataLoadError(f"Unsupported builder type: {type(self.data_builder)}")

    def _get_async_transformer(self) -> AsyncDataTransformer:
        """
        Get async transformer, auto-wrapping sync transformer if needed.

        Returns:
            AsyncDataTransformer instance (wrapped if needed)
        """
        if isinstance(self.data_transformer, AsyncDataTransformer):
            return self.data_transformer
        elif isinstance(self.data_transformer, DataTransformer):
            # Wrap sync transformer
            self.logger.debug(
                "[AsyncDataSource] Wrapping sync DataTransformer in AsyncDataTransformer"
            )
            return AsyncDataTransformer.wrap_sync_transformer(self.data_transformer)
        else:
            raise DataLoadError(
                f"Unsupported transformer type: {type(self.data_transformer)}"
            )

    async def _get_or_build_async(
        self, params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Async version of _get_or_build.

        Checks cache first, then builds data using AsyncDataBuilder.

        Args:
            params: Build parameters

        Returns:
            Built DataFrame (from cache or fresh build)
        """
        params = params or {}
        async_builder = self._get_async_builder()
        cache_key = self._get_cache_key("build", params, self.data_builder)

        # Try cache first
        if cache_key in self.cache:
            self.logger.info(f"[_get_or_build_async] Cache HIT | key={cache_key[:50]}")
            return self.cache[cache_key]

        self.logger.info(f"[_get_or_build_async] Cache MISS | key={cache_key[:50]}")

        # Build data using async builder
        data = await async_builder.build_async(**params)

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

    async def _get_or_transform_async(
        self, built_data: pd.DataFrame, params: Dict[str, Any]
    ) -> pd.DataFrame:
        """
        Async version of _get_or_transform.

        Checks cache first, then transforms data using AsyncDataTransformer.

        Args:
            built_data: Built DataFrame from stage 1
            params: Transform parameters

        Returns:
            Transformed DataFrame (from cache or fresh transform)
        """
        if built_data is None or built_data.empty:
            self.logger.warning(
                f"[_get_or_transform_async] No built_data | built_data={built_data}"
            )
            return built_data

        async_transformer = self._get_async_transformer()

        # Include built_data in cache key via hashed representation
        params_for_key = dict(params)
        params_for_key["__built_data__"] = built_data
        key = self._get_cache_key("transform", params_for_key, self.data_transformer)

        if key in self.cache:
            self.logger.debug("[_get_or_transform_async] Cache HIT")
            return self.cache[key]

        self.logger.info("[_get_or_transform_async] Cache MISS | transforming")

        # Transform data using async transformer
        filtered_data = await async_transformer.transform_async(built_data, **params)

        if not isinstance(filtered_data, pd.DataFrame):
            raise DataLoadError(
                f"AsyncDataTransformer.transform_async must return DataFrame, got {type(filtered_data)}"
            )

        self.cache[key] = filtered_data
        self.logger.info(
            f"[_get_or_transform_async] Complete | rows={len(filtered_data)}"
        )
        return filtered_data
