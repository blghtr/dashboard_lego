"""
Custom exceptions for dashboard_lego.

This module defines domain-specific exceptions for better error handling
and diagnostics throughout the application.

"""


class DashboardLegoError(Exception):
    """
    Base exception for all dashboard_lego errors.

        :hierarchy: [Core | Exceptions | DashboardLegoError]
        :relates-to:
         - motivated_by: "User requirement: Proper error handling with
           custom exceptions"
         - implements: "exception: 'DashboardLegoError'"
         - uses: ["class: 'Exception'"]

        :rationale: "Base exception class allows catching all
         library-specific errors."
        :contract:
         - pre: "An error condition specific to dashboard_lego occurs."
         - post: "Exception can be caught and handled appropriately."

    """

    pass


class DataSourceError(DashboardLegoError):
    """
    Raised when data source operations fail.

        :hierarchy: [Core | Exceptions | DataSourceError]
        :relates-to:
         - motivated_by: "User requirement: Specific exception for data
           loading failures"
         - implements: "exception: 'DataSourceError'"
         - uses: ["class: 'DashboardLegoError'"]

        :rationale: "Specific exception for data-related errors aids
         in debugging."
        :contract:
         - pre: "Data loading, processing, or caching fails."
         - post: "Error is raised with descriptive message."

    """

    pass


class DataLoadError(DataSourceError):
    """
    Raised when data loading specifically fails.

        :hierarchy: [Core | Exceptions | DataLoadError]
        :relates-to:
         - motivated_by: "User requirement: Distinguish between load and
           other data errors"
         - implements: "exception: 'DataLoadError'"
         - uses: ["class: 'DataSourceError'"]

        :rationale: "Separates load failures from processing failures."
        :contract:
         - pre: "Data cannot be loaded from source (file, DB, etc.)."
         - post: "Error is raised with source-specific details."

    """

    pass


class CacheError(DataSourceError):
    """
    Raised when cache operations fail.

        :hierarchy: [Core | Exceptions | CacheError]
        :relates-to:
         - motivated_by: "User requirement: Identify caching issues"
         - implements: "exception: 'CacheError'"
         - uses: ["class: 'DataSourceError'"]

        :rationale: "Cache failures should not crash the app but
         should be logged."
        :contract:
         - pre: "Cache read/write operation fails."
         - post: "Error is raised and can be handled gracefully."

    """

    pass


class BlockError(DashboardLegoError):
    """
    Raised when block operations fail.

        :hierarchy: [Core | Exceptions | BlockError]
        :relates-to:
         - motivated_by: "User requirement: Specific exception for
           block-related errors"
         - implements: "exception: 'BlockError'"
         - uses: ["class: 'DashboardLegoError'"]

        :rationale: "Blocks are the main UI components; specific
         errors help debugging."
        :contract:
         - pre: "Block initialization, layout, or update fails."
         - post: "Error is raised with block_id for context."

    """

    pass


class StateError(DashboardLegoError):
    """
    Raised when state management operations fail.

        :hierarchy: [Core | Exceptions | StateError]
        :relates-to:
         - motivated_by: "User requirement: Identify state management
           issues"
         - implements: "exception: 'StateError'"
         - uses: ["class: 'DashboardLegoError'"]

        :rationale: "State management is critical for interactivity;
         specific errors help."
        :contract:
         - pre: "State registration or callback generation fails."
         - post: "Error is raised with state_id for context."

    """

    pass


class ConfigurationError(DashboardLegoError):
    """
    Raised when configuration is invalid.

        :hierarchy: [Core | Exceptions | ConfigurationError]
        :relates-to:
         - motivated_by: "User requirement: Validate configuration at
           startup"
         - implements: "exception: 'ConfigurationError'"
         - uses: ["class: 'DashboardLegoError'"]

        :rationale: "Fail fast on invalid configuration to prevent
         runtime issues."
        :contract:
         - pre: "Invalid parameters or configuration are detected."
         - post: "Error is raised with details about what's invalid."

    """

    pass
