"""
Sidebar building methods for DashboardPage.

:hierarchy: [Core | Page | Sidebar Builder]
:complexity: 3
"""

from typing import List

from dash.development.base_component import Component


class SidebarBuilderMixin:
    """
    Mixin providing sidebar building methods for DashboardPage.

    :hierarchy: [Core | Page | Sidebar Builder | Mixin]
    :relates-to:
     - motivated_by: "Decomposition: Extract sidebar logic from DashboardPage"
     - implements: "Mixin: SidebarBuilderMixin"
     - uses: ["class: 'BaseBlock'"]

    :rationale: "Separates sidebar building concerns from core page logic."
    :contract:
     - pre: "Class has sidebar, state_manager, logger attributes"
     - post: "Provides methods for rendering sidebar blocks"
    """

    def _render_sidebar_blocks(self) -> List[Component]:
        """
        Render sidebar blocks with fixed IDs.

        :hierarchy: [Core | Layout | Sidebar | RenderBlocks]
        :relates-to:
         - motivated_by: "SidebarConfig requires rendering blocks with fixed IDs"
         - uses: ["class: 'BaseBlock'"]

        :contract:
         - pre: "self.sidebar is not None and contains valid blocks"
         - post: "List of rendered Dash components for sidebar content"
         - invariant: "All sidebar blocks have is_sidebar_block=True"

        :complexity: 3

        :returns:
         - List[Component]: Rendered sidebar block components
        """
        self.logger.debug(
            f"[Core|Sidebar|RenderBlocks] Rendering {len(self.sidebar.blocks)} sidebar blocks"
        )

        rendered_blocks = []

        # <semantic_block: sidebar_block_rendering>
        for idx, block in enumerate(self.sidebar.blocks):
            # Mark as sidebar block for fixed ID generation
            block.is_sidebar_block = True
            block.navigation_mode = False  # No pattern-matching

            self.logger.debug(
                f"[Core|Sidebar|RenderBlocks] Block {idx}: {block.block_id} | "
                f"is_sidebar_block=True"
            )

            # Register state interactions (publishers/subscribers)
            block._register_state_interactions(self.state_manager)

            # Render block layout
            rendered = block.layout()
            rendered_blocks.append(rendered)
        # </semantic_block: sidebar_block_rendering>

        self.logger.info(
            f"[Core|Sidebar|RenderBlocks] Rendered {len(rendered_blocks)} blocks successfully"
        )

        return rendered_blocks
