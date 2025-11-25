"""
Page package for DashboardPage decomposition.

:hierarchy: [Core | Page | Package]
:complexity: 1
"""

# Export DashboardPage and related classes from core module
from dashboard_lego.core.page.core import (
    DashboardPage,
    NavigationConfig,
    NavigationSection,
)

__all__ = [
    "DashboardPage",
    "NavigationConfig",
    "NavigationSection",
]
