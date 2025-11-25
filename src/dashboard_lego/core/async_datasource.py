"""
This module defines the AsyncDataSource for asynchronous data processing.

:hierarchy: [Core | DataSources | AsyncDataSource]
:relates-to:
 - motivated_by: "v0.15.0 Refactor: Separate async capabilities from base DataSource"
 - implements: "class: 'AsyncDataSource'"
 - uses: ["class: 'DataSource'", "class: 'DataBuilder'", "class: 'DataTransformer'"]

:contract:
 - pre: "build_fn can be async or sync"
 - post: "get_processed_data_async() runs pipeline asynchronously"
 - invariant: "Inherits stateless 2-stage pipeline from DataSource"
"""

import asyncio
import inspect
from typing import Any, Dict, Optional

import pandas as pd

from dashboard_lego.core.datasource import DataSource
from dashboard_lego.core.exceptions import CacheError, DataLoadError
from dashboard_lego.core.processing_context import DataProcessingContext


class AsyncDataSource(DataSource):
    """
    Async version of DataSource for use with async frameworks.

    Supports both async and sync build_fn:
    - If build_fn is async (coroutine), awaits it directly
    - If build_fn is sync, runs it in executor to avoid blocking event loop

    :hierarchy: [Core | DataSources | AsyncDataSource]
    :relates-to:
     - motivated_by: "Separate async logic from synchronous DataSource"
     - implements: "class: 'AsyncDataSource'"

    :contract:
     - pre: "params is dict or None"
     - post: "Returns filtered DataFrame (async)"
     - stages: "Build (async-aware) → Filter (sync for now)"
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

    async def get_processed_data_async(
        self, params: Optional[Dict[str, Any]] = None
    ) -> pd.DataFrame:
        """
        Run 2-stage pipeline asynchronously.

        Args:
            params: Parameters for build + filter

        Returns:
            Filtered DataFrame from 2-stage pipeline

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

            # Stage 1: Build (async-aware)
            built_data = await self._get_or_build_async(context.preprocessing_params)

            # Stage 2: Filter (sync for now)
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
