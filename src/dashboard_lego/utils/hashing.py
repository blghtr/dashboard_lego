"""
Function hashing utilities for cache key generation.

Provides stable hash computation for lambda functions to enable
cache sharing across functionally identical handlers.

:hierarchy: [Utils | Hashing]
:relates-to:
 - motivated_by: "Contract 3: Persistent cache for functionally identical handlers"
 - implements: "Function hash computation via source code inspection"

:contract:
 - pre: "Receives callable function"
 - post: "Returns stable hash string or None if source unavailable"
 - invariant: "Same source code → same hash"

:complexity: 5
:decision_cache: "Use inspect.getsource + hashlib for stable function identity"
"""

import hashlib
import inspect
from typing import Callable, Optional


def get_function_hash(func: Callable) -> Optional[str]:
    """
    Compute stable hash of a function based on its source code.

    This enables cache sharing for functionally identical lambda functions
    (Contract 3: Persistent cache for identical handlers).

    :hierarchy: [Utils | Hashing | GetFunctionHash]
    :relates-to:
     - motivated_by: "Enable cache reuse for identical lambda functions"
     - implements: "function: 'get_function_hash'"

    :contract:
     - pre: "func is callable"
     - post: "Returns hash string if source available, None otherwise"
     - invariant: "Deterministic: same source → same hash"

    :complexity: 4
    :decision_cache: "Use source code + name + defaults for hash stability"

    Args:
        func: Callable function to hash

    Returns:
        SHA256 hash string of function source, or None if source unavailable

    Example:
        >>> f1 = lambda x: x * 2
        >>> f2 = lambda x: x * 2
        >>> # Note: In practice, lambdas defined separately have different source
        >>> # This utility is most useful for comparing stored function definitions
        >>> get_function_hash(f1) is not None
        True
    """
    try:
        # Get source code
        source = inspect.getsource(func)

        # Get function name (for non-lambda functions)
        name = getattr(func, "__name__", "<lambda>")

        # Get defaults if any
        try:
            sig = inspect.signature(func)
            defaults = str(
                [
                    (param.name, param.default)
                    for param in sig.parameters.values()
                    if param.default != inspect.Parameter.empty
                ]
            )
        except Exception:
            defaults = ""

        # Include module and qualname to prevent hash collisions across different codebases
        # This is critical for security when sharing Redis cache
        module = getattr(func, "__module__", "")
        qualname = getattr(func, "__qualname__", "")

        # Combine all components for unique hash
        hash_input = f"{source}|{module}|{qualname}|{name}|{defaults}"

        # Compute SHA256 hash
        hash_obj = hashlib.sha256(hash_input.encode("utf-8"))
        return hash_obj.hexdigest()

    except (OSError, TypeError):
        # Source not available (built-in, C extension, etc.)
        # Fall back to None - caller should use id() instead
        return None


def get_stable_handler_id(handler: any) -> str:
    """
    Get stable identifier for a handler (builder/transformer).

    For regular classes: uses class name hash
    For lambda wrappers: uses function hash if available, else id()

    :hierarchy: [Utils | Hashing | GetStableHandlerId]
    :relates-to:
     - motivated_by: "Provide stable cache keys for both classes and lambdas"
     - implements: "function: 'get_stable_handler_id'"

    :contract:
     - pre: "handler is DataBuilder or DataTransformer instance"
     - post: "Returns stable string identifier"
     - invariant: "Same handler type/function → same ID (when possible)"

    :complexity: 3

    Args:
        handler: Handler instance (DataBuilder or DataTransformer)

    Returns:
        Stable identifier string

    Example:
        >>> from dashboard_lego.core.lambda_handlers import LambdaBuilder
        >>> builder = LambdaBuilder(lambda p: pd.DataFrame())
        >>> id_str = get_stable_handler_id(builder)
        >>> isinstance(id_str, str)
        True
    """
    handler_type_name = type(handler).__name__

    # For lambda wrappers and chained transformers, try to use function hash
    if handler_type_name in (
        "LambdaBuilder",
        "LambdaTransformer",
        "ChainedTransformer",
    ):
        # Check if handler has get_function_hash method
        if hasattr(handler, "get_function_hash"):
            func_hash = handler.get_function_hash()
            if func_hash:
                return f"{handler_type_name}_{func_hash}"

        # Fall back to id() for lambdas/transformers without hash
        return f"{handler_type_name}_{id(handler)}"

    # For regular classes, use type hash
    try:
        return f"{handler_type_name}_{hash(type(handler))}"
    except Exception:
        # Final fallback
        return f"{handler_type_name}_{id(handler)}"
