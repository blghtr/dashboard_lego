"""
Unit tests for the TextBlock class.

"""

import dash_bootstrap_components as dbc
import pytest
from dash import dcc, html

from dashboard_lego.blocks.text import TextBlock


def test_text_block_layout(datasource_factory):
    """
    Tests the basic layout structure of the TextBlock.
    """
    mock_ds = datasource_factory()
    block = TextBlock(
        block_id="test_text",
        datasource=mock_ds,
        subscribes_to="dummy_state",
        content_generator=lambda df: "Test",
    )
    layout = block.layout()
    assert isinstance(layout, dbc.Card)
    assert isinstance(layout.children, dcc.Loading)


def test_text_block_content_update(datasource_factory):
    """
    Tests that the content is correctly generated and updated.
    """
    content = "This is the main content."
    mock_ds = datasource_factory()
    block = TextBlock(
        block_id="test_text",
        datasource=mock_ds,
        subscribes_to="dummy_state",
        content_generator=lambda df: content,
    )

    # The layout is built, but the callback that generates the content is not yet called.
    # We call the internal update method directly to test the content generation logic.
    updated_content_card = block._update_content()
    assert isinstance(updated_content_card, dbc.CardBody)

    # The card body should contain the markdown component
    markdown = updated_content_card.children[0]
    assert isinstance(markdown, dcc.Markdown)
    assert markdown.children == content


def test_text_block_with_title(datasource_factory):
    """
    Tests that the title is correctly included when provided.
    """
    title = "My Title"
    content = "*Markdown* content."
    mock_ds = datasource_factory()
    block = TextBlock(
        block_id="test_text_2",
        datasource=mock_ds,
        subscribes_to="dummy_state",
        content_generator=lambda df: content,
        title=title,
    )

    updated_content_card = block._update_content()
    assert isinstance(updated_content_card, dbc.CardBody)

    # Should contain H4 title and Markdown content
    assert len(updated_content_card.children) == 2

    h4_title = updated_content_card.children[0]
    assert isinstance(h4_title, html.H4)
    assert h4_title.children == title

    markdown = updated_content_card.children[1]
    assert isinstance(markdown, dcc.Markdown)
    assert markdown.children == content


def test_text_block_list_subscription(datasource_factory):
    """
    Tests that TextBlock can subscribe to multiple states.

    :hierarchy: [Testing | Unit Tests | Blocks | TextBlock | Multi-State]
    :covers:
     - object: "TextBlock with list subscription"
     - requirement: "Bug Fix: Support subscribing to multiple states"

    :scenario: "Verifies that TextBlock can subscribe to multiple states
     using a list parameter without causing TypeError."
    :strategy: "Create TextBlock with list subscription and verify
     subscribes dict is created correctly."
    :contract:
     - pre: "subscribes_to accepts both str and List[str] types."
     - post: "Block subscribes to all specified states successfully."

    """
    mock_ds = datasource_factory()
    state_ids = ["state-1", "state-2", "state-3"]

    # This should not raise TypeError: unhashable type: 'list'
    block = TextBlock(
        block_id="test_text",
        datasource=mock_ds,
        subscribes_to=state_ids,
        content_generator=lambda df: "Test content",
    )

    # Verify subscribes dict was created correctly
    assert block.subscribes is not None
    assert len(block.subscribes) == 3
    for state_id in state_ids:
        assert state_id in block.subscribes
        assert block.subscribes[state_id] == block._update_content


def test_text_block_single_string_subscription(datasource_factory):
    """
    Tests that TextBlock still works with single string (regression).

    :hierarchy: [Testing | Unit Tests | Blocks | TextBlock | Single State]
    :covers:
     - object: "TextBlock with string subscription"
     - requirement: "Regression test: Single string subscription must still work"

    :scenario: "Verifies that TextBlock continues to work with single string
     state ID."
    :strategy: "Create TextBlock with string subscription and verify it works."
    :contract:
     - pre: "subscribes_to is a single string state ID."
     - post: "Block subscribes to the state successfully."

    """
    mock_ds = datasource_factory()

    block = TextBlock(
        block_id="test_text",
        datasource=mock_ds,
        subscribes_to="single-state",
        content_generator=lambda df: "Test content",
    )

    # Verify subscribes dict was created correctly
    assert block.subscribes is not None
    assert len(block.subscribes) == 1
    assert "single-state" in block.subscribes
