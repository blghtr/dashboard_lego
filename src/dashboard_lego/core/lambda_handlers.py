"""
Lambda wrapper classes for DataBuilder and DataTransformer.

Provides simple lambda-based handlers without requiring class inheritance.

:hierarchy: [Core | Pipeline | LambdaHandlers]
:relates-to:
 - motivated_by: "v0.15.0: Eliminate code duplication - LambdaBuilder/LambdaTransformer defined 3x in datasource.py"
 - implements: "Lambda wrapper classes with function hash support for cache stability"

:contract:
 - pre: "Receives lambda functions conforming to builder/transformer signatures"
 - post: "Wraps lambdas in DataBuilder/DataTransformer interface"
 - invariant: "Function hash computed once at initialization for cache key stability"

:complexity: 4
:decision_cache: "Centralized lambda wrappers with hash support for Contract 3 (functional identity)"
"""

import logging
from typing import Any, Callable, Dict, Optional

import pandas as pd

from dashboard_lego.core.data_builder import DataBuilder
from dashboard_lego.core.data_transformer import DataTransformer


class LambdaBuilder(DataBuilder):
    """
    Wraps a simple lambda function as a DataBuilder.

    :hierarchy: [Core | Pipeline | LambdaBuilder]
    :relates-to:
     - motivated_by: "Wrap user lambda in DataBuilder interface"
     - implements: "class: 'LambdaBuilder'"

    :contract:
     - pre: "Receives lambda: params → df"
     - post: "Conforms to DataBuilder interface"
     - invariant: "Function hash computed for cache stability"

    Example:
        >>> builder = LambdaBuilder(lambda p: pd.DataFrame({'x': [1, 2, 3]}))
        >>> df = builder.build()
    """

    def __init__(
        self,
        func: Callable[[Dict[str, Any]], pd.DataFrame],
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ):
        """
        Initialize LambdaBuilder with a function.

        Args:
            func: Function that builds DataFrame from params.
                  Signature: lambda params: df
            logger: Optional logger instance
            **kwargs: Additional arguments passed to DataBuilder
        """
        super().__init__(logger=logger, **kwargs)
        self.func = func

        # Compute function hash for cache stability (Contract 3)
        from dashboard_lego.utils.hashing import get_function_hash

        self._func_hash: Optional[str] = get_function_hash(func)

    def _build(self, **kwargs) -> pd.DataFrame:
        """
        Apply the wrapped lambda function.

        Args:
            **kwargs: Build parameters passed as dict to lambda

        Returns:
            DataFrame produced by lambda function
        """
        # Call user lambda with kwargs dict
        return self.func(kwargs)

    def get_function_hash(self) -> Optional[str]:
        """
        Get stable hash of wrapped function for cache key generation.

        Returns:
            Function hash string or None if not yet computed
        """
        return self._func_hash


class LambdaTransformer(DataTransformer):
    """
    Wraps a simple lambda function as a DataTransformer.

    :hierarchy: [Core | Pipeline | LambdaTransformer]
    :relates-to:
     - motivated_by: "Wrap user lambda in DataTransformer interface"
     - implements: "class: 'LambdaTransformer'"

    :contract:
     - pre: "Receives lambda: df → df (optionally accepts **kwargs)"
     - post: "Conforms to DataTransformer interface"
     - invariant: "Function hash computed for cache stability"

    Example:
        >>> transformer = LambdaTransformer(lambda df: df[df['x'] > 1])
        >>> result = transformer.transform(pd.DataFrame({'x': [1, 2, 3]}))
    """

    def __init__(
        self,
        func: Callable[[pd.DataFrame], pd.DataFrame],
        logger: Optional[logging.Logger] = None,
        **kwargs,
    ):
        """
        Initialize LambdaTransformer with a function.

        Args:
            func: Function that transforms DataFrame.
                  Signature: lambda df: df or lambda df, **kwargs: df
            logger: Optional logger instance
            **kwargs: Additional arguments passed to DataTransformer
        """
        super().__init__(logger=logger, **kwargs)
        self.func = func

        # Compute function hash for cache stability (Contract 3)
        from dashboard_lego.utils.hashing import get_function_hash

        self._func_hash: Optional[str] = get_function_hash(func)

    def _transform(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Apply the wrapped lambda function.

        Args:
            data: Input DataFrame to transform
            **kwargs: Optional transformation parameters

        Returns:
            Transformed DataFrame
        """
        # Try to pass kwargs to lambda if it accepts them
        # Otherwise just pass the DataFrame
        import inspect

        sig = inspect.signature(self.func)

        if len(sig.parameters) > 1:
            # Lambda accepts kwargs: lambda df, **kwargs: ...
            return self.func(data, **kwargs)
        else:
            # Lambda only accepts df: lambda df: ...
            return self.func(data)

    def get_function_hash(self) -> Optional[str]:
        """
        Get stable hash of wrapped function for cache key generation.

        Returns:
            Function hash string or None if not yet computed
        """
        return self._func_hash
