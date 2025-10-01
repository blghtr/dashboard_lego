"""
This module defines the TextBlock for displaying text content.

"""

from typing import Any, Callable, Optional

import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html
from dash.development.base_component import Component

from dashboard_lego.blocks.base import BaseBlock


class TextBlock(BaseBlock):
    """
    A block for displaying dynamic text content, with support for Markdown.

    This block subscribes to a state and uses a generator function to render
    its content based on the data from a datasource.

        :hierarchy: [Blocks | Text | TextBlock]
        :relates-to:
          - motivated_by: "Architectural Conclusion: Dynamic text blocks are essential
            for displaying model summaries and other formatted content"
          - implements: "block: 'TextBlock'"
          - uses: ["interface: 'BaseBlock'"]

        :contract:
          - pre: "A `subscribes_to` state ID and a `content_generator` function must be provided."
          - post: "The block renders a card with content that updates on state change."

        :rationale: "Refactored from a static block to a dynamic one to be consistent with other blocks like StaticChartBlock and to support data-driven text content."

    """

    def __init__(
        self,
        block_id: str,
        datasource: Any,
        subscribes_to: str,
        content_generator: Callable[[pd.DataFrame], Component | str],
        title: Optional[str] = None,
    ):
        """
        Initializes the TextBlock.

        Args:
            block_id: A unique identifier for this block instance.
            datasource: An instance of a class that implements the BaseDataSource interface.
            subscribes_to: The state ID to which this block subscribes to receive updates.
            content_generator: A function that takes a DataFrame and returns a Dash Component or a Markdown string.
            title: An optional title for the block's card.

        """
        self.title = title
        self.content_generator = content_generator
        super().__init__(
            block_id, datasource, subscribes={subscribes_to: self._update_content}
        )

    def _update_content(self, *args) -> Component:
        """
        Callback function to update the block's content based on datasource changes.

        """
        try:
            df = self.datasource.get_processed_data()
            generated_content = self.content_generator(df)

            # If the generator returns a string, wrap it in dcc.Markdown
            if isinstance(generated_content, str):
                content_component = dcc.Markdown(generated_content)
            else:
                content_component = generated_content

            children = [content_component]
            if self.title:
                children.insert(0, html.H4(self.title, className="card-title"))

            return dbc.CardBody(children)
        except Exception as e:
            return dbc.Alert(
                f"Ошибка генерации текстового блока: {str(e)}", color="danger"
            )

    def layout(self) -> Component:
        """
        Defines the initial layout of the block, including a loading wrapper.

        """
        # Initialize with current content instead of empty container
        initial_content = self._update_content()
        return dbc.Card(
            dcc.Loading(
                id=self._generate_id("loading"),
                type="default",
                children=html.Div(
                    id=self._generate_id("container"), children=initial_content
                ),
            ),
            className="mb-4",
        )
