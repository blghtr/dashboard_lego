"""
Metrics Factory - Factory function for creating dashboard block rows.

This module provides the get_metric_row() factory function that creates
individual SingleMetricBlock (numeric) or TextBlock (text) instances and
returns them with row options for proper DashboardPage integration.

:hierarchy: [Blocks | Metrics | Factory]
:relates-to:
 - motivated_by: "PRD: Unified factory for dashboard lamps (numeric metrics and text blocks)"
 - implements: "function: 'get_metric_row'"
 - uses: ["class: 'SingleMetricBlock'", "class: 'TextBlock'"]

:contract:
 - pre: "metrics_spec dict with valid block definitions (numeric or text)"
 - post: "Returns (List[BaseBlock], row_options_dict)"
 - invariant: "Each block is independent, all have h-100 for equal height"
 - layout_compliance: "Compatible with DashboardPage row format"

:complexity: 4
:decision_cache: "unified_factory: Content-based type detection for numeric vs text blocks"
"""

from typing import Any, Dict, List, Optional, Tuple, Union

from dashboard_lego.blocks.base import BaseBlock
from dashboard_lego.blocks.single_metric import SingleMetricBlock
from dashboard_lego.blocks.text import TextBlock
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.utils.logger import get_logger

logger = get_logger(__name__, "MetricsFactory")


def get_metric_row(
    metrics_spec: Dict[str, Dict[str, Any]],
    datasource: DataSource,
    subscribes_to: Optional[Union[str, List[str]]] = None,
    row_options: Optional[Dict[str, Any]] = None,
    block_id_prefix: str = "metric",
) -> Tuple[List[BaseBlock], Dict[str, Any]]:
    """
    Factory function to create a row of dashboard blocks (numeric metrics or text).

    :hierarchy: [Blocks | Metrics | Factory | GetMetricRow]
    :relates-to:
     - motivated_by: "PRD: Unified factory for dashboard lamps supporting both numeric and text content"
     - implements: "function: 'get_metric_row' with content-based type detection"
     - uses: ["class: 'SingleMetricBlock'", "class: 'TextBlock'"]

    :contract:
     - pre: "metrics_spec contains valid block definitions (numeric or text)"
     - post: "Returns (list_of_blocks, row_options_dict)"
     - invariant: "Each block is independent, all have h-100 for equal height"
     - layout_compliance: "Compatible with DashboardPage"

    :complexity: 4
    :decision_cache: "unified_factory: Content-based detection (column+agg = numeric, content_generator = text)"

    This function creates a row of equal-height containers ("dashboard lamps") that can
    display either numeric metrics (SingleMetricBlock) or text content (TextBlock).
    Block type is automatically detected from spec keys.

    Args:
        metrics_spec: Dictionary of block definitions, where each key is a block_id
            and value is a dict. For numeric metrics:
            - column (str): Column name to aggregate
            - agg (str|Callable): Aggregation function
            - title (str): Display title
            - color (str|dict): Bootstrap theme color (optional, supports conditional)
            - label (str|dict): Display label (optional, supports conditional)
            - dtype (str): Type conversion (optional)
            For text blocks:
            - content_generator (callable|str): Function that takes DataFrame and returns content
            - title (str): Display title (optional)
            - color (str|dict): Bootstrap theme color (optional, supports keyword-based conditional coloring)
              If dict: {'keyword1': 'color1', 'keyword2': 'color2', ...} - searches for keywords in content
        datasource: DataSource instance for block data
        subscribes_to: Optional state IDs to subscribe all blocks to
        row_options: Optional Bootstrap row styling options
        block_id_prefix: Prefix for generating block IDs (default: "metric")

    Returns:
        Tuple of (list of BaseBlock instances, row options dict)
        Ready for use with DashboardPage:
            page = DashboardPage(..., blocks=[(blocks, opts), ...])

    Example:
        blocks, row_opts = get_metric_row(
            metrics_spec={
                'revenue': {
                    'column': 'Revenue',
                    'agg': 'sum',
                    'title': 'Total Revenue',
                    'color': 'success'
                },
                'status': {
                    'content_generator': lambda df: f"Status: {df['status'].iloc[0]}",
                    'title': 'System Status',
                    'color': 'info'
                }
            },
            datasource=datasource,
            subscribes_to=['filters-category']
        )

        page = DashboardPage(..., blocks=[
            (blocks, row_opts),  # Mixed blocks row
            [chart1, chart2]  # Charts row
        ])
    """
    logger.info(
        f"[Blocks|Metrics|Factory] Creating dashboard row | "
        f"blocks_count={len(metrics_spec)}"
    )

    # <semantic_block: block_creation>
    blocks = []

    for block_id_key, block_spec in metrics_spec.items():
        # Generate unique block ID
        block_id = f"{block_id_prefix}-{block_id_key}"

        # Detect block type based on spec keys
        has_numeric_keys = "column" in block_spec and "agg" in block_spec
        has_text_keys = "content_generator" in block_spec

        # Validate: exactly one type must be specified
        if has_numeric_keys and has_text_keys:
            raise ValueError(
                f"Block '{block_id_key}' cannot have both numeric (column+agg) "
                f"and text (content_generator) keys. Specify exactly one type."
            )
        if not has_numeric_keys and not has_text_keys:
            raise ValueError(
                f"Block '{block_id_key}' must have either numeric keys (column+agg) "
                f"or text key (content_generator)."
            )

        # Create appropriate block type
        try:
            if has_numeric_keys:
                # Create SingleMetricBlock for numeric metrics
                block = SingleMetricBlock(
                    block_id=block_id,
                    datasource=datasource,
                    metric_spec=block_spec,
                    subscribes_to=subscribes_to,
                )
                block_type = "SingleMetricBlock"
            else:
                # Create TextBlock for text content
                # Extract TextBlock-specific parameters
                content_generator = block_spec["content_generator"]
                title = block_spec.get("title")
                color = block_spec.get("color")

                # Extract style parameters if provided
                card_style = block_spec.get("card_style")
                card_className = block_spec.get("card_className")
                title_style = block_spec.get("title_style")
                title_className = block_spec.get("title_className")
                content_style = block_spec.get("content_style")
                content_className = block_spec.get("content_className")
                loading_type = block_spec.get("loading_type", "default")

                block = TextBlock(
                    block_id=block_id,
                    datasource=datasource,
                    content_generator=content_generator,
                    subscribes_to=subscribes_to,
                    title=title,
                    card_style=card_style,
                    card_className=card_className,
                    title_style=title_style,
                    title_className=title_className,
                    content_style=content_style,
                    content_className=content_className,
                    loading_type=loading_type,
                    color=color,
                )
                block_type = "TextBlock"

            blocks.append(block)

            logger.debug(
                f"[Blocks|Metrics|Factory] Created {block_type} | "
                f"block_id={block_id} | title={block_spec.get('title', 'N/A')}"
            )

        except Exception as e:
            logger.error(
                f"[Blocks|Metrics|Factory] Failed to create block | "
                f"block_id={block_id_key} | error={e}"
            )
            raise

    # </semantic_block: block_creation>

    # <semantic_block: row_options>
    # Default row options: mb-4 spacing, no special alignment
    default_row_options = {"className": "mb-4"}

    # Merge with user-provided options
    final_row_options = {**default_row_options, **(row_options or {})}

    logger.info(
        f"[Blocks|Metrics|Factory] Dashboard row created | "
        f"blocks={len(blocks)} | row_opts={final_row_options}"
    )
    # </semantic_block: row_options>

    return blocks, final_row_options
