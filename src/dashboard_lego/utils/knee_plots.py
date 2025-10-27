"""
Knee plot functions for TypedChartBlock.

Pure functions for generating knee/elbow plots with optional automatic knee detection.

:hierarchy: [Utils | Plots | KneePlots]
:relates-to:
 - motivated_by: "Need knee/elbow plot visualization for optimization analysis and cluster validation"
 - implements: "utility: 'knee_plots_library'"
 - uses: ["library: 'plotly'", "optional: 'kneed' for auto-detection"]

:contract:
 - pre: All functions receive pre-filtered DataFrame from get_processed_data(params)
 - post: All functions return go.Figure (never raise exceptions)
 - invariant: Functions are pure (no side effects, deterministic)
 - kwargs: All **kwargs passed to plotly.express or fig.update_layout()
 - dependency: Auto knee detection requires 'kneed' package (lazy import)

:complexity: 4
:decision_cache: "Lazy import kneed to avoid hard dependency while enabling auto-detection"
"""

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard_lego.utils.logger import get_logger

logger = get_logger(__name__, "knee_plots")


def plot_knee(
    df: pd.DataFrame,
    x: str,
    y: str,
    title: Optional[str] = None,
    auto_knee: bool = False,
    knee_curve: str = "concave",
    knee_direction: str = "increasing",
    knee_S: float = 1.0,
    annotate_knee: bool = True,
    sort_by_x: bool = True,
    marker_kwargs: Optional[dict] = None,
    line_kwargs: Optional[dict] = None,
    **kwargs,
) -> go.Figure:
    """
    Create knee/elbow plot from pre-filtered data with optional automatic knee detection.

    :hierarchy: [Utils | Plots | KneePlots | KneePlot]
    :relates-to:
     - motivated_by: "Knee/elbow plots for optimization analysis, cluster validation, and parameter tuning"
     - implements: "function: 'plot_knee'"
     - uses: [
         "px.line: creates line plot for knee visualization",
         "kneed.KneeLocator: automatic knee detection (optional dependency)"
     ]

    :contract:
     - pre: df is pre-filtered, x and y are column names, knee_curve in ['concave', 'convex'], knee_direction in ['increasing', 'decreasing']
     - post: Returns knee plot figure with optional knee marker and annotation
     - invariant: deterministic (same input → same output), no side effects, never raises exceptions
     - dependency: auto_knee=True requires 'kneed' package (uv pip install kneed)

    :complexity: 4
    :decision_cache: "Lazy import kneed to avoid hard dependency while enabling auto-detection"

    Args:
        df: Pre-filtered DataFrame from get_processed_data()
        x: Column name for x-axis (typically parameter values, k values, etc.)
        y: Column name for y-axis (typically cost, inertia, error, etc.)
        title: Chart title
        auto_knee: Enable automatic knee detection (requires 'kneed' package)
        knee_curve: Curve type for knee detection ('concave' or 'convex')
        knee_direction: Direction of curve ('increasing' or 'decreasing')
        knee_S: Sensitivity parameter for knee detection (higher = less sensitive)
        annotate_knee: Add annotation and marker for detected knee point
        sort_by_x: Sort data by x values before knee detection (recommended for KneeLocator)
        marker_kwargs: Additional kwargs for knee marker (overrides defaults)
        line_kwargs: Additional kwargs for line plot (overrides px.line defaults)
        **kwargs: Additional arguments for fig.update_layout()

    Returns:
        Plotly Figure object with knee plot and optional knee detection

    Example:
        >>> fig = plot_knee(df, x='k', y='inertia', auto_knee=True, title='K-means Elbow Plot')
        >>> # Shows line plot with automatic knee point detection and annotation

    Note:
        Automatic knee detection requires the 'kneed' package:
        uv pip install kneed

        If 'kneed' is not installed and auto_knee=True, the plot will display
        an annotation prompting installation but will still render the basic plot.
    """
    logger.debug(
        f"[plot_knee] x={x}, y={y}, auto_knee={auto_knee}, "
        f"curve={knee_curve}, direction={knee_direction}, S={knee_S}"
    )

    if df.empty:
        logger.warning("[plot_knee] Empty DataFrame received")
        return go.Figure().add_annotation(
            text="No data available for knee plot",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )

    if x not in df.columns:
        logger.error(f"[plot_knee] Column '{x}' not found in DataFrame")
        return go.Figure().add_annotation(
            text=f"Column '{x}' not found",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )

    if y not in df.columns:
        logger.error(f"[plot_knee] Column '{y}' not found in DataFrame")
        return go.Figure().add_annotation(
            text=f"Column '{y}' not found",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )

    # Remove rows with NaN in required columns
    df_clean = df.dropna(subset=[x, y])
    if len(df_clean) < len(df):
        logger.warning(
            f"[plot_knee] Removed {len(df) - len(df_clean)} rows with NaN values"
        )

    if df_clean.empty:
        logger.error("[plot_knee] No valid rows after removing NaN values")
        return go.Figure().add_annotation(
            text="No valid data points after removing NaN values",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )

    try:
        # Sort by x if requested (recommended for KneeLocator)
        if sort_by_x:
            df_sorted = df_clean.sort_values(x).copy()
            logger.debug("[plot_knee] Data sorted by x values for knee detection")
        else:
            df_sorted = df_clean.copy()

        # Create base line plot
        fig = px.line(
            df_sorted,
            x=x,
            y=y,
            title=title,
        )

        # Apply line styling
        line_defaults = {"line": {"width": 2}, "mode": "lines+markers"}
        if line_kwargs:
            line_defaults.update(line_kwargs)
        fig.update_traces(**line_defaults)

        # Auto knee detection
        if auto_knee:
            # Lazy import kneed
            try:
                from kneed import KneeLocator

                logger.debug("[plot_knee] KneeLocator imported successfully")
            except ImportError:
                KneeLocator = None
                logger.warning(
                    "[plot_knee] kneed package not available. Install with: uv pip install kneed"
                )

            if KneeLocator is not None:
                # Extract x and y values for knee detection
                x_vals = df_sorted[x].values
                y_vals = df_sorted[y].values

                try:
                    # Create KneeLocator instance
                    kl = KneeLocator(
                        x_vals,
                        y_vals,
                        curve=knee_curve,
                        direction=knee_direction,
                        S=knee_S,
                    )
                    knee_x = kl.knee

                    if knee_x is not None and annotate_knee:
                        # Find corresponding y value for knee point
                        knee_idx = df_sorted[df_sorted[x] == knee_x].index
                        if len(knee_idx) > 0:
                            knee_y = df_sorted.loc[knee_idx[0], y]
                        else:
                            # Interpolate if exact match not found
                            knee_y = (
                                df_sorted[y]
                                .iloc[(df_sorted[x] - knee_x).abs().argsort()[:1]]
                                .iloc[0]
                            )

                        # Add knee marker
                        marker_defaults = {
                            "size": 12,
                            "color": "red",
                            "symbol": "diamond",
                            "line": {"width": 2, "color": "darkred"},
                        }
                        if marker_kwargs:
                            marker_defaults.update(marker_kwargs)

                        fig.add_scatter(
                            x=[knee_x],
                            y=[knee_y],
                            mode="markers",
                            marker=marker_defaults,
                            name="Knee Point",
                            showlegend=True,
                        )

                        # Add knee annotation
                        fig.add_annotation(
                            x=knee_x,
                            y=knee_y,
                            text=f"Knee: {knee_x:.2f}",
                            showarrow=True,
                            arrowhead=2,
                            arrowsize=1,
                            arrowwidth=2,
                            arrowcolor="red",
                            ax=20,
                            ay=-30,
                            bgcolor="white",
                            bordercolor="red",
                            borderwidth=1,
                        )

                        logger.info(
                            f"[plot_knee] Knee detected at x={knee_x:.2f}, y={knee_y:.2f}"
                        )
                    else:
                        logger.info("[plot_knee] No knee point detected")

                except Exception as e:
                    logger.error(f"[plot_knee] Error in knee detection: {e}")
                    # Continue without knee detection

            else:
                # kneed not available - add installation prompt
                fig.add_annotation(
                    text="kneed not installed: uv pip install kneed",
                    showarrow=False,
                    x=0.5,
                    y=0.1,
                    xref="paper",
                    yref="paper",
                    bgcolor="yellow",
                    bordercolor="orange",
                    borderwidth=1,
                    font={"color": "black", "size": 12},
                )

        # Apply additional layout updates
        if kwargs:
            fig.update_layout(**kwargs)

        logger.debug("[plot_knee] Figure created successfully")
        return fig

    except Exception as e:
        logger.error(f"[plot_knee] Error creating figure: {e}", exc_info=True)
        return go.Figure().add_annotation(
            text=f"Error creating knee plot: {str(e)[:100]}",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
            font={"color": "red"},
        )
