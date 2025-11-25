"""
This module defines AsyncDataBuilder for asynchronous data building.

:hierarchy: [Core | Pipeline | AsyncDataBuilder]
:relates-to:
 - motivated_by: "Separate async capabilities from base DataBuilder for async frameworks"
 - implements: "class: 'AsyncDataBuilder'"
 - uses: ["class: 'DataBuilder'"]

:contract:
 - pre: "build_async() can handle both async and sync builders"
 - post: "build_async() runs building asynchronously"
 - invariant: "Inherits stateless building from DataBuilder"
"""

import asyncio
import logging
from typing import Optional

import pandas as pd

from dashboard_lego.core.data_builder import DataBuilder
from dashboard_lego.core.data_transformer import _apply_column_filters


class AsyncDataBuilder(DataBuilder):
    """
    Async version of DataBuilder for use with async frameworks.

    Supports both async and sync builders:
    - If builder is async (has build_async or async _build), awaits it directly
    - If builder is sync, runs it in executor to avoid blocking event loop

    :hierarchy: [Core | Pipeline | AsyncDataBuilder]
    :relates-to:
     - motivated_by: "Separate async logic from synchronous DataBuilder"
     - implements: "class: 'AsyncDataBuilder'"

    :contract:
     - pre: "builder can be async or sync DataBuilder instance"
     - post: "build_async() returns DataFrame asynchronously"
     - invariant: "Stateless (no stored data)"

    :complexity: 5

    Example:
        >>> async def fetch_data(params):
        ...     async with httpx.AsyncClient() as client:
        ...         response = await client.get('/api/data')
        ...     return pd.DataFrame(response.json())
        >>>
        >>> class AsyncBuilder(AsyncDataBuilder):
        ...     async def _build_async(self, **kwargs):
        ...         return await fetch_data(kwargs)
        >>>
        >>> builder = AsyncBuilder()
        >>> df = await builder.build_async(limit=100)
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize AsyncDataBuilder.

        :hierarchy: [Core | Pipeline | AsyncDataBuilder | Init]
        :contract:
         - pre: "logger optional"
         - post: "AsyncBuilder ready"

        Args:
            logger: Optional logger instance
        """
        super().__init__(logger=logger)
        self.logger.info("[AsyncDataBuilder|Init] Initialized")

    async def build_async(self, **kwargs) -> pd.DataFrame:
        """
        Build complete dataset asynchronously (load + process).

        :hierarchy: [Core | Pipeline | AsyncDataBuilder | BuildAsync]
        :contract:
         - pre: "kwargs contains construction parameters"
         - post: "Returns complete DataFrame ready for filtering (async)"
         - invariant: "Same params → same output"

        This method provides state protection wrapper around _build_async().
        Override _build_async() in subclass to implement async building logic.

        Args:
            **kwargs: Construction parameters
                     Examples: file paths, SQL queries, transformations

        Returns:
            Complete built DataFrame

        Raises:
            DataLoadError: If data loading/building fails

        Example:
            >>> class AsyncCSVBuilder(AsyncDataBuilder):
            ...     async def _build_async(self, **kwargs):
            ...         file_path = kwargs.get('file', 'data.csv')
            ...         # Simulate async file read
            ...         await asyncio.sleep(0.1)
            ...         return pd.read_csv(file_path)
            >>>
            >>> builder = AsyncCSVBuilder()
            >>> df = await builder.build_async(file='sales.csv')
        """
        # State protection: Reset any mutable state before building
        self._reset_mutable_state()

        # Call the actual async build implementation
        return await self._build_async(**kwargs)

    async def _build_async(self, **kwargs) -> pd.DataFrame:
        """
        Abstract async build implementation.

        Override this method in subclass to implement async building logic.
        This method is called by build_async() after state reset.

        :hierarchy: [Core | Pipeline | AsyncDataBuilder | BuildAsyncImplementation]
        :contract:
         - pre: "Mutable state has been reset"
         - post: "Returns complete DataFrame ready for filtering"
         - invariant: "Pure function (no side effects on instance state)"

        Args:
            **kwargs: Construction parameters

        Returns:
            Complete built DataFrame
        """
        self.logger.debug(
            "[AsyncDataBuilder|_BuildAsync] No-op builder (empty DataFrame)"
        )
        return pd.DataFrame()

    @classmethod
    def wrap_sync_builder(cls, builder: DataBuilder) -> "AsyncDataBuilder":
        """
        Wrap a synchronous DataBuilder to make it async-compatible.

        Creates an AsyncDataBuilder that wraps the sync builder and runs
        it in an executor when build_async() is called.

        :hierarchy: [Core | Pipeline | AsyncDataBuilder | WrapSync]
        :contract:
         - pre: "builder is DataBuilder instance"
         - post: "Returns AsyncDataBuilder that wraps sync builder"

        Args:
            builder: Synchronous DataBuilder to wrap

        Returns:
            AsyncDataBuilder that wraps the sync builder

        Example:
            >>> sync_builder = DataBuilder()
            >>> async_builder = AsyncDataBuilder.wrap_sync_builder(sync_builder)
            >>> df = await async_builder.build_async()
        """
        return _SyncBuilderWrapper(builder)


class _SyncBuilderWrapper(AsyncDataBuilder):
    """
    Internal wrapper that makes a sync DataBuilder async-compatible.

    Runs sync builder.build() in executor to avoid blocking event loop.
    """

    def __init__(self, builder: DataBuilder, logger: Optional[logging.Logger] = None):
        """
        Initialize wrapper with sync builder.

        Args:
            builder: Synchronous DataBuilder to wrap
            logger: Optional logger instance
        """
        super().__init__(logger=logger)
        self._wrapped_builder = builder

    async def _build_async(self, **kwargs) -> pd.DataFrame:
        """
        Run wrapped sync builder in executor.

        Args:
            **kwargs: Build parameters

        Returns:
            Built DataFrame
        """
        loop = asyncio.get_event_loop()

        def _sync_build_wrapper():
            return self._wrapped_builder.build(**kwargs)

        self.logger.debug(
            "[_SyncBuilderWrapper|_BuildAsync] Running sync builder in executor"
        )
        return await loop.run_in_executor(None, _sync_build_wrapper)


class AsyncDfHandler(AsyncDataBuilder):
    """
    Async version of DfHandler for DataFrame wrapping with filtering.

    Similar to DfHandler but with async support. Accepts DataFrame in
    constructor and applies filters during build_async() based on kwargs
    matching column names.

    :hierarchy: [Core | Pipeline | AsyncDataBuilder | AsyncDfHandler]
    :relates-to:
     - motivated_by: "Async version of DfHandler for async pipelines"
     - implements: "class: 'AsyncDfHandler'"

    :contract:
     - pre: "df is valid DataFrame"
     - post: "build_async() returns filtered DataFrame"
     - invariant: "Does not modify stored DataFrame"

    Example:
        >>> df = pd.DataFrame({'Category': ['A', 'B', 'A'], 'Value': [1, 2, 3]})
        >>> builder = AsyncDfHandler(df)
        >>> filtered = await builder.build_async(Category='A')
        >>> len(filtered)
        2
    """

    def __init__(self, df: pd.DataFrame, logger: Optional[logging.Logger] = None):
        """
        Initialize AsyncDfHandler with DataFrame.

        :hierarchy: [Core | Pipeline | AsyncDataBuilder | AsyncDfHandler | Initialization]
        :relates-to:
         - motivated_by: "Store DataFrame for async filtering during build"
         - implements: "method: '__init__'"

        :contract:
         - pre: "df is valid pandas DataFrame"
         - post: "AsyncDfHandler ready with stored DataFrame copy"

        Args:
            df: DataFrame to wrap and filter
            logger: Optional logger instance
        """
        super().__init__(logger=logger)
        if df is None or not isinstance(df, pd.DataFrame):
            raise ValueError("df must be a valid pandas DataFrame")
        if df.empty:
            self.logger.warning("[AsyncDfHandler] Empty DataFrame provided")

        self._df = df.copy()  # Copy to avoid external mutations
        self.logger.debug(
            f"[AsyncDfHandler|Init] Initialized | rows={len(df)} | cols={len(df.columns)}"
        )

    async def _build_async(self, **kwargs) -> pd.DataFrame:
        """
        Return filtered DataFrame based on kwargs matching column names.

        Applies column-based filtering using _apply_column_filters() function,
        same logic as DataFilter._transform(). Runs filtering in executor
        since _apply_column_filters is sync but pure.

        :hierarchy: [Core | Pipeline | AsyncDataBuilder | AsyncDfHandler | BuildAsync]
        :relates-to:
         - motivated_by: "Apply filters during async build stage using extracted filter logic"
         - implements: "method: '_build_async'"
         - uses: ["_apply_column_filters: column-based filtering function"]

        :contract:
         - pre: "kwargs contains filter parameters (key=column_name, value=filter_value)"
         - post: "Returns filtered DataFrame with rows matching all filter conditions"
         - invariant: "Does not modify stored DataFrame, uses copy for filtering"

        Args:
            **kwargs: Filter parameters matching column names

        Returns:
            Filtered DataFrame based on kwargs

        Example:
            >>> df = pd.DataFrame({'A': [1, 2, 3], 'B': ['x', 'y', 'z']})
            >>> builder = AsyncDfHandler(df)
            >>> filtered = await builder.build_async(A=2, B='y')
            >>> len(filtered)
            1
        """
        self.logger.debug(
            f"[AsyncDfHandler|_BuildAsync] Filtering DataFrame | "
            f"rows={len(self._df)} | filters={list(kwargs.keys())}"
        )

        # Run sync filtering in executor (pure function, safe to run async)
        loop = asyncio.get_event_loop()

        def _filter_wrapper():
            return _apply_column_filters(self._df, self.logger, **kwargs)

        return await loop.run_in_executor(None, _filter_wrapper)
