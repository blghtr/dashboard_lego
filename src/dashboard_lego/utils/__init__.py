"""
Utils module - utility functions and registries.

:hierarchy: [Utils]
:exports: ["plot_registry", "formatting", "logger", "exceptions"]
"""

from dashboard_lego.utils.plot_registry import (
    PLOT_REGISTRY,
    get_plot_function,
    list_plot_types,
    register_plot_type,
)

__all__ = [
    # Plot registry (NEW in v0.15.0)
    "PLOT_REGISTRY",
    "register_plot_type",
    "get_plot_function",
    "list_plot_types",
    # Formatting, logger, exceptions imported directly by users if needed
]
