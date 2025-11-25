"""
This module defines the TextBlock for displaying text content.

"""

from typing import Any, Callable, Dict, List, Optional, Union

import dash_bootstrap_components as dbc
import pandas as pd
from dash import dcc, html
from dash.development.base_component import Component

from dashboard_lego.blocks.base import BaseBlock


class TextBlock(BaseBlock):
    """
    A block for displaying dynamic or static text content, with support for
    Markdown and customizable styling.

    This block optionally subscribes to a state and uses a generator function
    to render its content based on the data from a datasource.

        :hierarchy: [Blocks | Text | TextBlock]
        :relates-to:
          - motivated_by: "Architectural Conclusion: Dynamic text blocks are
            essential for displaying model summaries and other formatted
            content with customizable styling"
          - implements: "block: 'TextBlock'"
          - uses: ["interface: 'BaseBlock'"]

        :rationale: "Enhanced with style customization parameters to allow
         fine-grained control over text block appearance while maintaining
         backward compatibility. subscribes_to is now optional."
        :contract:
          - pre: "A `content_generator` function or string must be provided.
            `subscribes_to` is optional."
          - post: "The block renders a card with content that updates on state
            change (if subscribed) or displays static content with customizable
            styling applied."

    """

    def __init__(
        self,
        block_id: str,
        datasource: Any,
        content_generator: Union[Callable[[pd.DataFrame], Component | str], str],
        subscribes_to: Union[str, List[str], None] = None,
        title: Optional[str] = None,
        # Style customization parameters
        card_style: Optional[Dict[str, Any]] = None,
        card_className: Optional[str] = None,
        title_style: Optional[Dict[str, Any]] = None,
        title_className: Optional[str] = None,
        content_style: Optional[Dict[str, Any]] = None,
        content_className: Optional[str] = None,
        loading_type: str = "default",
        # Color specification (supports conditional coloring)
        color: Optional[Union[str, Dict[str, Any]]] = None,
    ):
        """
        Initializes the TextBlock with customizable styling.

        Args:
            block_id: A unique identifier for this block instance.
            datasource: An instance of a class that implements the
                DataSource interface.
            content_generator: A function that takes a DataFrame and returns a
                Dash Component or a Markdown string, or a static string for fixed content.
            subscribes_to: Optional state ID(s) to which this block subscribes
                to receive updates. Can be a single state ID string, a list of
                state IDs, or None for static content. Defaults to None.
            title: An optional title for the block's card.
            card_style: Optional style dictionary for the card component.
            card_className: Optional CSS class name for the card component.
            title_style: Optional style dictionary for the title component.
            title_className: Optional CSS class name for the title component.
            content_style: Optional style dictionary for the content container.
            content_className: Optional CSS class name for the content
                container.
            loading_type: Type of loading indicator to display.
            color: Optional color specification. Can be:
                - str: Bootstrap theme color name ('primary', 'success', etc.)
                - dict: Keyword-based coloring with {'keyword1': 'color1', 'keyword2': 'color2', ...}
                  Searches for keywords in generated content (case-insensitive)

        """
        self.title = title

        # Handle both callable and static string content
        if isinstance(content_generator, str):
            # Static content: create a lambda that returns the string
            self.content_generator = lambda df: content_generator
        else:
            # Callable content generator
            self.content_generator = content_generator

        # Store style customization parameters
        self.card_style = card_style
        self.card_className = card_className
        self.title_style = title_style
        self.title_className = title_className
        self.content_style = content_style
        self.content_className = content_className
        self.loading_type = loading_type
        self.color = color

        # Normalize subscribes_to to list and build subscribes dict
        state_ids = self._normalize_subscribes_to(subscribes_to)
        subscribes_dict = {state_id: self._update_content for state_id in state_ids}

        super().__init__(block_id, datasource, subscribes=subscribes_dict)

    def _determine_color(
        self, content: str, color_spec: Union[str, Dict[str, str]]
    ) -> str:
        """
        Determine Bootstrap theme color based on keyword matching in content.

        :hierarchy: [Blocks | Text | TextBlock | ColorResolution]
        :relates-to:
         - motivated_by: "PRD: Conditional color assignment based on keywords in text content"
         - implements: "method: '_determine_color'"

        :contract:
         - pre: "color_spec is str or dict with keyword:color mapping"
         - post: "Returns Bootstrap theme color name"
         - theme_compliance: "Returns only valid Bootstrap colors"

        :complexity: 2
        :decision_cache: "keyword_based_coloring: Simple keyword matching for text content"

        Args:
            content: Text content to search for keywords
            color_spec: Either:
                - str: Bootstrap color name ('primary', 'success', etc.)
                - dict: {'keyword1': 'color1', 'keyword2': 'color2', ...}

        Returns:
            Bootstrap theme color name
        """
        if isinstance(color_spec, str):
            return color_spec

        if isinstance(color_spec, dict):
            # Search for keywords in content (case-insensitive)
            content_lower = content.lower()
            for keyword, color in color_spec.items():
                if keyword.lower() in content_lower:
                    return color

        # Fallback if no keyword matches
        return "primary"

    def _update_content(self, *args) -> Component:
        """
        Callback function to update the block's content based on datasource
        changes with customizable styling.

        :hierarchy: [Blocks | Text | TextBlock | Update Logic]
        :relates-to:
         - motivated_by: "PRD: Need to display dynamic text content with
           customizable styling and conditional coloring"
         - implements: "method: '_update_content' with style overrides and color support"
         - uses: ["attribute: 'content_generator'", "attribute: 'title_style'", "method: '_determine_color'"]

        :rationale: "Enhanced to apply style customization parameters to
         content and title components. Works for both subscribed and
         non-subscribed blocks. Supports conditional coloring via color parameter."
        :contract:
         - pre: "Datasource is available and content generator is set."
         - post: "Returns a styled CardBody with current content and title."

        """
        try:
            # Build params dict from args for filtered data
            params = {}
            if args and hasattr(self, "subscribes"):
                state_ids = list(self.subscribes.keys())
                for idx, value in enumerate(args):
                    if idx < len(state_ids):
                        params[state_ids[idx]] = value

            df = self._get_data_sync(params)
            generated_content = self.content_generator(df)

            # If the generator returns a string, wrap it in dcc.Markdown
            if isinstance(generated_content, str):
                content_component = dcc.Markdown(generated_content)
            else:
                content_component = generated_content

            # Apply content styling if provided
            if self.content_style or self.content_className:
                content_props = {}
                if self.content_style:
                    content_props["style"] = self.content_style
                if self.content_className:
                    content_props["className"] = self.content_className
                content_component = html.Div(content_component, **content_props)

            children = [content_component]
            if self.title:
                # Build title props with style overrides
                title_props = {
                    "className": self.title_className or "card-title",
                }
                if self.title_style:
                    title_props["style"] = self.title_style
                children.insert(0, html.H4(self.title, **title_props))

            return dbc.CardBody(children)
        except Exception as e:
            return dbc.Alert(f"Error generating text block: {str(e)}", color="danger")

    def layout(self) -> Component:
        """
        Defines the initial layout of the block with theme-aware styling.

        :hierarchy: [Blocks | Text | TextBlock | Layout]
        :relates-to:
         - motivated_by: "PRD: Automatic theme application to text blocks"
         - implements: "method: 'layout' with theme integration"
         - uses: ["method: '_get_themed_style'", "attribute: 'card_style'"]

        :rationale: "Uses theme system for consistent styling with user override capability."
        :contract:
         - pre: "Block is properly initialized, theme_config may be available."
         - post: "Returns a themed Card component with automatic styling."

        """
        # Initialize with current content instead of empty container
        initial_content = self._update_content()

        # Determine color if specified (for conditional coloring based on keywords)
        color_to_apply = None
        if self.color:
            if isinstance(self.color, dict):
                # Keyword-based coloring: extract text content and search for keywords
                try:
                    df = self.datasource.get_processed_data()
                    generated_content = self.content_generator(df)

                    # Convert content to string for keyword search
                    if isinstance(generated_content, str):
                        content_text = generated_content
                    else:
                        # If it's a Component, try to extract text from it
                        # For now, use a fallback - in practice, content_generator should return string
                        content_text = str(generated_content)

                    color_to_apply = self._determine_color(content_text, self.color)
                except Exception as e:
                    self.logger.warning(
                        f"[Blocks|Text|TextBlock] Failed to determine color from content: {e}"
                    )
                    color_to_apply = "primary"
            else:
                # Direct color specification
                color_to_apply = self.color

        # Build card style with color if specified
        card_style_with_color = self.card_style.copy() if self.card_style else {}
        if color_to_apply and self.theme_config:
            # Apply theme color to card background
            color_map = {
                "primary": self.theme_config.colors.primary,
                "secondary": self.theme_config.colors.secondary,
                "success": self.theme_config.colors.success,
                "danger": self.theme_config.colors.danger,
                "warning": self.theme_config.colors.warning,
                "info": self.theme_config.colors.info,
            }
            bg_color = color_map.get(color_to_apply, self.theme_config.colors.primary)
            card_style_with_color["backgroundColor"] = bg_color
            card_style_with_color["color"] = self.theme_config.colors.white

        # Build card props with theme-aware style
        themed_card_style = self._get_themed_style(
            "card",
            "background",
            card_style_with_color if card_style_with_color else None,
        )
        # h-100 ensures equal height when multiple blocks in same row
        # Note: mb-4 removed, handled by Row.mb-4
        base_classes = "h-100"
        card_class_name = base_classes
        if color_to_apply and not self.theme_config:
            # Fallback to Bootstrap classes if no theme
            card_class_name += f" text-white bg-{color_to_apply}"
        if self.card_className:
            card_class_name += f" {self.card_className}"

        card_props = {"className": card_class_name}
        if themed_card_style:
            card_props["style"] = themed_card_style

        return dbc.Card(
            dcc.Loading(
                id=self._generate_id("loading"),
                type=self.loading_type,
                children=html.Div(
                    id=self._generate_id("container"), children=initial_content
                ),
            ),
            **card_props,
        )
