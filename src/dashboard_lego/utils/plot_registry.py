"""
Plot type registry for extensible chart system.

Maps plot type strings to plotting functions.

:hierarchy: [Utils | Plots | Registry]
:relates-to:
 - motivated_by: "Need extensible mapping of plot types to functions"
 - implements: "module: 'plot_registry'"

:contract:
 - pre: All registered functions follow plot function contract
 - post: get_plot_function() returns callable or raises ValueError
 - invariant: Registry is globally accessible and mutable

:complexity: 2
:decision_cache: "Dict registry for simplicity and runtime extensibility"
"""

from typing import Callable, Dict, List

from dashboard_lego.utils.comparison_plots import (
    plot_comparison_line,
    plot_overlay_histogram,
    plot_side_by_side_bar,
)
from dashboard_lego.utils.knee_plots import plot_knee
from dashboard_lego.utils.plot_functions import (
    plot_area,
    plot_bar,
    plot_box,
    plot_heatmap,
    plot_histogram,
    plot_line,
    plot_scatter,
    plot_violin,
)

# Global registry mapping plot type strings to functions
PLOT_REGISTRY: Dict[str, Callable] = {
    # Basic plots
    "histogram": plot_histogram,
    "scatter": plot_scatter,
    "line": plot_line,
    "box": plot_box,
    "bar": plot_bar,
    "heatmap": plot_heatmap,
    "violin": plot_violin,
    "area": plot_area,
    # Analysis plots
    "knee_plot": plot_knee,
    # Comparison plots
    "overlay_histogram": plot_overlay_histogram,
    "side_by_side_bar": plot_side_by_side_bar,
    "comparison_line": plot_comparison_line,
}


def register_plot_type(name: str, plot_func: Callable) -> None:
    """
    Register custom plot type in global registry.

    :hierarchy: [Utils | Plots | Registry | Register]
    :contract:
     - pre: plot_func follows plot function contract (df, **kwargs) -> go.Figure
     - post: name added to PLOT_REGISTRY
     - invariant: Can override existing types

    Args:
        name: Plot type identifier
        plot_func: Function with signature (df, **kwargs) -> go.Figure

    Example:
        >>> def my_plot(df, x, **kwargs):
        ...     return px.scatter(df, x=x, **kwargs)
        >>> register_plot_type('my_scatter', my_plot)
        >>> # Now available: TypedChartBlock(plot_type='my_scatter', ...)
    """
    PLOT_REGISTRY[name] = plot_func


def get_plot_function(plot_type: str) -> Callable:
    """
    Get plot function by type.

    :hierarchy: [Utils | Plots | Registry | Get]
    :contract:
     - pre: plot_type is string
     - post: Returns callable or raises ValueError

    Args:
        plot_type: Plot type identifier

    Returns:
        Plot function from registry

    Raises:
        ValueError: If plot_type not found in registry
    """
    if plot_type not in PLOT_REGISTRY:
        available = ", ".join(sorted(PLOT_REGISTRY.keys()))
        raise ValueError(
            f"Unknown plot_type: '{plot_type}'. " f"Available types: {available}"
        )
    return PLOT_REGISTRY[plot_type]


def list_plot_types() -> List[str]:
    """
    List all available plot types.

    :hierarchy: [Utils | Plots | Registry | List]
    :contract:
     - pre: None
     - post: Returns sorted list of type names

    Returns:
        List of registered plot type names
    """
    return sorted(PLOT_REGISTRY.keys())
