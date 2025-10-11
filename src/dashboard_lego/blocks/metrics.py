"""
MetricsBlock - Display aggregated metrics from filtered data.

DEPRECATED: Use get_metric_row() factory pattern instead.

.. deprecated:: 0.16.0
   Use :func:`get_metric_row` for better layout integration.

This module maintained for backward compatibility. MetricsBlock returns a Row
component internally, which violates layout contracts. The new factory pattern
creates individual SingleMetricBlock instances for proper flexbox layout.

:hierarchy: [Blocks | Metrics | MetricsBlock | DEPRECATED]
:relates-to:
 - motivated_by: "Backward compatibility during factory pattern migration"
 - implements: "block: 'MetricsBlock' (deprecated)"
 - superseded_by: "function: 'get_metric_row'"

:contract:
 - pre: "metrics_spec dict provided"
 - post: "Renders metrics from filtered data (as Row component)"
 - pattern: "Uses BaseBlock subscription mechanism (no override needed)"
 - layout_violation: "Returns dbc.Row, not single component"

:complexity: 4
:decision_cache: "deprecated_metrics_block: Kept for backward compat only"
"""

import warnings
from typing import Any, Dict, List, Optional, Union

import dash_bootstrap_components as dbc
import pandas as pd
from dash import html
from dash.development.base_component import Component

from dashboard_lego.blocks.base import BaseBlock
from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.utils.formatting import format_number


class MetricsBlock(BaseBlock):
    """
    Display aggregated metrics (sum, mean, count, etc.).

    .. deprecated:: 0.16.0
       Use :func:`get_metric_row` from metrics_factory for better layout
       integration. This class violates layout contracts by returning dbc.Row
       instead of a single component.

    :hierarchy: [Blocks | Metrics | MetricsBlock | DEPRECATED]
    :complexity: 4

    :contract:
     - agg: Can be str ('sum', 'mean', 'count', 'max', 'min') or callable
     - callable: Receives pd.Series, returns scalar value
     - dtype: Optional dtype for type conversion (e.g., 'float64', 'int64')
     - layout_violation: "Returns dbc.Row, not single component"

    Example (deprecated):
        # OLD WAY (still works but deprecated):
        metrics = MetricsBlock(
            block_id="metrics",
            datasource=datasource,
            metrics_spec={
                'revenue': {
                    'column': 'Revenue',
                    'agg': 'sum',
                    'title': 'Total Revenue',
                    'color': 'success'
                }
            },
            subscribes_to=['control-category']
        )

        # NEW WAY (recommended):
        from dashboard_lego.blocks import get_metric_row

        metrics, opts = get_metric_row(
            metrics_spec={...},
            datasource=datasource,
            subscribes_to=['control-category']
        )
        page = DashboardPage(..., blocks=[(metrics, opts)])
    """

    def __init__(
        self,
        block_id: str,
        datasource: BaseDataSource,
        metrics_spec: Dict[str, Dict[str, Any]],
        subscribes_to: Union[str, List[str], None] = None,
        # Style customization parameters
        container_style: Optional[Dict[str, Any]] = None,
        container_className: Optional[str] = None,
        loading_type: str = "default",
        # Card styling parameters
        card_style: Optional[Dict[str, Any]] = None,
        card_className: Optional[str] = None,
        value_style: Optional[Dict[str, Any]] = None,
        value_className: Optional[str] = None,
        title_style: Optional[Dict[str, Any]] = None,
        title_className: Optional[str] = None,
        **kwargs,
    ):
        """
        Initialize MetricsBlock.

        .. deprecated:: 0.16.0
           Use :func:`get_metric_row` instead.

        Args:
            block_id: Unique block identifier
            datasource: DataSource instance
            metrics_spec: Metric definitions
                Format: {
                    'metric_id': {
                        'column': str,           # Column name to aggregate
                        'agg': str | Callable,   # Aggregation function
                        'title': str,            # Display title
                        'color': str,            # Bootstrap color (optional)
                        'dtype': str             # Type conversion (optional)
                    }
                }
                Built-in agg strings: 'sum', 'mean', 'count', 'max', 'min'
                Custom agg: lambda series: series.quantile(0.95)
                dtype examples: 'float64', 'int64', 'str'
            subscribes_to: State IDs to subscribe to
        """
        # Emit deprecation warning
        warnings.warn(
            "MetricsBlock is deprecated. Use get_metric_row() factory from "
            "dashboard_lego.blocks for better layout integration.",
            DeprecationWarning,
            stacklevel=2,
        )

        self.metrics_spec = metrics_spec

        # Store style customization parameters
        self.container_style = container_style
        self.container_className = container_className
        self.loading_type = loading_type
        self.card_style = card_style
        self.card_className = card_className
        self.value_style = value_style
        self.value_className = value_className
        self.title_style = title_style
        self.title_className = title_className

        # Build subscribes dict (same as KPIBlock - lines 191-192)
        state_ids = self._normalize_subscribes_to(subscribes_to)
        subscribes_dict = {state: self._update_metrics for state in state_ids}

        # Pass to parent - BaseBlock handles everything!
        super().__init__(block_id, datasource, subscribes=subscribes_dict, **kwargs)

    def _calculate_metrics(self, df: pd.DataFrame) -> Dict[str, float]:
        """
        Calculate metrics from filtered DataFrame.

        Supports:
        - String agg: 'sum', 'mean', 'count', 'max', 'min'
        - Callable agg: Custom function(pd.Series) -> scalar
        - Optional dtype conversion

        :contract:
         - pre: "df is filtered"
         - post: "Returns {metric_id: value}"
         - agg: "str or callable"

        :complexity: 3
        """
        results = {}

        for metric_id, spec in self.metrics_spec.items():
            column = spec["column"]
            agg = spec["agg"]
            dtype = spec.get("dtype")  # Optional dtype

            if df.empty or column not in df.columns:
                results[metric_id] = 0.0
                continue

            # Get column data
            series = df[column]

            # Apply dtype conversion if specified
            if dtype is not None:
                try:
                    series = series.astype(dtype)
                except Exception as e:
                    self.logger.warning(
                        f"[MetricsBlock] dtype conversion failed for "
                        f"{metric_id}: {e}"
                    )

            # Calculate metric
            try:
                if callable(agg):
                    # Custom callable function
                    value = agg(series)
                elif isinstance(agg, str):
                    # Built-in string aggregations
                    if agg == "sum":
                        value = series.sum()
                    elif agg == "mean":
                        value = series.mean()
                    elif agg == "count":
                        value = len(df)
                    elif agg == "max":
                        value = series.max()
                    elif agg == "min":
                        value = series.min()
                    else:
                        self.logger.warning(f"Unknown agg string: {agg}")
                        value = 0.0
                else:
                    self.logger.warning(
                        f"Invalid agg type for {metric_id}: {type(agg)}"
                    )
                    value = 0.0

                results[metric_id] = value

            except Exception as e:
                self.logger.error(f"[MetricsBlock] Error calculating {metric_id}: {e}")
                results[metric_id] = 0.0

        return results

    def _calculate_responsive_columns(self, metric_count: int) -> Dict[str, int]:
        """
        Calculate optimal Bootstrap column sizes based on metric count.

        :hierarchy: [Blocks | Metrics | MetricsBlock | ColumnCalculation]
        :relates-to:
         - motivated_by: "Dynamic scaling requirement for optimal space"
         - implements: "method: '_calculate_responsive_columns'"

        :contract:
         - pre: "metric_count > 0"
         - post: "Returns dict with Bootstrap column sizes"
         - invariant: "Total columns sum to 12 per breakpoint"
         - scaling_principle: "Minimize empty space"

        :complexity: 2
        :decision_cache: "Responsive sizing per metric count"

        Args:
            metric_count: Number of metrics to display

        Returns:
            Dict with Bootstrap column props (xs, sm, md, lg)

        Example:
            >>> _calculate_responsive_columns(2)
            {'xs': 12, 'sm': 6, 'md': 6, 'lg': 6}
        """
        if metric_count == 1:
            # Single metric: Full width
            return {"xs": 12, "sm": 12, "md": 12, "lg": 12}
        elif metric_count == 2:
            # Two metrics: Half width each
            return {"xs": 12, "sm": 6, "md": 6, "lg": 6}
        elif metric_count == 3:
            # Three metrics: Third width each (4 columns)
            return {"xs": 12, "sm": 6, "md": 4, "lg": 4}
        else:
            # Four or more metrics: Quarter width each (3 columns)
            # This ensures we don't have too narrow cards
            return {"xs": 12, "sm": 6, "md": 3, "lg": 3}

    def _update_metrics(self, *args) -> Component:
        """
        Update metrics display.

        Called by BaseBlock automatically when subscribed states change.
        Same pattern as KPIBlock._update_kpi_cards.

        :contract:
         - pre: "Subscribed state values in *args"
         - post: "Returns updated metric cards"
        """
        # Build params dict from args (same as KPIBlock lines 218-224)
        params = {}
        if args and hasattr(self, "subscribes"):
            state_ids = list(self.subscribes.keys())
            for idx, value in enumerate(args):
                if idx < len(state_ids):
                    params[state_ids[idx]] = value

        self.logger.debug(f"[MetricsBlock|Update] params={params}")

        # Get filtered data
        df = self.datasource.get_processed_data(params)

        # Calculate metrics
        metrics = self._calculate_metrics(df)

        # Render
        return self._render_cards(metrics)

    def _render_cards(self, metrics: Dict[str, float]) -> Component:
        """
        Render metric cards with dynamic responsive sizing.

        :hierarchy: [Blocks | Metrics | MetricsBlock | Rendering]
        :relates-to:
         - motivated_by: "User feedback: Metrics should scale dynamically"
         - implements: "method: '_render_cards' with dynamic column sizing"
         - uses: ["component: 'dbc.Col'", "component: 'dbc.Card'"]

        :contract:
         - pre: "metrics dict with calculated values"
         - post: "Returns responsive row with dynamically sized cards"
         - invariant: "Cards fill horizontal space optimally"
         - invariant: "Equal height via h-100 class"
         - scaling_logic: "Optimal column sizes per count"

        :complexity: 4
        :decision_cache: "Dynamic sizing per metric count"

        Responsive sizing strategy:
        - 1 metric: Full width (xs=12, sm=12, md=12, lg=12)
        - 2 metrics: Half width each (xs=12, sm=6, md=6, lg=6)
        - 3 metrics: Third width each (xs=12, sm=6, md=4, lg=4)
        - 4+ metrics: Quarter width each (xs=12, sm=6, md=3, lg=3)
        """
        cards = []
        metric_count = len(metrics)

        # Calculate optimal column sizes based on metric count
        # This ensures metrics always fill available horizontal space
        col_props = self._calculate_responsive_columns(metric_count)

        self.logger.debug(
            f"[MetricsBlock|Render] Rendering {metric_count} metrics with "
            f"columns: {col_props}"
        )

        for metric_id, value in metrics.items():
            spec = self.metrics_spec[metric_id]
            title = spec.get("title", metric_id)
            color = spec.get("color", "primary")

            # Build card props with theme integration
            # h-100 ensures equal height cards in the row
            base_classes = "text-center h-100"
            card_props = {
                "className": (
                    f"{base_classes} {self.card_className}"
                    if self.card_className
                    else base_classes
                )
            }
            if self.card_style:
                card_props["style"] = self.card_style

            # Build title props
            title_props = {"className": self.title_className or "text-muted mb-2"}
            if self.title_style:
                title_props["style"] = self.title_style

            # Build value props with color
            value_props = {"className": self.value_className or f"text-{color} mb-0"}
            if self.value_style:
                value_props["style"] = self.value_style

            cards.append(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H6(title, **title_props),
                                html.H3(format_number(value), **value_props),
                            ]
                        ),
                        **card_props,
                    ),
                    className="h-100",  # Stretch column to full row height
                    **col_props,
                )
            )

        return dbc.Row(cards, className="g-3 align-items-stretch")

    def layout(self) -> Component:
        """
        Render initial layout with styling and loading support.

        :hierarchy: [Blocks | Metrics | MetricsBlock | Layout]
        :relates-to:
         - motivated_by: "Consistent styling with other blocks and loading"
         - implements: "method: 'layout' with style overrides and loading"

        :contract:
         - pre: "Block initialized with style parameters"
         - post: "Returns styled container with loading and initial metrics"
         - invariant: "Applies container styling and loading animation"

        :complexity: 3
        """
        initial_content = self._update_metrics()

        # Build container props with style overrides
        container_props = {
            "id": self._generate_id("container"),
            "children": initial_content,
        }
        if self.container_style:
            container_props["style"] = self.container_style
        if self.container_className:
            container_props["className"] = self.container_className

        return html.Div(**container_props)
