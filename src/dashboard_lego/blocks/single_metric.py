"""
SingleMetricBlock - Atomic block for displaying a single metric value.

This module implements the factory pattern component for metrics display.
Each instance calculates and renders ONE metric value in a compact card.

:hierarchy: [Blocks | Metrics | SingleMetricBlock]
:relates-to:
 - motivated_by: "SPEC: Metrics factory for layout integration"
 - implements: "class: 'SingleMetricBlock'"
 - uses: ["class: 'BaseBlock'", "class: 'ThemeConfig'"]

:contract:
 - pre: "One metric_spec dict, datasource, optional subscribes_to"
 - post: "layout() returns dbc.Card with metric value"
 - invariant: "Card is compact (height determined by content only)"
 - theme_compliance: "color Bootstrap theme, via ThemeConfig"

:complexity: 4
:decision_cache: "atomic_metrics: Independent blocks for flexibility"
"""

from typing import Any, Dict, List, Union

import dash_bootstrap_components as dbc
import pandas as pd
from dash import html
from dash.development.base_component import Component

from dashboard_lego.blocks.base import BaseBlock
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.utils.formatting import format_number


class SingleMetricBlock(BaseBlock):
    """
    Display a single aggregated metric value in a compact card.

    :hierarchy: [Blocks | Metrics | SingleMetricBlock]
    :relates-to:
     - motivated_by: "Factory pattern: atomic metric blocks"
     - implements: "class: 'SingleMetricBlock'"

    :contract:
     - pre: "metric_spec contains column, agg, title, optional color"
     - post: "Renders compact card with metric value"
     - invariant: "Card height adapts to content (no fixed height)"
     - theme_compliance: "Uses ThemeConfig for colors"

    :complexity: 4

    Example:
        metric = SingleMetricBlock(
            block_id="revenue_metric",
            datasource=datasource,
            metric_spec={
                'column': 'Revenue',
                'agg': 'sum',
                'title': 'Total Revenue',
                'color': 'success',  # Bootstrap theme color
                'dtype': 'float64'
            },
            subscribes_to=['control-category']
        )
    """

    def __init__(
        self,
        block_id: str,
        datasource: DataSource,
        metric_spec: Dict[str, Any],
        subscribes_to: Union[str, List[str], None] = None,
        **kwargs,
    ):
        """
        Initialize SingleMetricBlock.

        :hierarchy: [Blocks | Metrics | SingleMetricBlock | Init]
        :contract:
         - pre: "metric_spec has required keys: column, agg, title"
         - post: "Block registered with state manager"

        Args:
            block_id: Unique block identifier
            datasource: DataSource instance
            metric_spec: Metric definition with keys:
                - column (str): Column name to aggregate
                - agg (str|Callable): Aggregation func
                - title (str): Display title
                - color (str): Bootstrap color (optional)
                - dtype (str): Type conversion (optional)
                - color_rules (dict): Conditional coloring (optional)
            subscribes_to: State IDs to subscribe to
        """
        self.metric_spec = metric_spec

        # Validate required keys
        required_keys = {"column", "agg", "title"}
        if not required_keys.issubset(metric_spec.keys()):
            missing = required_keys - metric_spec.keys()
            raise ValueError(f"metric_spec missing required keys: {missing}")

        # Build subscribes dict
        state_ids = self._normalize_subscribes_to(subscribes_to)
        subscribes_dict = {state: self._update_metric for state in state_ids}

        # Pass to parent
        super().__init__(block_id, datasource, subscribes=subscribes_dict, **kwargs)

        self.logger.debug(
            f"[Blocks|Metrics|SingleMetricBlock] Initialized | "
            f"block_id={block_id} | metric={metric_spec.get('title')}"
        )

    def _calculate_metric(self, df: pd.DataFrame) -> float:
        """
        Calculate metric value from DataFrame.

        :hierarchy: [Blocks | Metrics | SingleMetricBlock | Calculate]
        :relates-to:
         - motivated_by: "Metric calculation logic reused from MetricsBlock"
         - implements: "method: '_calculate_metric'"

        :contract:
         - pre: "df is filtered DataFrame"
         - post: "Returns numeric metric value"
         - agg_types: "Supports str ('sum', 'mean', etc.) or callable"

        :complexity: 3

        Args:
            df: Filtered DataFrame

        Returns:
            Calculated metric value (float)
        """
        column = self.metric_spec["column"]
        agg = self.metric_spec["agg"]
        dtype = self.metric_spec.get("dtype")

        if df.empty or column not in df.columns:
            self.logger.warning(
                f"[Blocks|Metrics|SingleMetricBlock] Empty data or "
                f"missing column: {column}"
            )
            return 0.0

        # Get column data
        series = df[column]

        # Apply dtype conversion if specified
        if dtype is not None:
            try:
                series = series.astype(dtype)
            except Exception as e:
                self.logger.warning(
                    f"[Blocks|Metrics|SingleMetricBlock] dtype conversion "
                    f"failed: {e}"
                )

        # Calculate metric
        try:
            if callable(agg):
                value = agg(series)
            elif isinstance(agg, str):
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
                self.logger.warning(f"Invalid agg type: {type(agg)}")
                value = 0.0

            self.logger.debug(
                f"[Blocks|Metrics|SingleMetricBlock] Calculated | "
                f"column={column} | agg={agg} | value={value}"
            )
            return value

        except Exception as e:
            self.logger.error(
                f"[Blocks|Metrics|SingleMetricBlock] Calculation error: {e}"
            )
            return 0.0

    def _determine_color(
        self, value: float, color_spec: Union[str, Dict[str, Any]]
    ) -> str:
        """
        Determine Bootstrap theme color for metric value.

        :hierarchy: [Blocks | Metrics | SingleMetricBlock | ColorResolution]
        :relates-to:
         - motivated_by: "SPEC: Theme-aware conditional coloring"
         - implements: "method: '_determine_color'"

        :contract:
         - pre: "color_spec is str or dict with thresholds"
         - post: "Returns Bootstrap theme color name"
         - theme_compliance: "Returns only valid Bootstrap colors"

        :complexity: 2
        :decision_cache: "conditional_coloring: Threshold rules"

        Args:
            value: Calculated metric value
            color_spec: Either:
                - str: Bootstrap color name ('primary', 'success', etc.)
                - dict: {'thresholds': [...], 'colors': [...]}

        Returns:
            Bootstrap theme color name
        """
        if isinstance(color_spec, str):
            return color_spec

        if isinstance(color_spec, dict) and "thresholds" in color_spec:
            thresholds = color_spec["thresholds"]
            colors = color_spec["colors"]

            for i, threshold in enumerate(thresholds):
                if value < threshold:
                    return colors[i]

            # Value exceeds all thresholds
            return colors[-1]

        # Fallback
        return "primary"

    def _render_card(self, value: float, color: str) -> Component:
        """
        Render metric card with theme-aware styling.

        :hierarchy: [Blocks | Metrics | SingleMetricBlock | Render]
        :relates-to:
         - motivated_by: "Layout contract: Card h-100 for flexbox"
         - implements: "method: '_render_card'"

        :contract:
         - pre: "value is calculated, color is Bootstrap theme name"
         - post: "Returns dbc.Card with h-100 class"
         - invariant: "No fixed height, uses ThemeConfig for styling"

        :complexity: 3
        :decision_cache: "compact_cards: No fixed height"

        Args:
            value: Metric value
            color: Bootstrap theme color name

        Returns:
            dbc.Card component
        """
        title = self.metric_spec["title"]

        # Get theme-aware styles
        if self.theme_config:
            # Card background using theme color
            color_map = {
                "primary": self.theme_config.colors.primary,
                "secondary": self.theme_config.colors.secondary,
                "success": self.theme_config.colors.success,
                "danger": self.theme_config.colors.danger,
                "warning": self.theme_config.colors.warning,
                "info": self.theme_config.colors.info,
            }
            bg_color = color_map.get(color, self.theme_config.colors.primary)

            card_style = {
                "backgroundColor": bg_color,
                "color": self.theme_config.colors.white,
                "borderRadius": self.theme_config.spacing.border_radius,
                "padding": self.theme_config.spacing.card_padding,
            }

            value_style = {
                "fontSize": self.theme_config.typography.font_size_h2,
                "fontWeight": self.theme_config.typography.font_weight_bold,
            }

            title_style = {
                "fontSize": self.theme_config.typography.font_size_sm,
                "opacity": "0.9",
            }
        else:
            # Fallback to Bootstrap classes
            card_style = None
            value_style = None
            title_style = None

        # Build card with h-100 for flexbox
        card_body = dbc.CardBody(
            [
                html.H6(title, className="mb-2", style=title_style),
                html.H3(format_number(value), className="mb-0", style=value_style),
            ]
        )

        card_className = "text-center h-100"
        if not self.theme_config:
            card_className += f" text-white bg-{color}"

        return dbc.Card(
            card_body,
            className=card_className,
            style=card_style if self.theme_config else None,
        )

    def _update_metric(self, *args) -> Component:
        """
        Update metric display (callback handler).

        :hierarchy: [Blocks | Metrics | SingleMetricBlock | Update]
        :relates-to:
         - motivated_by: "BaseBlock callback mechanism"
         - implements: "method: '_update_metric'"

        :contract:
         - pre: "Subscribed state values in *args"
         - post: "Returns updated card component"

        :complexity: 2

        Args:
            *args: State values from subscribed controls

        Returns:
            Updated dbc.Card component
        """
        # Build params dict from args
        params = {}
        if args and hasattr(self, "subscribes"):
            state_ids = list(self.subscribes.keys())
            for idx, value in enumerate(args):
                if idx < len(state_ids):
                    params[state_ids[idx]] = value

        self.logger.debug(
            f"[Blocks|Metrics|SingleMetricBlock] Update triggered | " f"params={params}"
        )

        # Get filtered data
        df = self.datasource.get_processed_data(params)

        # Calculate metric
        value = self._calculate_metric(df)

        # Determine color (support conditional coloring)
        color_spec = self.metric_spec.get("color", "primary")
        if isinstance(color_spec, dict):
            color = self._determine_color(value, color_spec)
        else:
            color = color_spec

        # Render card
        return self._render_card(value, color)

    def layout(self) -> Component:
        """
        Render initial layout with callback-compatible container.

        CRITICAL: Must wrap metric card in Div with id=block_id-container
        to match BaseBlock.output_target() contract for callbacks.

        :hierarchy: [Blocks | Metrics | SingleMetricBlock | Layout]
        :relates-to:
         - motivated_by: "BaseBlock lifecycle contract requires container ID"
         - implements: "method: 'layout'"
         - uses: ["method: '_generate_id'", "method: '_update_metric'"]

        :contract:
         - pre: "Block initialized with navigation_mode and section_index"
         - post: "Returns Div(id=block_id-container) wrapping metric card"
         - invariant: "Container ID matches output_target() for callbacks"
         - spec_compliance: "Dash callback Output target must exist in DOM"

        :complexity: 2
        :decision_cache: "Wrap in container Div to enable state-centric callbacks"

        Returns:
            html.Div wrapping dbc.Card (not Card directly!)
        """
        self.logger.debug(
            f"[Blocks|Metrics|SingleMetricBlock] Rendering layout | "
            f"block_id={self.block_id}"
        )

        # CRITICAL: Wrap card in Div with id matching output_target()
        # This enables Dash callbacks to find the component
        # h-100 ensures equal height when multiple metrics in same row
        return html.Div(
            id=self._generate_id("container"),
            children=self._update_metric(),
            className="h-100",
        )
