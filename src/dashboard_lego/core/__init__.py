"""
Core components of the dashboard_lego library.

Organized into submodules:
    - sync/: Synchronous API (DataSource, DataBuilder, DataTransformer, etc.)
    - async_api/: Asynchronous API (AsyncDataSource, AsyncDataBuilder, etc.)

Exports:
    - DashboardPage: Main page orchestrator
    - NavigationConfig: Configuration for navigation panels
    - NavigationSection: Individual navigation section definition
    - StateManager: Global state management
    - DataSource: Base data source with 2-stage pipeline (sync)
    - AsyncDataSource: Async version of DataSource
    - DataBuilder: Data building handler (load + process) (sync)
    - AsyncDataBuilder: Async version of DataBuilder
    - DataTransformer: Data transformation handler (sync)
    - AsyncDataTransformer: Async version of DataTransformer
    - DataProcessingContext: Pipeline parameter context
    - ThemeConfig: Theme configuration system
    - ColorScheme: Color scheme definition
    - Typography: Typography settings
    - Spacing: Spacing settings

"""

# Import from submodules for organized structure
from dashboard_lego.core.async_api import (
    AsyncChainedTransformer,
    AsyncDataBuilder,
    AsyncDataFilter,
    AsyncDataSource,
    AsyncDataTransformer,
    AsyncDfHandler,
    AsyncLambdaBuilder,
    AsyncLambdaTransformer,
)

# Import sync classes (from core/ for backward compatibility, but organized in sync/ submodule)
from dashboard_lego.core.data_builder import DataBuilder, DfHandler
from dashboard_lego.core.data_transformer import (
    ChainedTransformer,
    DataFilter,
    DataTransformer,
)
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.core.lambda_handlers import LambdaBuilder, LambdaTransformer

# Import other core components
from dashboard_lego.core.page import DashboardPage, NavigationConfig, NavigationSection
from dashboard_lego.core.processing_context import DataProcessingContext
from dashboard_lego.core.state import StateManager
from dashboard_lego.core.theme import ColorScheme, Spacing, ThemeConfig, Typography

__all__ = [
    "DashboardPage",
    "NavigationConfig",
    "NavigationSection",
    "StateManager",
    # Sync API
    "DataSource",
    "DataBuilder",
    "DfHandler",
    "DataTransformer",
    "DataFilter",
    "ChainedTransformer",
    "LambdaBuilder",
    "LambdaTransformer",
    # Async API
    "AsyncDataSource",
    "AsyncDataBuilder",
    "AsyncDfHandler",
    "AsyncDataTransformer",
    "AsyncDataFilter",
    "AsyncChainedTransformer",
    "AsyncLambdaBuilder",
    "AsyncLambdaTransformer",
    # Other
    "DataProcessingContext",
    "ThemeConfig",
    "ColorScheme",
    "Typography",
    "Spacing",
]
