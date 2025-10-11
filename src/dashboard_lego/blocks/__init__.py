"""
Blocks module - dashboard visual components.

v0.15.0: StaticChartBlock and InteractiveChartBlock removed.
v0.15.0: Added SingleMetricBlock and get_metric_row() factory.

:hierarchy: [Blocks]
:relates-to:
 - motivated_by: "v0.15.0: Factory pattern for metrics layout"
 - exports: "TypedChartBlock, SingleMetricBlock, get_metric_row"
"""

from dashboard_lego.blocks.control_panel import Control, ControlPanelBlock
from dashboard_lego.blocks.metrics_factory import get_metric_row
from dashboard_lego.blocks.single_metric import SingleMetricBlock
from dashboard_lego.blocks.text import TextBlock
from dashboard_lego.blocks.typed_chart import TypedChartBlock

__all__ = [
    "TypedChartBlock",  # v0.15.0
    "ControlPanelBlock",
    "Control",
    "SingleMetricBlock",  # NEW in v0.15.1
    "get_metric_row",  # NEW in v0.15.1 (factory function)
    "TextBlock",
    # REMOVED in v0.15.0:
    # - StaticChartBlock (use TypedChartBlock)
    # - InteractiveChartBlock (use TypedChartBlock with controls)
    # REMOVED in v0.15.1:
    # - KPIBlock (use get_metric_row)
    # - MetricsBlock (use get_metric_row)
]
