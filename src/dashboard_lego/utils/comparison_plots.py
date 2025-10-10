"""
Comparison plot functions for multi-view visualizations.

Edge case solution: These functions receive multiple DataFrames
or handle calling get_processed_data() multiple times.

:hierarchy: [Utils | Plots | Comparison]
:relates-to:
 - motivated_by: "Need to compare filtered vs unfiltered data simultaneously"
 - implements: "module: 'comparison_plots'"

:contract:
 - pre: Receives multiple DataFrames for comparison
 - post: Returns overlay or side-by-side figure
 - edge_case: Block calls get_processed_data() twice with different params

:complexity: 4
:decision_cache: "Chose two-DataFrame pattern over special datasource methods for clarity"
"""

import pandas as pd
import plotly.graph_objects as go


def plot_overlay_histogram(
    df_baseline: pd.DataFrame,
    df_comparison: pd.DataFrame,
    x: str,
    baseline_name: str = "Baseline",
    comparison_name: str = "Comparison",
    **kwargs,
) -> go.Figure:
    """
    Overlay two histograms for comparison.

    :hierarchy: [Utils | Plots | Comparison | OverlayHistogram]
    :contract:
     - pre: Both DataFrames have column x
     - post: Returns overlay histogram
     - kwargs: Passed to fig.update_layout()

    :complexity: 2
    :decision_cache: "Normalized histograms for fair comparison regardless of sample sizes"

    Args:
        df_baseline: Baseline DataFrame (e.g., all users)
        df_comparison: Comparison DataFrame (e.g., one user)
        x: Column name to plot
        baseline_name: Name for baseline trace
        comparison_name: Name for comparison trace
        **kwargs: Passed to fig.update_layout()

    Returns:
        Plotly Figure with overlay histograms

    Usage in block:
        df_all = datasource.get_processed_data({})  # All data
        df_user = datasource.get_processed_data({'user_id': user})  # Filtered
        fig = plot_overlay_histogram(df_all, df_user, x='feature')
    """
    fig = go.Figure()

    # Add baseline trace
    if not df_baseline.empty and x in df_baseline.columns:
        fig.add_trace(
            go.Histogram(
                x=df_baseline[x],
                name=baseline_name,
                marker_color="#888888",
                opacity=0.6,
                histnorm="probability density",
            )
        )

    # Add comparison trace
    if not df_comparison.empty and x in df_comparison.columns:
        fig.add_trace(
            go.Histogram(
                x=df_comparison[x],
                name=comparison_name,
                marker_color="#BF616A",
                opacity=0.6,
                histnorm="probability density",
            )
        )

    # Apply layout kwargs
    fig.update_layout(barmode="overlay", **kwargs)

    if fig.data:
        return fig
    else:
        return go.Figure().add_annotation(text="No data available for comparison")


def plot_side_by_side_bar(
    df_baseline: pd.DataFrame,
    df_comparison: pd.DataFrame,
    x: str,
    y: str,
    baseline_name: str = "Baseline",
    comparison_name: str = "Comparison",
    **kwargs,
) -> go.Figure:
    """
    Side-by-side bar chart comparison.

    :hierarchy: [Utils | Plots | Comparison | SideBySideBar]
    :contract:
     - pre: Both DataFrames have columns x and y
     - post: Returns grouped bar chart
     - kwargs: Passed to fig.update_layout()

    Args:
        df_baseline: Baseline DataFrame
        df_comparison: Comparison DataFrame
        x: Column for x-axis (categories)
        y: Column for y-axis (values)
        baseline_name: Name for baseline bars
        comparison_name: Name for comparison bars
        **kwargs: Passed to fig.update_layout()

    Returns:
        Plotly Figure with grouped bars
    """
    fig = go.Figure()

    # Add baseline bars
    if not df_baseline.empty and x in df_baseline.columns and y in df_baseline.columns:
        fig.add_trace(
            go.Bar(
                x=df_baseline[x],
                y=df_baseline[y],
                name=baseline_name,
                marker_color="#3498db",
            )
        )

    # Add comparison bars
    if (
        not df_comparison.empty
        and x in df_comparison.columns
        and y in df_comparison.columns
    ):
        fig.add_trace(
            go.Bar(
                x=df_comparison[x],
                y=df_comparison[y],
                name=comparison_name,
                marker_color="#e74c3c",
            )
        )

    fig.update_layout(barmode="group", **kwargs)

    if fig.data:
        return fig
    else:
        return go.Figure().add_annotation(text="No data available for comparison")


def plot_comparison_line(
    df_baseline: pd.DataFrame,
    df_comparison: pd.DataFrame,
    x: str,
    y: str,
    baseline_name: str = "Baseline",
    comparison_name: str = "Comparison",
    **kwargs,
) -> go.Figure:
    """
    Line plot with two series for comparison.

    :hierarchy: [Utils | Plots | Comparison | ComparisonLine]
    :contract:
     - pre: Both DataFrames have columns x and y
     - post: Returns line figure with two traces
     - kwargs: Passed to fig.update_layout()

    Args:
        df_baseline: Baseline DataFrame
        df_comparison: Comparison DataFrame
        x: Column for x-axis
        y: Column for y-axis
        baseline_name: Name for baseline line
        comparison_name: Name for comparison line
        **kwargs: Passed to fig.update_layout()

    Returns:
        Plotly Figure with two line traces
    """
    fig = go.Figure()

    # Add baseline line
    if not df_baseline.empty and x in df_baseline.columns and y in df_baseline.columns:
        fig.add_trace(
            go.Scatter(
                x=df_baseline[x],
                y=df_baseline[y],
                mode="lines",
                name=baseline_name,
                line=dict(color="#3498db", width=2),
            )
        )

    # Add comparison line
    if (
        not df_comparison.empty
        and x in df_comparison.columns
        and y in df_comparison.columns
    ):
        fig.add_trace(
            go.Scatter(
                x=df_comparison[x],
                y=df_comparison[y],
                mode="lines",
                name=comparison_name,
                line=dict(color="#e74c3c", width=2, dash="dash"),
            )
        )

    fig.update_layout(**kwargs)

    if fig.data:
        return fig
    else:
        return go.Figure().add_annotation(text="No data available for comparison")
