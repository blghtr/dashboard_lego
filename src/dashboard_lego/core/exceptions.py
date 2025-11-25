"""
Custom exceptions for dashboard_lego.

:hierarchy: [Core | Exceptions]
:complexity: 1
"""

# LLM:METADATA
# :hierarchy: [Core | Exceptions]
# :relates-to:
#  - motivated_by: "Consolidation of exceptions into a single core module"
#  - implements: "Custom exception hierarchy for the entire library"
# :contract:
#  - pre: "Exceptions raised when specific error conditions occur"
#  - post: "Caller can catch and handle specific error types"
#  - invariant: "All exceptions inherit from DashboardLegoError base"
# :complexity: 1
# :decision_cache: "[decision-exc-002] Consolidated utils.exceptions into core.exceptions for better organization"
# LLM:END


class DashboardLegoError(Exception):
    """Base exception for all dashboard_lego errors."""

    pass


class DataSourceError(DashboardLegoError):
    """Raised when data source operations fail."""

    pass


class DataLoadError(DataSourceError):
    """
    Raised when data loading fails.

    Examples:
        - File not found
        - Database connection failed
        - API request failed
        - Invalid data format
    """

    pass


class CacheError(DataSourceError):
    """
    Raised when cache operations fail.

    Examples:
        - Cache directory not writable
        - Cache corruption
        - Serialization errors
    """

    pass


class DataTransformError(DataSourceError):
    """
    Raised when data transformation fails.

    Examples:
        - Invalid filter parameters
        - Column not found
        - Type conversion error
    """

    pass


class AsyncSyncMismatchError(DataSourceError):
    """
    Raised when async/sync methods are called incorrectly.

    Examples:
        - Calling sync method with async build_fn
        - Calling async method with sync-only context
    """

    pass


class BlockError(DashboardLegoError):
    """
    Raised when block operations fail.

    Examples:
        - Block initialization failed
        - Layout error
        - Update failed
    """

    pass


class StateError(DashboardLegoError):
    """
    Raised when state management operations fail.

    Examples:
        - State registration failed
        - Callback generation failed
    """

    pass


class ConfigurationError(DashboardLegoError):
    """
    Raised when configuration is invalid.

    Examples:
        - Invalid parameters
        - Missing required config
    """

    pass
