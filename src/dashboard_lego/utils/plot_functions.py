"""
Plot functions library for TypedChartBlock.

Pure functions for generating Plotly figures from pre-filtered DataFrames.

:hierarchy: [Utils | Plots | Functions]
:relates-to:
 - motivated_by: "Need reusable plot functions for high-level TypedChartBlock"
 - implements: "utility: 'plot_functions_library'"
 - uses: ["library: 'plotly'"]

:contract:
 - pre: All functions receive pre-filtered DataFrame from get_processed_data(params)
 - post: All functions return go.Figure (never raise exceptions)
 - invariant: Functions are pure (no side effects, deterministic)
 - kwargs: All **kwargs passed to plotly.express or fig.update_layout()

:complexity: 5
:decision_cache: "Chose pure functions over class methods for maximum reusability"
"""

from typing import Optional

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

from dashboard_lego.utils.logger import get_logger

logger = get_logger(__name__, "plot_functions")


def plot_histogram(
    df: pd.DataFrame,
    x: str,
    bins: int = 20,
    color: Optional[str] = None,
    title: Optional[str] = None,
    **kwargs,
) -> go.Figure:
    """
    Create histogram plot from pre-filtered data.

    :hierarchy: [Utils | Plots | Histogram]
    :relates-to:
     - motivated_by: "Basic histogram visualization"
     - implements: "function: 'plot_histogram'"

    :contract:
     - pre: df is pre-filtered, x is column name
     - post: Returns histogram figure
     - kwargs: Passed directly to px.histogram()

    :complexity: 1

    Args:
        df: Pre-filtered DataFrame from get_processed_data()
        x: Column name for x-axis
        bins: Number of histogram bins
        color: Optional column for color grouping
        title: Chart title
        **kwargs: Additional arguments for px.histogram()
                 (e.g., opacity, barmode, histnorm)

    Returns:
        Plotly Figure object or empty figure if data invalid
    """
    logger.debug(f"[plot_histogram] x={x}, bins={bins}, color={color}")

    if df.empty:
        logger.warning("[plot_histogram] Empty DataFrame received")
        return go.Figure()

    if x not in df.columns:
        logger.error(f"[plot_histogram] Column '{x}' not found in DataFrame")
        return go.Figure()

    try:
        fig = px.histogram(df, x=x, color=color, nbins=bins, title=title, **kwargs)
        logger.debug("[plot_histogram] Figure created successfully")
        return fig
    except Exception as e:
        logger.error(f"[plot_histogram] Error creating figure: {e}", exc_info=True)
        return go.Figure()


def plot_scatter(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: Optional[str] = None,
    size: Optional[str] = None,
    title: Optional[str] = None,
    **kwargs,
) -> go.Figure:
    """
    Create scatter plot from pre-filtered data.

    :hierarchy: [Utils | Plots | Scatter]
    :relates-to:
     - motivated_by: "Scatter plot for correlation analysis"
     - implements: "function: 'plot_scatter'"

    :contract:
     - pre: df is pre-filtered, x and y are column names
     - post: Returns scatter plot figure
     - kwargs: Passed directly to px.scatter()

    :complexity: 1

    Args:
        df: Pre-filtered DataFrame
        x: Column name for x-axis
        y: Column name for y-axis
        color: Optional column for color grouping
        size: Optional column for marker size
        title: Chart title
        **kwargs: Additional arguments for px.scatter()

    Returns:
        Plotly Figure object or empty figure if data invalid
    """
    logger.debug(f"[plot_scatter] x={x}, y={y}, color={color}, size={size}")

    if df.empty:
        logger.warning("[plot_scatter] Empty DataFrame received")
        return go.Figure()

    if x not in df.columns:
        logger.error(f"[plot_scatter] Column '{x}' not found")
        return go.Figure()

    if y not in df.columns:
        logger.error(f"[plot_scatter] Column '{y}' not found")
        return go.Figure()

    # CRITICAL: Remove rows with NaN in required columns to prevent plotly errors
    required_cols = [x, y]
    if color and color in df.columns:
        required_cols.append(color)
    if size and size in df.columns:
        required_cols.append(size)

    df_clean = df.dropna(subset=required_cols)
    if len(df_clean) < len(df):
        logger.warning(
            f"[plot_scatter] Removed {len(df) - len(df_clean)} rows with NaN values"
        )

    if df_clean.empty:
        logger.error("[plot_scatter] No valid rows after removing NaN values")
        return go.Figure()

    try:
        fig = px.scatter(
            df_clean, x=x, y=y, color=color, size=size, title=title, **kwargs
        )
        logger.debug("[plot_scatter] Figure created successfully")
        return fig
    except Exception as e:
        logger.error(f"[plot_scatter] Error: {e}", exc_info=True)
        return go.Figure()


def plot_line(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: Optional[str] = None,
    title: Optional[str] = None,
    **kwargs,
) -> go.Figure:
    """
    Create line plot from pre-filtered data.

    :hierarchy: [Utils | Plots | Line]
    :relates-to:
     - motivated_by: "Time series and trend visualization"
     - implements: "function: 'plot_line'"

    :contract:
     - pre: df is pre-filtered, x and y are column names
     - post: Returns line plot figure
     - kwargs: Passed directly to px.line()

    :complexity: 1

    Args:
        df: Pre-filtered DataFrame
        x: Column name for x-axis (typically time/date)
        y: Column name for y-axis
        color: Optional column for line color grouping
        title: Chart title
        **kwargs: Additional arguments for px.line()

    Returns:
        Plotly Figure object or empty figure if data invalid
    """
    logger.debug(f"[plot_line] x={x}, y={y}, color={color}")

    if df.empty:
        logger.warning("[plot_line] Empty DataFrame received")
        return go.Figure()

    if x not in df.columns or y not in df.columns:
        logger.error("[plot_line] Required columns not found")
        return go.Figure()

    try:
        fig = px.line(df, x=x, y=y, color=color, title=title, **kwargs)
        logger.debug("[plot_line] Figure created successfully")
        return fig
    except Exception as e:
        logger.error(f"[plot_line] Error: {e}", exc_info=True)
        return go.Figure()


def plot_box(
    df: pd.DataFrame,
    x: Optional[str] = None,
    y: Optional[str] = None,
    color: Optional[str] = None,
    title: Optional[str] = None,
    **kwargs,
) -> go.Figure:
    """
    Create box plot from pre-filtered data.

    :hierarchy: [Utils | Plots | Box]
    :relates-to:
     - motivated_by: "Distribution comparison visualization"
     - implements: "function: 'plot_box'"

    :contract:
     - pre: df is pre-filtered
     - post: Returns box plot figure
     - kwargs: Passed directly to px.box()

    :complexity: 1

    Args:
        df: Pre-filtered DataFrame
        x: Optional column for x-axis (categories)
        y: Optional column for y-axis (values)
        color: Optional column for color grouping
        title: Chart title
        **kwargs: Additional arguments for px.box()

    Returns:
        Plotly Figure object or empty figure if data invalid
    """
    logger.debug(f"[plot_box] x={x}, y={y}, color={color}")

    if df.empty:
        logger.warning("[plot_box] Empty DataFrame received")
        return go.Figure()

    try:
        fig = px.box(df, x=x, y=y, color=color, title=title, **kwargs)
        logger.debug("[plot_box] Figure created successfully")
        return fig
    except Exception as e:
        logger.error(f"[plot_box] Error: {e}", exc_info=True)
        return go.Figure()


def plot_bar(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: Optional[str] = None,
    orientation: str = "v",
    title: Optional[str] = None,
    **kwargs,
) -> go.Figure:
    """
    Create bar chart from pre-filtered data.

    :hierarchy: [Utils | Plots | Bar]
    :relates-to:
     - motivated_by: "Categorical data visualization"
     - implements: "function: 'plot_bar'"

    :contract:
     - pre: df is pre-filtered, x and y are column names
     - post: Returns bar chart figure
     - kwargs: Passed directly to px.bar()

    :complexity: 1

    Args:
        df: Pre-filtered DataFrame
        x: Column name for x-axis
        y: Column name for y-axis
        color: Optional column for bar color grouping
        orientation: 'v' for vertical, 'h' for horizontal
        title: Chart title
        **kwargs: Additional arguments for px.bar()

    Returns:
        Plotly Figure object or empty figure if data invalid
    """
    logger.debug(f"[plot_bar] x={x}, y={y}, orientation={orientation}")

    if df.empty:
        logger.warning("[plot_bar] Empty DataFrame received")
        return go.Figure()

    if x not in df.columns or y not in df.columns:
        logger.error("[plot_bar] Required columns not found")
        return go.Figure()

    try:
        fig = px.bar(
            df, x=x, y=y, color=color, orientation=orientation, title=title, **kwargs
        )
        logger.debug("[plot_bar] Figure created successfully")
        return fig
    except Exception as e:
        logger.error(f"[plot_bar] Error: {e}", exc_info=True)
        return go.Figure()


def plot_heatmap(
    df: pd.DataFrame,
    values: Optional[str] = None,
    index: Optional[str] = None,
    columns: Optional[str] = None,
    title: Optional[str] = None,
    **kwargs,
) -> go.Figure:
    """
    Create heatmap from pre-filtered data.

    Two modes:
    1. Pivot table mode: values, index, columns specified
    2. Correlation mode: auto-correlates numeric columns

    :hierarchy: [Utils | Plots | Heatmap]
    :relates-to:
     - motivated_by: "Matrix visualization for correlations and pivot tables"
     - implements: "function: 'plot_heatmap'"

    :contract:
     - pre: df is pre-filtered
     - post: Returns heatmap figure
     - kwargs: Passed to fig.update_layout()

    :complexity: 2
    :decision_cache: "Dual-mode heatmap for flexibility"

    Args:
        df: Pre-filtered DataFrame
        values: Column name for cell values (pivot mode)
        index: Column name for rows (pivot mode)
        columns: Column name for columns (pivot mode)
        title: Chart title
        **kwargs: Additional arguments for fig.update_layout()

    Returns:
        Plotly Figure object or empty figure if data invalid
    """
    logger.debug(f"[plot_heatmap] mode={'pivot' if values else 'correlation'}")

    if df.empty:
        logger.warning("[plot_heatmap] Empty DataFrame received")
        return go.Figure()

    try:
        if values and index and columns:
            # Pivot table mode
            logger.debug(f"[plot_heatmap] Pivot mode: {index} x {columns} = {values}")
            pivot = df.pivot_table(values=values, index=index, columns=columns)
        else:
            # Correlation mode
            logger.debug("[plot_heatmap] Correlation mode")
            numerical_df = df.select_dtypes(include="number")
            if numerical_df.empty:
                logger.warning("[plot_heatmap] No numerical columns for correlation")
                return go.Figure()
            pivot = numerical_df.corr()

        fig = go.Figure(
            data=go.Heatmap(
                z=pivot.values,
                x=list(pivot.columns),
                y=list(pivot.index),
                colorscale="RdBu",
                zmid=0,
            )
        )

        if title:
            fig.update_layout(title=title)
        fig.update_layout(**kwargs)

        logger.debug("[plot_heatmap] Figure created successfully")
        return fig
    except Exception as e:
        logger.error(f"[plot_heatmap] Error: {e}", exc_info=True)
        return go.Figure()


def plot_violin(
    df: pd.DataFrame,
    x: Optional[str] = None,
    y: Optional[str] = None,
    color: Optional[str] = None,
    title: Optional[str] = None,
    **kwargs,
) -> go.Figure:
    """
    Create violin plot from pre-filtered data.

    :hierarchy: [Utils | Plots | Violin]
    :relates-to:
     - motivated_by: "Distribution shape visualization"
     - implements: "function: 'plot_violin'"

    :contract:
     - pre: df is pre-filtered
     - post: Returns violin plot figure
     - kwargs: Passed directly to px.violin()

    :complexity: 1

    Args:
        df: Pre-filtered DataFrame
        x: Optional column for x-axis (categories)
        y: Optional column for y-axis (values)
        color: Optional column for color grouping
        title: Chart title
        **kwargs: Additional arguments for px.violin()

    Returns:
        Plotly Figure object or empty figure if data invalid
    """
    logger.debug(f"[plot_violin] x={x}, y={y}, color={color}")

    if df.empty:
        logger.warning("[plot_violin] Empty DataFrame received")
        return go.Figure()

    try:
        fig = px.violin(df, x=x, y=y, color=color, title=title, **kwargs)
        logger.debug("[plot_violin] Figure created successfully")
        return fig
    except Exception as e:
        logger.error(f"[plot_violin] Error: {e}", exc_info=True)
        return go.Figure()


def plot_area(
    df: pd.DataFrame,
    x: str,
    y: str,
    color: Optional[str] = None,
    title: Optional[str] = None,
    **kwargs,
) -> go.Figure:
    """
    Create area plot from pre-filtered data.

    :hierarchy: [Utils | Plots | Area]
    :relates-to:
     - motivated_by: "Stacked area charts for composition over time"
     - implements: "function: 'plot_area'"

    :contract:
     - pre: df is pre-filtered, x and y are column names
     - post: Returns area plot figure
     - kwargs: Passed directly to px.area()

    :complexity: 1

    Args:
        df: Pre-filtered DataFrame
        x: Column name for x-axis (typically time)
        y: Column name for y-axis
        color: Optional column for area color grouping
        title: Chart title
        **kwargs: Additional arguments for px.area()

    Returns:
        Plotly Figure object or empty figure if data invalid
    """
    logger.debug(f"[plot_area] x={x}, y={y}, color={color}")

    if df.empty:
        logger.warning("[plot_area] Empty DataFrame received")
        return go.Figure()

    if x not in df.columns or y not in df.columns:
        logger.error("[plot_area] Required columns not found")
        return go.Figure()

    try:
        fig = px.area(df, x=x, y=y, color=color, title=title, **kwargs)
        logger.debug("[plot_area] Figure created successfully")
        return fig
    except Exception as e:
        logger.error(f"[plot_area] Error: {e}", exc_info=True)
        return go.Figure()
