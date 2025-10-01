"""
Tests for the BaseBlock abstract base class.

:hierarchy: [Testing | Unit Tests | Blocks | BaseBlock]
:relates-to:
 - motivated_by: "Architectural Conclusion: Base block requires comprehensive
   testing as the foundation for all dashboard components"
 - implements: "test_suite: 'BaseBlock'"

:strategy: "Use a concrete subclass of BaseBlock for testing its non-abstract methods. Use pytest.raises to test abstract nature and input validation."
:contract:
 - pre: "Test environment is set up with pytest and mock."
 - post: "All tests for BaseBlock pass, and code coverage for the module is 100%."

"""

from unittest.mock import MagicMock, call

import pytest
from dash import html

from dashboard_lego.blocks.base import BaseBlock
from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.core.state import StateManager
from dashboard_lego.utils.exceptions import ConfigurationError


# A concrete implementation of BaseBlock for testing purposes
class ConcreteTestBlock(BaseBlock):
    def layout(self):
        return html.Div()


@pytest.fixture
def mock_datasource():
    """Fixture for a mocked BaseDataSource."""
    return MagicMock(spec=BaseDataSource)


@pytest.fixture
def mock_state_manager():
    """Fixture for a mocked StateManager."""
    return MagicMock(spec=StateManager)


def test_base_block_is_abstract(mock_datasource):
    """
    Tests that BaseBlock cannot be instantiated directly.

    :hierarchy: [Testing | Unit Tests | Blocks | BaseBlock | Abstract]
    :covers:
     - object: "BaseBlock"
     - requirement: "BaseBlock must be abstract."

    :scenario: "Attempting to instantiate BaseBlock directly raises a TypeError."
    :contract:
     - pre: "BaseBlock is an abstract class."
     - post: "TypeError is raised."

    """
    with pytest.raises(
        TypeError,
        match="Can't instantiate abstract class BaseBlock with abstract method layout",
    ):
        BaseBlock(block_id="test", datasource=mock_datasource)


def test_base_block_init_invalid_id(mock_datasource):
    """
    Tests that __init__ raises ValueError for an invalid block_id.

    :hierarchy: [Testing | Unit Tests | Blocks | BaseBlock | Init | InvalidId]
    :covers:
     - object: "BaseBlock.__init__"
     - requirement: "block_id must be a non-empty string."

    :scenario: "Providing a non-string or empty string for block_id raises a ValueError."
    :contract:
     - pre: "block_id is not a valid string."
     - post: "ValueError is raised."

    """
    with pytest.raises(
        ConfigurationError, match="block_id must be a non-empty string."
    ):
        ConcreteTestBlock(block_id="", datasource=mock_datasource)
    with pytest.raises(
        ConfigurationError, match="block_id must be a non-empty string."
    ):
        ConcreteTestBlock(block_id=None, datasource=mock_datasource)
    with pytest.raises(
        ConfigurationError, match="block_id must be a non-empty string."
    ):
        ConcreteTestBlock(block_id=123, datasource=mock_datasource)


def test_base_block_init_invalid_datasource():
    """
    Tests that __init__ raises TypeError for an invalid datasource.

    :hierarchy: [Testing | Unit Tests | Blocks | BaseBlock | Init | InvalidDatasource]
    :covers:
     - object: "BaseBlock.__init__"
     - requirement: "datasource must be an instance of BaseDataSource."

    :scenario: "Providing an object that is not a BaseDataSource instance raises a TypeError."
    :contract:
     - pre: "datasource is not a BaseDataSource instance."
     - post: "TypeError is raised."

    """
    with pytest.raises(
        ConfigurationError, match="datasource must be an instance of BaseDataSource."
    ):
        ConcreteTestBlock(block_id="test", datasource=object())


def test_register_with_state_manager(mock_datasource, mock_state_manager):
    """
    Tests the registration of publishers and subscribers with the StateManager.

    :hierarchy: [Testing | Unit Tests | Blocks | BaseBlock | StateRegistration]
    :covers:
     - object: "BaseBlock._register_state_interactions"
     - requirement: "Block must register its state interactions."

    :scenario: "A block with publishes and subscribes kwargs correctly calls the StateManager's registration methods."
    :contract:
     - pre: "Block has publishes and subscribes attributes."
     - post: "StateManager.register_publisher and StateManager.register_subscriber are called with correct arguments."

    """
    publishes = [{"state_id": "filter-a", "component_prop": "value"}]
    subscribes = {"filter-b": lambda x: x}
    block = ConcreteTestBlock(
        block_id="my-block",
        datasource=mock_datasource,
        publishes=publishes,
        subscribes=subscribes,
    )

    block._register_state_interactions(mock_state_manager)

    mock_state_manager.register_publisher.assert_called_once_with(
        "filter-a", "my-block-a", "value"
    )
    mock_state_manager.register_subscriber.assert_called_once_with(
        "filter-b", "my-block-container", "children", subscribes["filter-b"]
    )


def test_register_with_state_manager_no_interactions(
    mock_datasource, mock_state_manager
):
    """
    Tests that no registration happens if publishes/subscribes are not defined.

    :hierarchy: [Testing | Unit Tests | Blocks | BaseBlock | StateRegistration | NoInteractions]
    :covers:
     - object: "BaseBlock._register_state_interactions"
     - requirement: "Block should not fail if there are no state interactions to register."

    :scenario: "A block without publishes and subscribes kwargs does not call the StateManager's registration methods."
    :contract:
     - pre: "Block does not have publishes or subscribes attributes."
     - post: "StateManager registration methods are not called."

    """
    block = ConcreteTestBlock(block_id="my-block", datasource=mock_datasource)
    block._register_state_interactions(mock_state_manager)

    mock_state_manager.register_publisher.assert_not_called()
    mock_state_manager.register_subscriber.assert_not_called()


def test_generate_id(mock_datasource):
    """
    Tests the _generate_id method.

    :hierarchy: [Testing | Unit Tests | Blocks | BaseBlock | GenerateId]
    :covers:
     - object: "BaseBlock._generate_id"
     - requirement: "Block must be able to generate unique component IDs."

    :scenario: "The _generate_id method correctly prepends the block_id to the component name."
    :contract:
     - pre: "A component name is provided."
     - post: "A unique ID string is returned in the format 'block_id-component_name'."

    """
    block = ConcreteTestBlock(block_id="my-block", datasource=mock_datasource)
    assert block._generate_id("my-component") == "my-block-my-component"


def test_register_callbacks_does_nothing(mock_datasource):
    """
    Tests that the deprecated register_callbacks method runs without error.

    :hierarchy: [Testing | Unit Tests | Blocks | BaseBlock | Deprecated]
    :covers:
     - object: "BaseBlock.register_callbacks"
     - requirement: "Old methods should not break."

    :scenario: "Calling the register_callbacks method does nothing and does not raise an error."
    :contract:
     - pre: "An app object is passed."
     - post: "The method completes without any side effects or errors."

    """
    block = ConcreteTestBlock(block_id="test", datasource=mock_datasource)
    try:
        block.register_callbacks(app=MagicMock())
    except Exception as e:
        pytest.fail(f"register_callbacks should do nothing, but it raised {e}")
