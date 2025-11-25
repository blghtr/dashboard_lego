"""
Async lambda wrapper classes for AsyncDataBuilder and AsyncDataTransformer.

Provides simple async lambda-based handlers without requiring class inheritance.

:hierarchy: [Core | Pipeline | AsyncLambdaHandlers]
:relates-to:
 - motivated_by: "Async version of LambdaBuilder/LambdaTransformer for async pipelines"
 - implements: "Async lambda wrapper classes with function hash support for cache stability"

:contract:
 - pre: "Receives async or sync lambda functions conforming to builder/transformer signatures"
 - post: "Wraps lambdas in AsyncDataBuilder/AsyncDataTransformer interface"
 - invariant: "Function hash computed once at initialization for cache stability"

:complexity: 4
:decision_cache: "Centralized async lambda wrappers with hash support for Contract 3 (functional identity)"
"""

import inspect
import logging
from typing import Any, Callable, Dict, Optional

import pandas as pd

from dashboard_lego.core.async_api.async_data_builder import AsyncDataBuilder
from dashboard_lego.core.async_api.async_data_transformer import AsyncDataTransformer
from dashboard_lego.utils.hashing import get_function_hash


class AsyncLambdaBuilder(AsyncDataBuilder):
    """
    Wraps a simple lambda function as an AsyncDataBuilder.

    Supports both async and sync lambda functions:
    - If lambda is async (coroutine), awaits it directly
    - If lambda is sync, runs it in executor

    :hierarchy: [Core | Pipeline | AsyncLambdaBuilder]
    :relates-to:
     - motivated_by: "Wrap user lambda in AsyncDataBuilder interface"
     - implements: "class: 'AsyncLambdaBuilder'"

    :contract:
     - pre: "Receives lambda: params → df (can be async or sync)"
     - post: "Conforms to AsyncDataBuilder interface"
     - invariant: "Function hash computed for cache stability"

    Example:
        >>> # Async lambda
        >>> async def fetch_data(params):
        ...     async with httpx.AsyncClient() as client:
        ...         response = await client.get('/api/data')
        ...     return pd.DataFrame(response.json())
        >>>
        >>> builder = AsyncLambdaBuilder(fetch_data)
        >>> df = await builder.build_async(limit=100)
        >>>
        >>> # Sync lambda (runs in executor)
        >>> builder = AsyncLambdaBuilder(lambda p: pd.DataFrame({'x': [1, 2, 3]}))
        >>> df = await builder.build_async()
    """

    def __init__(
        self,
        func: Callable[[Dict[str, Any]], pd.DataFrame],
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ):
        """
        Initialize AsyncLambdaBuilder with a function.

        Args:
            func: Function that builds DataFrame from params.
                  Signature: lambda params: df (can be async or sync)
            logger: Optional logger instance
            **kwargs: Additional arguments passed to AsyncDataBuilder
        """
        super().__init__(logger=logger, **kwargs)
        self.func = func

        # Detect if function is async
        self._is_async = inspect.iscoroutinefunction(func)

        # Compute function hash for cache stability (Contract 3)
        self._func_hash: Optional[str] = get_function_hash(func)

        self.logger.debug(
            f"[AsyncLambdaBuilder|Init] Initialized | "
            f"is_async={self._is_async} | func_hash={self._func_hash[:20] if self._func_hash else None}"
        )

    async def _build_async(self, **kwargs) -> pd.DataFrame:
        """
        Apply the wrapped lambda function.

        If lambda is async, awaits it directly. If sync, runs in executor.

        Args:
            **kwargs: Build parameters passed as dict to lambda

        Returns:
            DataFrame produced by lambda function
        """
        if self._is_async:
            # Async lambda - await directly
            self.logger.debug("[AsyncLambdaBuilder|_BuildAsync] Using async lambda")
            return await self.func(kwargs)
        else:
            # Sync lambda - run in executor
            self.logger.debug(
                "[AsyncLambdaBuilder|_BuildAsync] Using sync lambda in executor"
            )
            import asyncio

            loop = asyncio.get_event_loop()

            def _sync_wrapper():
                return self.func(kwargs)

            return await loop.run_in_executor(None, _sync_wrapper)

    def get_function_hash(self) -> Optional[str]:
        """
        Get stable hash of wrapped function for cache key generation.

        Returns:
            Function hash string or None if not yet computed
        """
        return self._func_hash


class AsyncLambdaTransformer(AsyncDataTransformer):
    """
    Wraps a simple lambda function as an AsyncDataTransformer.

    Supports both async and sync lambda functions:
    - If lambda is async (coroutine), awaits it directly
    - If lambda is sync, runs it in executor

    :hierarchy: [Core | Pipeline | AsyncLambdaTransformer]
    :relates-to:
     - motivated_by: "Wrap user lambda in AsyncDataTransformer interface"
     - implements: "class: 'AsyncLambdaTransformer'"

    :contract:
     - pre: "Receives lambda: df → df (can be async or sync, optionally accepts **kwargs)"
     - post: "Conforms to AsyncDataTransformer interface"
     - invariant: "Function hash computed for cache stability"

    Example:
        >>> # Async lambda
        >>> async def aggregate_async(df, **kwargs):
        ...     await asyncio.sleep(0.1)
        ...     return df.groupby('category').sum()
        >>>
        >>> transformer = AsyncLambdaTransformer(aggregate_async)
        >>> result = await transformer.transform_async(df)
        >>>
        >>> # Sync lambda (runs in executor)
        >>> transformer = AsyncLambdaTransformer(lambda df: df[df['x'] > 1])
        >>> result = await transformer.transform_async(df)
    """

    def __init__(
        self,
        func: Callable[[pd.DataFrame], pd.DataFrame],
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ):
        """
        Initialize AsyncLambdaTransformer with a function.

        Args:
            func: Function that transforms DataFrame.
                  Signature: lambda df: df or lambda df, **kwargs: df (can be async or sync)
            logger: Optional logger instance
            **kwargs: Additional arguments passed to AsyncDataTransformer
        """
        super().__init__(logger=logger, **kwargs)
        self.func = func

        # Detect if function is async
        self._is_async = inspect.iscoroutinefunction(func)

        # Compute function hash for cache stability (Contract 3)
        self._func_hash: Optional[str] = get_function_hash(func)

        self.logger.debug(
            f"[AsyncLambdaTransformer|Init] Initialized | "
            f"is_async={self._is_async} | func_hash={self._func_hash[:20] if self._func_hash else None}"
        )

    async def _transform_async(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Apply the wrapped lambda function.

        If lambda is async, awaits it directly. If sync, runs in executor.
        Tries to pass kwargs to lambda if it accepts them.

        Args:
            data: Input DataFrame to transform
            **kwargs: Optional transformation parameters

        Returns:
            Transformed DataFrame
        """
        sig = inspect.signature(self.func)
        accepts_kwargs = len(sig.parameters) > 1

        if self._is_async:
            # Async lambda - await directly
            self.logger.debug(
                "[AsyncLambdaTransformer|_TransformAsync] Using async lambda"
            )
            if accepts_kwargs:
                # Lambda accepts kwargs: lambda df, **kwargs: ...
                return await self.func(data, **kwargs)
            else:
                # Lambda only accepts df: lambda df: ...
                return await self.func(data)
        else:
            # Sync lambda - run in executor
            self.logger.debug(
                "[AsyncLambdaTransformer|_TransformAsync] Using sync lambda in executor"
            )
            import asyncio

            loop = asyncio.get_event_loop()

            def _sync_wrapper():
                if accepts_kwargs:
                    return self.func(data, **kwargs)
                else:
                    return self.func(data)

            return await loop.run_in_executor(None, _sync_wrapper)

    def get_function_hash(self) -> Optional[str]:
        """
        Get stable hash of wrapped function for cache key generation.

        Returns:
            Function hash string or None if not yet computed
        """
        return self._func_hash
