"""
This module defines the DashboardPage class, which orchestrates blocks on a page.

"""
from typing import List, Any

import dash_bootstrap_components as dbc
from dash import html
from dash.development.base_component import Component

from blocks.base import BaseBlock
from core.state import StateManager

class DashboardPage:
    """
    Orchestrates the assembly of a dashboard page from a list of blocks.

        :hierarchy: [Feature | Layout System | Page Modification]
        :relates-to:
          - motivated_by: "Architectural Conclusion: Provide a flexible grid-based layout system"
          - implements: "class: 'DashboardPage'"
          - uses: ["interface: 'BaseBlock'", "class: 'StateManager'"]

        :rationale: "The page now accepts a nested list structure for layout definition and builds a Bootstrap grid, offering a balance of power and simplicity."
        :contract:
         - pre: "`blocks` must be a list of lists, where each inner item is a BaseBlock or a (BaseBlock, dict) tuple."
         - post: "A complete Dash layout with a grid structure can be retrieved."

    """

    def __init__(self, title: str, blocks: List[List[Any]], theme: str = dbc.themes.BOOTSTRAP):
        """
        Initializes the DashboardPage, creates a StateManager, and registers all blocks.

        Args:
            title: The main title of the dashboard page.
            blocks: A list of lists representing rows. Each item in a row is either a
                    BaseBlock instance or a tuple of (BaseBlock, dict_of_col_props).
                    Example: [[block1], [(block2, {'width': 8}), (block3, {'width': 4})]]
            theme: An optional URL to a dash-bootstrap-components theme (e.g., dbc.themes.CYBORG).

        """
        self.title = title
        self.theme = theme
        self.layout_structure = blocks
        self.state_manager = StateManager()

        # Flatten the structure to get all block instances for registration
        self.blocks: List[BaseBlock] = []
        for row in self.layout_structure:
            for item in row:
                block = item[0] if isinstance(item, tuple) else item
                if not isinstance(block, BaseBlock):
                    raise TypeError("All layout items must be of type BaseBlock.")
                self.blocks.append(block)

        # Register all blocks with the state manager
        for block in self.blocks:
            block._register_state_interactions(self.state_manager)

    def build_layout(self) -> Component:
        """
        Assembles the layouts from all blocks into a grid-based page layout.

        Returns:
            A Dash component representing the entire page.

        """
        rows = []
        for row_items in self.layout_structure:
            cols = []
            for item in row_items:
                if isinstance(item, tuple):
                    block, col_props = item
                else:
                    block, col_props = item, {}
                
                # If no width is specified, assign it automatically
                if not any(prop in col_props for prop in ['width', 'lg', 'md', 'sm', 'xs']):
                    col_props['width'] = 12 // len(row_items)

                cols.append(dbc.Col(block.layout(), **col_props))
            rows.append(dbc.Row(cols, className="mb-4"))

        return dbc.Container(
            [
                html.H1(self.title, className="my-4"),
                *rows
            ],
            fluid=True
        )

    def register_callbacks(self, app: Any):
        """
        Delegates the callback generation and registration to the StateManager.

        Args:
            app: The Dash app instance.

        """
        self.state_manager.generate_callbacks(app)
