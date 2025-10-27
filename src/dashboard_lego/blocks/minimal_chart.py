"""
MinimalChartBlock - Minimalist-styled chart block.

Wraps TypedChartBlock with automatic minimal styling preset.

:hierarchy: [Blocks | Charts | MinimalChartBlock]
:relates-to:
 - motivated_by: "Need minimalist charts with stripped-down visuals"
 - implements: "block: 'MinimalChartBlock' wrapping TypedChartBlock"
 - uses: ["class: 'TypedChartBlock'", "plotly figure styling"]

:contract:
 - pre: "plot_type valid (defaults to scatter), x and y required"
 - post: "Returns chart with minimal styling (hidden grids/labels/legend)"
 - invariant: "plot_kwargs can override any minimal preset setting"

:complexity: 4
"""

from typing import Any, Callable, Dict, List, Optional, Union

import pandas as pd
import plotly.graph_objects as go

from dashboard_lego.blocks.typed_chart import Control, TypedChartBlock
from dashboard_lego.core.datasource import DataSource


class MinimalChartBlock(TypedChartBlock):
    """
    Minimalist-styled chart block with stripped-down visuals.

    Wraps TypedChartBlock and applies minimal styling:
    - Hidden grids, zeroline, tick labels, axis titles
    - Transparent background
    - Compact margins
    - Legend hidden by default (override via plot_kwargs)

    Example:
        >>> chart = MinimalChartBlock(
        ...     block_id="sparkline",
        ...     datasource=datasource,
        ...     plot_type='line',  # optional, defaults to scatter
        ...     plot_params={'x': 'date', 'y': 'value'},
        ...     plot_kwargs={'showlegend': True}  # override minimal preset
        ... )
    """

    def __init__(
        self,
        block_id: str,
        datasource: DataSource,
        plot_type: str = "scatter",
        plot_params: Dict[str, Any] = None,
        plot_kwargs: Optional[Dict[str, Any]] = None,
        title: Optional[str] = None,
        plot_title: Optional[str] = None,
        controls: Optional[Dict[str, Control]] = None,
        subscribes_to: Union[str, List[str], Dict[str, Any], None] = None,
        transform_fn: Optional[Callable[[pd.DataFrame], pd.DataFrame]] = None,
        **kwargs,
    ):
        """
        Initialize MinimalChartBlock.

        Args:
            block_id: Unique identifier
            datasource: DataSource instance
            plot_type: Plot type (default: 'scatter')
            plot_params: Plot parameters (x, y, color, size, etc.)
            plot_kwargs: Additional plot kwargs (can override minimal styling)
            title: Block title
            plot_title: Dynamic plot title with placeholders
            controls: Embedded controls
            subscribes_to: External state IDs
            transform_fn: Block-specific data transformation
        """
        # Initialize parent TypedChartBlock
        super().__init__(
            block_id=block_id,
            datasource=datasource,
            plot_type=plot_type,
            plot_params=plot_params or {},
            plot_kwargs=plot_kwargs,
            title=title,
            plot_title=plot_title,
            controls=controls,
            subscribes_to=subscribes_to,
            transform_fn=transform_fn,
            **kwargs,
        )

        self.logger.info(f"[MinimalChartBlock|Init] {block_id} | plot_type={plot_type}")

    def _update_chart(self, *args, **kwargs) -> go.Figure:
        """
        Override to apply minimal styling after chart generation.

        Calls parent's _update_chart, then applies minimal preset.
        """
        # Get figure from parent TypedChartBlock
        figure = super()._update_chart(*args, **kwargs)

        # Apply minimal styling
        figure = self._apply_minimal_style(figure)

        self.logger.debug("[MinimalChartBlock|Update] Applied minimal style preset")
        return figure

    def _apply_minimal_style(self, fig: go.Figure) -> go.Figure:
        """
        Apply minimalist styling to Plotly figure.

        Styling applied (can be overridden via plot_kwargs):
        - Hidden grids, zeroline, tick labels, axis titles
        - Transparent background
        - Compact margins
        - Legend hidden by default

        Args:
            fig: Plotly figure to style

        Returns:
            Styled figure
        """
        # Check plot_kwargs for overrides
        allow_legend = self.plot_kwargs.get("showlegend", False)

        # Apply minimal layout
        fig.update_layout(
            showlegend=allow_legend,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
            margin=dict(l=20, r=20, t=40, b=20),
        )

        # Hide axis elements
        fig.update_xaxes(
            showgrid=False, zeroline=False, showticklabels=False, title=None
        )
        fig.update_yaxes(
            showgrid=False, zeroline=False, showticklabels=False, title=None
        )

        return fig
