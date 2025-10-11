"""
Metrics Factory - Factory function for creating metric block rows.

This module provides the get_metric_row() factory function that creates
individual SingleMetricBlock instances and returns them with row options
for proper DashboardPage integration.

:hierarchy: [Blocks | Metrics | Factory]
:relates-to:
 - motivated_by: "SPEC: Separate metric calculation from layout management"
 - implements: "function: 'get_metric_row'"
 - uses: ["class: 'SingleMetricBlock'"]

:contract:
 - pre: "metrics_spec dict with valid metric definitions"
 - post: "Returns (List[SingleMetricBlock], row_options_dict)"
 - invariant: "Each metric is independent block"
 - layout_compliance: "Compatible with DashboardPage row format"

:complexity: 3
:decision_cache: "factory_pattern: Separates metric creation from layout logic"
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from dashboard_lego.blocks.single_metric import SingleMetricBlock
from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.utils.logger import get_logger

logger = get_logger(__name__, "MetricsFactory")


def get_metric_row(
    metrics_spec: Dict[str, Dict[str, Any]],
    datasource: BaseDataSource,
    subscribes_to: Optional[Union[str, List[str]]] = None,
    row_options: Optional[Dict[str, Any]] = None,
    block_id_prefix: str = "metric",
) -> Tuple[List[SingleMetricBlock], Dict[str, Any]]:
    """
    Factory function to create a row of individual metric blocks.

    :hierarchy: [Blocks | Metrics | Factory | GetMetricRow]
    :relates-to:
     - motivated_by: "SPEC: Factory pattern for flexible metric layout"
     - implements: "function: 'get_metric_row'"
     - uses: ["class: 'SingleMetricBlock'"]

    :contract:
     - pre: "metrics_spec contains valid metric definitions"
     - post: "Returns (list_of_blocks, row_options_dict)"
     - invariant: "Each metric is independent SingleMetricBlock"
     - layout_compliance: "Compatible with DashboardPage"

    :complexity: 3
    :decision_cache: "metric_factory: Atomic blocks for flexibility"

    This function separates metric calculation logic from layout management,
    allowing metrics to be composed naturally with other blocks in rows.

    Args:
        metrics_spec: Dictionary of metric definitions, where each key is
            a metric_id and value is a dict with:
            - column (str): Column name to aggregate
            - agg (str|Callable): Aggregation function
            - title (str): Display title
            - color (str): Bootstrap theme color (optional, default: 'primary')
            - dtype (str): Type conversion (optional)
            - color_rules (dict): Conditional coloring (optional)
        datasource: DataSource instance for metric calculation
        subscribes_to: Optional state IDs to subscribe all metrics to
        row_options: Optional Bootstrap row styling options
        block_id_prefix: Prefix for generating block IDs (default: "metric")

    Returns:
        Tuple of (list of SingleMetricBlock instances, row options dict)
        Ready for use with DashboardPage:
            page = DashboardPage(..., blocks=[(metrics, opts), ...])

    Example:
        metrics, row_opts = get_metric_row(
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
                    'title': 'Average Price',
                    'color': 'info'
                }
            },
            datasource=datasource,
            subscribes_to=['filters-category']
        )

        page = DashboardPage(..., blocks=[
            (metrics, row_opts),  # Metrics row
            [chart1, chart2]  # Charts row
        ])
    """
    logger.info(
        f"[Blocks|Metrics|Factory] Creating metric row | "
        f"metrics_count={len(metrics_spec)}"
    )

    # <semantic_block: block_creation>
    metric_blocks = []

    for metric_id, metric_spec in metrics_spec.items():
        # Generate unique block ID
        block_id = f"{block_id_prefix}-{metric_id}"

        # Create SingleMetricBlock
        try:
            metric_block = SingleMetricBlock(
                block_id=block_id,
                datasource=datasource,
                metric_spec=metric_spec,
                subscribes_to=subscribes_to,
            )
            metric_blocks.append(metric_block)

            logger.debug(
                f"[Blocks|Metrics|Factory] Created block | "
                f"block_id={block_id} | title={metric_spec.get('title')}"
            )

        except Exception as e:
            logger.error(
                f"[Blocks|Metrics|Factory] Failed to create block | "
                f"metric_id={metric_id} | error={e}"
            )
            raise

    # </semantic_block: block_creation>

    # <semantic_block: row_options>
    # Default row options: mb-4 spacing, no special alignment
    default_row_options = {"className": "mb-4"}

    # Merge with user-provided options
    final_row_options = {**default_row_options, **(row_options or {})}

    logger.info(
        f"[Blocks|Metrics|Factory] Metric row created | "
        f"blocks={len(metric_blocks)} | row_opts={final_row_options}"
    )
    # </semantic_block: row_options>

    return metric_blocks, final_row_options
