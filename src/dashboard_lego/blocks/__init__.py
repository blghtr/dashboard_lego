"""
Blocks module - dashboard visual components.

v0.15.0: StaticChartBlock and InteractiveChartBlock removed.
Use TypedChartBlock instead.

:hierarchy: [Blocks]
:relates-to:
 - motivated_by: "v0.15.0: Simplified chart API with plot registry"
 - exports: "TypedChartBlock, ControlPanelBlock, KPIBlock, MetricsBlock, TextBlock, Control"
"""

from dashboard_lego.blocks.control_panel import Control, ControlPanelBlock
from dashboard_lego.blocks.kpi import KPIBlock
from dashboard_lego.blocks.metrics import MetricsBlock
from dashboard_lego.blocks.text import TextBlock
from dashboard_lego.blocks.typed_chart import TypedChartBlock

__all__ = [
    "TypedChartBlock",  # NEW in v0.15.0
    "ControlPanelBlock",
    "Control",
    "KPIBlock",
    "MetricsBlock",  # NEW - replaces get_kpis() approach
    "TextBlock",
    # REMOVED in v0.15.0:
    # - StaticChartBlock (use TypedChartBlock)
    # - InteractiveChartBlock (use TypedChartBlock with controls)
]
