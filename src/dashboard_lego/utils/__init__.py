"""
Utils module - utility functions and registries.

:hierarchy: [Utils]
:exports: ["plot_registry", "formatting", "logger", "exceptions",
           "jupyter_factory"]
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
    # Jupyter factory (NEW in v0.15.1)
    "quick_dashboard",
    # Formatting, logger, exceptions imported directly by users if needed
]


def __getattr__(name):
    """Lazy import to avoid circular dependency."""
    if name == "quick_dashboard":
        from dashboard_lego.utils.quick_dashboard import quick_dashboard

        return quick_dashboard
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
