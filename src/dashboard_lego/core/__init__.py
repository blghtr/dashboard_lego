"""
Core components of the dashboard_lego library.

Exports:
    - DashboardPage: Main page orchestrator
    - NavigationConfig: Configuration for navigation panels
    - NavigationSection: Individual navigation section definition
    - StateManager: Global state management
    - BaseDataSource: Abstract data source interface
    - ThemeConfig: Theme configuration system
    - ColorScheme: Color scheme definition
    - Typography: Typography settings
    - Spacing: Spacing settings

"""

from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.core.page import DashboardPage, NavigationConfig, NavigationSection
from dashboard_lego.core.state import StateManager
from dashboard_lego.core.theme import ColorScheme, Spacing, ThemeConfig, Typography

__all__ = [
    "DashboardPage",
    "NavigationConfig",
    "NavigationSection",
    "StateManager",
    "BaseDataSource",
    "ThemeConfig",
    "ColorScheme",
    "Typography",
    "Spacing",
]
