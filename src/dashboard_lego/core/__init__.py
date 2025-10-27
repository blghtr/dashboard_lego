"""
Core components of the dashboard_lego library.

Exports:
    - DashboardPage: Main page orchestrator
    - NavigationConfig: Configuration for navigation panels
    - NavigationSection: Individual navigation section definition
    - StateManager: Global state management
    - DataSource: Base data source with 2-stage pipeline
    - DataBuilder: Data building handler (load + process)
    - DataTransformer: Data transformation handler (filter/aggregate/reshape)
    - DataProcessingContext: Pipeline parameter context
    - ThemeConfig: Theme configuration system
    - ColorScheme: Color scheme definition
    - Typography: Typography settings
    - Spacing: Spacing settings

"""

from dashboard_lego.core.data_builder import DataBuilder
from dashboard_lego.core.data_transformer import DataTransformer
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.core.page import DashboardPage, NavigationConfig, NavigationSection
from dashboard_lego.core.processing_context import DataProcessingContext
from dashboard_lego.core.state import StateManager
from dashboard_lego.core.theme import ColorScheme, Spacing, ThemeConfig, Typography

__all__ = [
    "DashboardPage",
    "NavigationConfig",
    "NavigationSection",
    "StateManager",
    "DataSource",
    "DataBuilder",
    "DataTransformer",
    "DataProcessingContext",
    "ThemeConfig",
    "ColorScheme",
    "Typography",
    "Spacing",
]
