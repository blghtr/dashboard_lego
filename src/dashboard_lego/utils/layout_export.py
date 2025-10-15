"""
Layout export utilities for converting dashboard layouts to Plotly figures.

Supports exporting complex layouts with multiple charts as single Plotly figure
using subplots. Non-chart blocks (metrics, text) are skipped.
"""

from typing import Any, Dict, List, Optional, Tuple

import plotly.graph_objects as go
from plotly.subplots import make_subplots

from dashboard_lego.blocks.base import BaseBlock
from dashboard_lego.utils.logger import get_logger

logger = get_logger(__name__)


def export_layout_to_figure(
    layout: List[List[Any]],
    params: Optional[Dict[str, Any]] = None,
    title: Optional[str] = None,
    vertical_spacing: float = 0.1,
    horizontal_spacing: float = 0.1,
) -> go.Figure:
    """
    Export dashboard layout to single Plotly figure using subplots.

    Converts a dashboard_lego layout structure into a single Plotly figure
    by arranging charts in a grid using subplots. Non-chart blocks are skipped.

    Args:
        layout: Dashboard layout (list of rows, each row is list of blocks/tuples)
        params: Optional parameters to pass to all blocks for filtering
        title: Optional title for the combined figure
        vertical_spacing: Space between rows (0.0 to 1.0)
        horizontal_spacing: Space between columns (0.0 to 1.0)

    Returns:
        Single Plotly Figure with all charts arranged in grid

    Example:
        >>> layout = [
        ...     [chart1, chart2],  # Row 1: 2 charts
        ...     [chart3]           # Row 2: 1 chart
        ... ]
        >>> fig = export_layout_to_figure(layout, title="Dashboard Export")
        >>> fig.write_html("dashboard.html")
    """
    # Extract blocks and calculate grid dimensions
    blocks_grid, rows, cols = _extract_blocks_grid(layout)

    if not blocks_grid:
        logger.warning("No chart blocks found in layout")
        return go.Figure().add_annotation(
            text="No exportable charts in layout",
            showarrow=False,
            xref="paper",
            yref="paper",
            x=0.5,
            y=0.5,
        )

    # Create subplot titles
    subplot_titles = []
    for row in blocks_grid:
        for block in row:
            if block and hasattr(block, "title"):
                subplot_titles.append(block.title or block.block_id)
            else:
                subplot_titles.append("")

    # Create subplots
    fig = make_subplots(
        rows=rows,
        cols=cols,
        subplot_titles=subplot_titles,
        vertical_spacing=vertical_spacing,
        horizontal_spacing=horizontal_spacing,
    )

    # Add traces from each block
    for row_idx, row in enumerate(blocks_grid, start=1):
        for col_idx, block in enumerate(row, start=1):
            if block is None:
                continue

            try:
                # Get figure from block
                block_fig = block.get_figure(params)

                # Add traces to subplot
                for trace in block_fig.data:
                    fig.add_trace(trace, row=row_idx, col=col_idx)

                # Copy axis properties if needed
                _copy_axis_properties(fig, block_fig, row_idx, col_idx)

            except Exception as e:
                logger.error(f"Failed to export block {block.block_id}: {e}")
                continue

    # Update layout
    if title:
        fig.update_layout(title_text=title, title_x=0.5)

    fig.update_layout(showlegend=True, height=300 * rows)

    return fig


def _extract_blocks_grid(
    layout: List[List[Any]],
) -> Tuple[List[List[Optional[BaseBlock]]], int, int]:
    """
    Extract chart blocks from layout and organize into grid.

    Returns:
        Tuple of (blocks_grid, num_rows, num_cols)
    """
    blocks_grid = []
    max_cols = 0

    for row in layout:
        # Handle row options tuple: (row_content, row_options)
        if isinstance(row, tuple):
            row_content = row[0]
        else:
            row_content = row

        row_blocks = []
        for cell in row_content:
            # Extract block from (block, options) tuple
            if isinstance(cell, tuple):
                block = cell[0]
            else:
                block = cell

            # Only include blocks with get_figure() method (chart blocks)
            if hasattr(block, "get_figure") and callable(block.get_figure):
                row_blocks.append(block)

        if row_blocks:
            blocks_grid.append(row_blocks)
            max_cols = max(max_cols, len(row_blocks))

    # Pad rows to have equal columns (None for empty cells)
    for row in blocks_grid:
        while len(row) < max_cols:
            row.append(None)

    return blocks_grid, len(blocks_grid), max_cols


def _copy_axis_properties(
    target_fig: go.Figure, source_fig: go.Figure, row: int, col: int
) -> None:
    """Copy axis titles and properties from source to target subplot."""
    # Get axis references
    xaxis_name = f"xaxis{(row - 1) * 2 + col}" if row > 1 or col > 1 else "xaxis"
    yaxis_name = f"yaxis{(row - 1) * 2 + col}" if row > 1 or col > 1 else "yaxis"

    # Copy axis titles if present
    if source_fig.layout.xaxis.title:
        target_fig.layout[xaxis_name].title = source_fig.layout.xaxis.title
    if source_fig.layout.yaxis.title:
        target_fig.layout[yaxis_name].title = source_fig.layout.yaxis.title
