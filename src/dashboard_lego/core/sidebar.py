"""
Sidebar configuration module for dashboard_lego.

This module defines the configuration for collapsible sidebars that contain
global controls or navigation elements with fixed (non-pattern-matched) IDs.

:hierarchy: [Core | Layout | Sidebar]
:relates-to:
 - motivated_by: "Cross-section pattern-matching State() resolution conflict"
 - enables: ["class: 'DashboardPage'"]
 - uses: ["class: 'BaseBlock'"]

:contract:
 - pre: "Sidebar blocks must be BaseBlock instances"
 - post: "SidebarConfig provides validated configuration for sidebar rendering"
 - invariant: "Sidebar blocks receive fixed string IDs (no section dict)"

:complexity: 3
:decision_cache: "sidebar_architecture: Chose dbc.Offcanvas over custom div for mobile-responsiveness and accessibility (DBC best practices)"
"""

from dataclasses import dataclass, field
from typing import Any, List, Optional

from dashboard_lego.utils.logger import get_logger

logger = get_logger(__name__)


@dataclass
class SidebarConfig:
    """
    Configuration for collapsible sidebar with global controls.

    Sidebar blocks use fixed string IDs (not pattern-matched with section dicts),
    enabling cross-section State() subscriptions that work with pattern-matching callbacks.

    :hierarchy: [Core | Layout | SidebarConfig]
    :relates-to:
     - motivated_by: "Pattern-matching callbacks cannot resolve State() from other sections"
     - implements: "feature: 'Collapsible Sidebar'"
     - uses: ["class: 'BaseBlock'"]

    :contract:
     - pre: "blocks list contains only BaseBlock instances"
     - post: "Valid sidebar configuration for DashboardPage"
     - invariant: "Sidebar blocks always get fixed IDs (is_sidebar_block=True)"

    :complexity: 2

    :params:
     - blocks (List[BaseBlock]): List of blocks to render in sidebar
     - collapsible (bool): Enable collapse/expand toggle button
     - width (str): CSS width value (e.g., "300px", "20%")
     - position (str): Placement - "start" (left) or "end" (right)
     - default_collapsed (bool): Initial collapsed state
     - title (Optional[str]): Sidebar header title
     - backdrop (bool): Show backdrop overlay when open (mobile UX)

    :example:
        ```python
        sidebar = SidebarConfig(
            blocks=[control_panel],
            collapsible=True,
            width="280px",
            title="Global Filters"
        )
        page = DashboardPage(sidebar=sidebar, navigation=nav_config)
        ```
    """

    blocks: List[Any] = field(default_factory=list)
    collapsible: bool = True
    width: str = "300px"
    position: str = "start"  # 'start' (left) or 'end' (right)
    default_collapsed: bool = False
    title: Optional[str] = None
    backdrop: bool = False  # No backdrop for persistent sidebar

    def __post_init__(self):
        """
        Validate configuration after initialization.

        :hierarchy: [Core | Layout | SidebarConfig | Validation]
        :contract:
         - pre: "Dataclass fields initialized"
         - post: "Configuration validated or ValueError raised"

        :raises:
         - ValueError: If blocks list is empty or contains non-BaseBlock
         - ValueError: If position not in ['start', 'end']
        """
        logger.debug(
            f"[Core|Sidebar|SidebarConfig] Initializing | "
            f"blocks={len(self.blocks)} collapsible={self.collapsible}"
        )

        # <semantic_block: validation>
        if not self.blocks:
            logger.error(
                "[Core|Sidebar|SidebarConfig] Validation failed: empty blocks list"
            )
            raise ValueError("SidebarConfig.blocks cannot be empty")

        if self.position not in ["start", "end"]:
            logger.error(
                f"[Core|Sidebar|SidebarConfig] Invalid position: {self.position}"
            )
            raise ValueError("position must be 'start' or 'end'")

        # Validate blocks are BaseBlock instances (lazy import to avoid circular)
        from dashboard_lego.blocks.base import BaseBlock

        for idx, block in enumerate(self.blocks):
            if not isinstance(block, BaseBlock):
                logger.error(
                    f"[Core|Sidebar|SidebarConfig] Block {idx} invalid type: {type(block)}"
                )
                raise ValueError(
                    f"All sidebar blocks must be BaseBlock instances. "
                    f"Got {type(block)} at index {idx}"
                )
        # </semantic_block: validation>

        logger.info(
            f"[Core|Sidebar|SidebarConfig] Configuration validated | "
            f"blocks={len(self.blocks)} position={self.position} width={self.width}"
        )
