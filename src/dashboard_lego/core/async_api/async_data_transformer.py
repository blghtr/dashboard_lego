"""
This module defines AsyncDataTransformer for asynchronous data transformation.

:hierarchy: [Core | DataSources | AsyncDataTransformer]
:relates-to:
 - motivated_by: "Separate async capabilities from base DataTransformer for async frameworks"
 - implements: "class: 'AsyncDataTransformer'"
 - uses: ["class: 'DataTransformer'"]

:contract:
 - pre: "transform_async() can handle both async and sync transformers"
 - post: "transform_async() runs transformation asynchronously"
 - invariant: "Inherits stateless transformation from DataTransformer"
"""

import asyncio
import logging
from typing import Optional

import pandas as pd

from dashboard_lego.core.data_transformer import DataTransformer, _apply_column_filters


class AsyncDataTransformer(DataTransformer):
    """
    Async version of DataTransformer for use with async frameworks.

    Supports both async and sync transformers:
    - If transformer is async (has transform_async or async _transform), awaits it directly
    - If transformer is sync, runs it in executor to avoid blocking event loop

    :hierarchy: [Core | DataSources | AsyncDataTransformer]
    :relates-to:
     - motivated_by: "Separate async logic from synchronous DataTransformer"
     - implements: "class: 'AsyncDataTransformer'"

    :contract:
     - pre: "transformer can be async or sync DataTransformer instance"
     - post: "transform_async() returns DataFrame asynchronously"
     - invariant: "Input DataFrame not modified (copy-on-write)"

    :complexity: 5

    Example:
        >>> async def aggregate_data(df, **kwargs):
        ...     await asyncio.sleep(0.1)  # Simulate async operation
        ...     return df.groupby('category').sum()
        >>>
        >>> class AsyncAggregateTransformer(AsyncDataTransformer):
        ...     async def _transform_async(self, data, **kwargs):
        ...         return await aggregate_data(data, **kwargs)
        >>>
        >>> transformer = AsyncAggregateTransformer()
        >>> result = await transformer.transform_async(df)
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize AsyncDataTransformer.

        :hierarchy: [Core | DataSources | AsyncDataTransformer | Init]
        :contract:
         - pre: "logger optional"
         - post: "AsyncTransformer ready"

        Args:
            logger: Optional logger instance
        """
        super().__init__(logger=logger)
        self.logger.info("[AsyncDataTransformer|Init] Initialized")

    async def transform_async(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Transform data asynchronously based on params.

        :hierarchy: [Core | DataSources | AsyncDataTransformer | TransformAsync]
        :contract:
         - pre: "data is valid DataFrame"
         - post: "Returns transformed DataFrame (any shape/structure allowed) (async)"
         - invariant: "Does not modify input DataFrame"

        This method provides state protection wrapper around _transform_async().
        Override _transform_async() in subclass to implement async transformation logic.

        Args:
            data: Built DataFrame to transform
            **kwargs: Transformation parameters

        Returns:
            Transformed DataFrame (can be filtered, aggregated, reshaped, etc.)

        Raises:
            DataLoadError: If transformation fails

        Example:
            >>> class AsyncPriceFilter(AsyncDataTransformer):
            ...     async def _transform_async(self, data, **kwargs):
            ...         df = data.copy()
            ...         if 'min_price' in kwargs:
            ...             await asyncio.sleep(0.01)  # Simulate async
            ...             df = df[df['Price'] >= kwargs['min_price']]
            ...         return df
            >>>
            >>> transformer = AsyncPriceFilter()
            >>> result = await transformer.transform_async(df, min_price=100)
        """
        # State protection: Reset any mutable state before transforming
        self._reset_mutable_state()

        # Call the actual async transform implementation
        return await self._transform_async(data, **kwargs)

    async def _transform_async(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Abstract async transform implementation.

        Override this method in subclass to implement async transformation logic.
        This method is called by transform_async() after state reset.

        :hierarchy: [Core | DataSources | AsyncDataTransformer | TransformAsyncImplementation]
        :contract:
         - pre: "Mutable state has been reset"
         - post: "Returns transformed DataFrame (any shape/structure allowed)"
         - invariant: "Pure function (no side effects on instance state)"

        Args:
            data: Built DataFrame to transform
            **kwargs: Transformation parameters

        Returns:
            Transformed DataFrame (can be filtered, aggregated, reshaped, etc.)
        """
        self.logger.debug(
            f"[AsyncDataTransformer|_TransformAsync] Transforming {len(data)} rows "
            f"with kwargs: {list(kwargs.keys())}"
        )

        # Default: no transformation, return data as-is
        self.logger.debug(
            "[AsyncDataTransformer|_TransformAsync] Using default implementation "
            "(no transformation)"
        )
        return data

    @classmethod
    def wrap_sync_transformer(
        cls, transformer: DataTransformer
    ) -> "AsyncDataTransformer":
        """
        Wrap a synchronous DataTransformer to make it async-compatible.

        Creates an AsyncDataTransformer that wraps the sync transformer and runs
        it in an executor when transform_async() is called.

        :hierarchy: [Core | DataSources | AsyncDataTransformer | WrapSync]
        :contract:
         - pre: "transformer is DataTransformer instance"
         - post: "Returns AsyncDataTransformer that wraps sync transformer"

        Args:
            transformer: Synchronous DataTransformer to wrap

        Returns:
            AsyncDataTransformer that wraps the sync transformer

        Example:
            >>> sync_transformer = DataTransformer()
            >>> async_transformer = AsyncDataTransformer.wrap_sync_transformer(sync_transformer)
            >>> result = await async_transformer.transform_async(df)
        """
        return _SyncTransformerWrapper(transformer)


class _SyncTransformerWrapper(AsyncDataTransformer):
    """
    Internal wrapper that makes a sync DataTransformer async-compatible.

    Runs sync transformer.transform() in executor to avoid blocking event loop.
    """

    def __init__(
        self,
        transformer: DataTransformer,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize wrapper with sync transformer.

        Args:
            transformer: Synchronous DataTransformer to wrap
            logger: Optional logger instance
        """
        super().__init__(logger=logger)
        self._wrapped_transformer = transformer

    async def _transform_async(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Run wrapped sync transformer in executor.

        Args:
            data: Input DataFrame
            **kwargs: Transformation parameters

        Returns:
            Transformed DataFrame
        """
        loop = asyncio.get_event_loop()

        def _sync_transform_wrapper():
            return self._wrapped_transformer.transform(data, **kwargs)

        self.logger.debug(
            "[_SyncTransformerWrapper|_TransformAsync] Running sync transformer in executor"
        )
        return await loop.run_in_executor(None, _sync_transform_wrapper)


class AsyncDataFilter(AsyncDataTransformer):
    """
    Async version of DataFilter for filtering DataFrames based on column names.

    Filters DataFrame by matching params to column names. Uses the same
    _apply_column_filters() logic as DataFilter but runs it asynchronously.

    :hierarchy: [Core | DataSources | AsyncDataTransformer | AsyncDataFilter]
    :relates-to:
     - motivated_by: "Async version of DataFilter for async pipelines"
     - implements: "class: 'AsyncDataFilter'"

    :contract:
     - pre: "Receives DataFrame and params"
     - post: "Returns DataFrame filtered by params that match column names (async)"
     - invariant: "Ignores params that don't match columns or are None/'all'"

    Example:
        >>> df = pd.DataFrame({'Category': ['A', 'B', 'A'], 'Value': [1, 2, 3]})
        >>> filter = AsyncDataFilter()
        >>> filtered = await filter.transform_async(df, Category='A')
        >>> len(filtered)
        2
    """

    async def _transform_async(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Filter data by matching params to columns.

        Uses extracted _apply_column_filters() function for filtering logic.
        Runs filtering in executor since _apply_column_filters is sync but pure.

        Args:
            data: Input DataFrame
            **kwargs: Filter parameters

        Returns:
            Filtered DataFrame
        """
        loop = asyncio.get_event_loop()

        def _filter_wrapper():
            return _apply_column_filters(data, self.logger, **kwargs)

        return await loop.run_in_executor(None, _filter_wrapper)


class AsyncChainedTransformer(AsyncDataTransformer):
    """
    Async version of ChainedTransformer for sequential async transformations.

    Applies multiple transformers in sequence. First transformer receives params,
    second receives empty dict. Supports both async and sync transformers.

    :hierarchy: [Core | DataSources | AsyncDataTransformer | AsyncChainedTransformer]
    :relates-to:
     - motivated_by: "v0.15.0: Block-specific async transforms after global filters"
     - implements: "class: 'AsyncChainedTransformer'"
     - uses: ["class: 'AsyncDataTransformer'"]

    :contract:
     - pre: "transformer_1 and transformer_2 are AsyncDataTransformer instances (or sync wrapped)"
     - post: "transform_async() applies transformers sequentially (async)"
     - invariant: "First gets params, second gets empty dict"

    :complexity: 4
    :decision_cache: "Sequential async application preserves global filter → block transform order"

    Example:
        >>> global_filter = AsyncDataFilter()
        >>> block_transform = AsyncAggregateTransformer()
        >>> chained = AsyncChainedTransformer(global_filter, block_transform)
        >>> result = await chained.transform_async(data, {'category': 'A'})
        # First filters to category A, then aggregates
    """

    def __init__(
        self,
        transformer_1: AsyncDataTransformer,
        transformer_2: AsyncDataTransformer,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize AsyncChainedTransformer with two transformers.

        :hierarchy: [Core | DataSources | AsyncChainedTransformer | Initialization]
        :relates-to:
         - motivated_by: "Compose async transformation pipeline"
         - implements: "method: '__init__'"

        :contract:
         - pre: "Both transformers are AsyncDataTransformer instances"
         - post: "AsyncChainedTransformer ready to apply sequential async transforms"

        :complexity: 1

        Args:
            transformer_1: First transformer in chain (receives params)
            transformer_2: Second transformer in chain (receives empty dict)
            logger: Optional logger instance
        """
        super().__init__(logger=logger)
        self.transformer_1 = transformer_1
        self.transformer_2 = transformer_2
        self.logger.debug(
            f"[AsyncChainedTransformer|Init] Chain: {type(transformer_1).__name__} → "
            f"{type(transformer_2).__name__}"
        )

    async def _transform_async(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Apply transformers sequentially asynchronously.

        First transformer receives params (global filters), second receives
        empty dict (block-specific transform doesn't need params).

        :hierarchy: [Core | DataSources | AsyncChainedTransformer | TransformAsync]
        :relates-to:
         - motivated_by: "Sequential async transformation preserves order"
         - implements: "method: '_transform_async'"

        :contract:
         - pre: "data is valid DataFrame, params is dict"
         - post: "Returns result of transformer_2.transform_async(transformer_1.transform_async(data, params), {})"
         - invariant: "transformer_1 gets params, transformer_2 gets empty dict"

        :complexity: 3
        :decision_cache: "Params only for first transformer (global filter)"

        Args:
            data: Input DataFrame
            **kwargs: Parameters for first transformer (global filters)

        Returns:
            DataFrame after both transformations applied

        Example:
            >>> # Step 1: Apply global filter with params
            >>> filtered = await transformer_1.transform_async(data, {'category': 'A'})
            >>> # Step 2: Apply block-specific transform (no params)
            >>> final = await transformer_2.transform_async(filtered)
        """
        self.logger.debug(
            f"[AsyncChainedTransformer|_TransformAsync] Starting chain | "
            f"input_rows={len(data)} | params={list(kwargs.keys())}"
        )

        # Step 1: Apply the global filter with its params
        filtered_data = await self.transformer_1.transform_async(data, **kwargs)
        self.logger.debug(
            f"[AsyncChainedTransformer|_TransformAsync] After transformer_1: {len(filtered_data)} rows"
        )

        # Step 2: Apply the block-specific transform (it does not need params)
        final_data = await self.transformer_2.transform_async(filtered_data)
        self.logger.debug(
            f"[AsyncChainedTransformer|_TransformAsync] After transformer_2: {len(final_data)} rows"
        )

        return final_data
