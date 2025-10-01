"""
Core components of the dashboard_lego library.

Exports:
    - DashboardPage: Main page orchestrator
    - NavigationConfig: Configuration for navigation panels
    - NavigationSection: Individual navigation section definition
    - StateManager: Global state management
    - BaseDataSource: Abstract data source interface

"""

from dashboard_lego.core.page import (
    DashboardPage,
    NavigationConfig,
    NavigationSection,
)
from dashboard_lego.core.state import StateManager
from dashboard_lego.core.datasource import BaseDataSource

__all__ = [
    "DashboardPage",
    "NavigationConfig",
    "NavigationSection",
    "StateManager",
    "BaseDataSource",
]
