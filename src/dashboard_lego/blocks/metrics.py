"""
MetricsBlock - Display aggregated metrics from filtered data.

Replaces get_kpis() from DataSource. Follows KPIBlock pattern.

:hierarchy: [Blocks | Metrics | MetricsBlock]
:relates-to:
 - motivated_by: "Remove get_kpis from DataSource, use block instead"
 - implements: "block: 'MetricsBlock'"

:contract:
 - pre: "metrics_spec dict provided"
 - post: "Renders metrics from filtered data"
 - pattern: "Uses BaseBlock subscription mechanism (no override needed)"

:complexity: 4
:decision_cache: "Support both string agg names and callable functions for flexibility"
"""

from typing import Any, Dict, List, Union

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

    :hierarchy: [Blocks | Metrics | MetricsBlock]
    :complexity: 4

    :contract:
     - agg: Can be str ('sum', 'mean', 'count', 'max', 'min') or callable
     - callable: Receives pd.Series, returns scalar value
     - dtype: Optional dtype for type conversion (e.g., 'float64', 'int64')

    Example:
        metrics = MetricsBlock(
            block_id="metrics",
            datasource=datasource,
            metrics_spec={
                'revenue': {
                    'column': 'Revenue',
                    'agg': 'sum',
                    'title': 'Total Revenue',
                    'color': 'success'
                },
                'avg_price': {
                    'column': 'Price',
                    'agg': 'mean',
                    'title': 'Avg Price',
                    'dtype': 'float64'
                },
                'percentile_95': {
                    'column': 'Sales',
                    'agg': lambda x: x.quantile(0.95),
                    'title': '95th Percentile',
                    'color': 'info'
                }
            },
            subscribes_to=['control-category', 'control-region']
        )
    """

    def __init__(
        self,
        block_id: str,
        datasource: BaseDataSource,
        metrics_spec: Dict[str, Dict[str, Any]],
        subscribes_to: Union[str, List[str], None] = None,
        **kwargs,
    ):
        """
        Initialize MetricsBlock.

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
        self.metrics_spec = metrics_spec

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
                        f"[MetricsBlock] dtype conversion failed for {metric_id}: {e}"
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
        """Render metric cards in responsive row."""
        cards = []

        for metric_id, value in metrics.items():
            spec = self.metrics_spec[metric_id]
            title = spec.get("title", metric_id)
            color = spec.get("color", "primary")

            cards.append(
                dbc.Col(
                    dbc.Card(
                        dbc.CardBody(
                            [
                                html.H6(title, className="text-muted mb-2"),
                                html.H3(
                                    format_number(value), className=f"text-{color} mb-0"
                                ),
                            ]
                        ),
                        className="text-center",
                    ),
                    xs=12,
                    sm=6,
                    md=4,
                    lg=3,
                )
            )

        return dbc.Row(cards, className="g-3")

    def layout(self) -> Component:
        """
        Render initial layout.

        :contract:
         - pre: "Block initialized"
         - post: "Returns container with initial metrics"
        """
        initial_content = self._update_metrics()

        return html.Div(id=self._generate_id("container"), children=initial_content)
