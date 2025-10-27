"""
Tests for the ControlPanelBlock.

:hierarchy: [Tests | Blocks | ControlPanelBlock]
:relates-to:
 - motivated_by: "PRD: Ensure ControlPanelBlock functions correctly with all features"
 - implements: "test_suite: 'ControlPanelBlock'"
 - uses: ["class: 'ControlPanelBlock'", "class: 'Control'"]

:rationale: "Comprehensive test coverage for standalone control panels."
:contract:
 - pre: "Test environment with pytest and mock datasources."
 - post: "All ControlPanelBlock functionality is validated."

"""

import pandas as pd
import pytest
from dash import dcc

from dashboard_lego.blocks.control_panel import Control, ControlPanelBlock


@pytest.fixture
def sample_data():
    """
    Provides sample data for testing.

    :hierarchy: [Tests | Blocks | ControlPanelBlock | Fixtures]
    :covers:
     - object: "fixture: sample_data"
     - requirement: "Test data for ControlPanelBlock validation"

    :scenario: "Creates a simple DataFrame for testing control initialization."
    :strategy: "Use pandas DataFrame with basic numeric data."
    :contract:
     - pre: "None"
     - post: "Returns a DataFrame with sample data."

    """
    return pd.DataFrame(
        {
            "category": ["A", "B", "C", "D"],
            "value": [10, 20, 30, 40],
            "metric": [1.5, 2.5, 3.5, 4.5],
        }
    )


@pytest.fixture
def datasource(sample_data, datasource_factory):
    """
    Provides a mock datasource for testing.

    :hierarchy: [Tests | Blocks | ControlPanelBlock | Fixtures]
    :covers:
     - object: "fixture: datasource"
     - requirement: "Datasource for ControlPanelBlock tests"

    :scenario: "Creates a mock datasource with sample data."
    :strategy: "Use datasource_factory to create mock with sample DataFrame."
    :contract:
     - pre: "Sample data is available."
     - post: "Returns a configured mock datasource."

    """
    return datasource_factory(get_processed_data=sample_data)


@pytest.fixture
def basic_controls():
    """
    Provides basic controls for testing.

    :hierarchy: [Tests | Blocks | ControlPanelBlock | Fixtures]
    :covers:
     - object: "fixture: basic_controls"
     - requirement: "Control definitions for testing"

    :scenario: "Creates a dictionary of Control objects."
    :strategy: "Define slider and dropdown controls with default props."
    :contract:
     - pre: "None"
     - post: "Returns dictionary of Control objects."

    """
    return {
        "slider": Control(
            component=dcc.Slider, props={"min": 0, "max": 100, "value": 50}
        ),
        "dropdown": Control(
            component=dcc.Dropdown,
            props={
                "options": [{"label": "A", "value": "a"}, {"label": "B", "value": "b"}],
                "value": "a",
            },
        ),
    }

    def test_control_panel_creation(datasource, basic_controls, mocker):
        """
        Test that ControlPanelBlock can be created with basic parameters.

        :hierarchy: [Tests | Blocks | ControlPanelBlock | Creation]
        :covers:
         - object: "class: ControlPanelBlock.__init__"
         - requirement: "ControlPanelBlock should initialize correctly"

        :scenario: "Creates a ControlPanelBlock with minimal required parameters."
        :strategy: "Instantiate with datasource, title, and controls."
        :contract:
         - pre: "Valid datasource and controls are provided."
         - post: "Block is created with correct attributes and state interactions."

        """
        block = ControlPanelBlock(
            block_id="test_panel",
            datasource=datasource,
            title="Test Panel",
            controls=basic_controls,
        )

        assert block.block_id == "test_panel"
        assert block.title == "Test Panel"
        assert len(block.controls) == 2
        assert "slider" in block.controls
        assert "dropdown" in block.controls

        # Manually register state to populate publishes list
        mock_state_manager = mocker.MagicMock(spec=StateManager)
        block._register_state_interactions(mock_state_manager)

        # Check that publishes are set up correctly
        assert block.publishes is not None
        assert len(block.publishes) == 2
        assert any(p["state_id"] == "test_panel-slider" for p in block.publishes)
        assert any(p["state_id"] == "test_panel-dropdown" for p in block.publishes)

    def test_control_panel_with_value_initializer(datasource, basic_controls):
        """
        Test that ControlPanelBlock can initialize values from datasource.

        :hierarchy: [Tests | Blocks | ControlPanelBlock | Initialization]
        :covers:
         - object: "method: ControlPanelBlock._initialize_control_values"
         - requirement: "Control values should be initialized from datasource"

        :scenario: "Creates a ControlPanelBlock with value_initializer function."
        :strategy: "Define value_initializer that computes values from DataFrame."
        :contract:
         - pre: "Datasource contains valid data."
         - post: "Control values are initialized based on datasource data."

        """

        def value_initializer(df):
            return {
                "slider": int(df["value"].mean()),
                "dropdown": df["category"].iloc[0],
            }

        block = ControlPanelBlock(
            block_id="test_panel",
            datasource=datasource,
            title="Test Panel",
            controls=basic_controls,
            value_initializer=value_initializer,
        )

        # Check that initial values were computed
        assert block._initial_control_values["slider"] == 25  # mean of [10, 20, 30, 40]
        assert block._initial_control_values["dropdown"] == "A"

    def test_control_panel_with_subscribes_to(datasource, basic_controls, mocker):
        """
        Test that ControlPanelBlock can subscribe to external states.

        :hierarchy: [Tests | Blocks | ControlPanelBlock | Subscriptions]
        :covers:
         - object: "parameter: subscribes_to"
         - requirement: "Control panels should be able to subscribe to external states"

        :scenario: "Creates a ControlPanelBlock that subscribes to an external state."
        :strategy: "Pass subscribes_to parameter and verify subscription setup."
        :contract:
         - pre: "Valid state ID is provided."
         - post: "Block subscribes to the specified state."

        """
        block = ControlPanelBlock(
            block_id="test_panel",
            datasource=datasource,
            title="Test Panel",
            controls=basic_controls,
            subscribes_to="external_state",
        )

        # Manually register state to populate subscribes list
        mock_state_manager = mocker.MagicMock(spec=StateManager)
        block._register_state_interactions(mock_state_manager)

        # Check that subscribes are set up correctly
        assert block.subscribes is not None
        assert "external_state" in block.subscribes
        assert callable(block.subscribes["external_state"])

    def test_control_panel_with_multiple_subscribes(datasource, basic_controls, mocker):
        """
        Test that ControlPanelBlock can subscribe to multiple external states.

        :hierarchy: [Tests | Blocks | ControlPanelBlock | Multi-Subscriptions]
        :covers:
         - object: "parameter: subscribes_to (list)"
         - requirement: "Control panels should support multiple state subscriptions"

        :scenario: "Creates a ControlPanelBlock that subscribes to multiple states."
        :strategy: "Pass list of state IDs and verify all subscriptions."
        :contract:
         - pre: "List of valid state IDs is provided."
         - post: "Block subscribes to all specified states."

        """
        block = ControlPanelBlock(
            block_id="test_panel",
            datasource=datasource,
            title="Test Panel",
            controls=basic_controls,
            subscribes_to=["state1", "state2"],
        )

        # Manually register state to populate subscribes list
        mock_state_manager = mocker.MagicMock(spec=StateManager)
        block._register_state_interactions(mock_state_manager)

        # Check that subscribes are set up correctly
        assert block.subscribes is not None
        assert "state1" in block.subscribes
        assert "state2" in block.subscribes


def test_control_panel_style_customization(datasource, basic_controls):
    """
    Test that ControlPanelBlock accepts style customization parameters.

    :hierarchy: [Tests | Blocks | ControlPanelBlock | Styling]
    :covers:
     - object: "parameters: card_style, title_style, controls_row_style"
     - requirement: "Control panels should support full style customization"

    :scenario: "Creates a ControlPanelBlock with custom style parameters."
    :strategy: "Pass style dictionaries and verify they are stored."
    :contract:
     - pre: "Valid style dictionaries are provided."
     - post: "Block stores all style customization parameters."

    """
    custom_card_style = {"backgroundColor": "#f0f0f0"}
    custom_title_style = {"color": "red"}
    custom_controls_style = {"padding": "10px"}

    block = ControlPanelBlock(
        block_id="test_panel",
        datasource=datasource,
        title="Test Panel",
        controls=basic_controls,
        card_style=custom_card_style,
        title_style=custom_title_style,
        controls_row_style=custom_controls_style,
    )

    assert block.card_style == custom_card_style
    assert block.title_style == custom_title_style
    assert block.controls_row_style == custom_controls_style


def test_control_panel_layout(datasource, basic_controls):
    """
    Test that ControlPanelBlock renders a valid layout.

    :hierarchy: [Tests | Blocks | ControlPanelBlock | Layout]
    :covers:
     - object: "method: ControlPanelBlock.layout"
     - requirement: "Control panels should render valid Dash components"

    :scenario: "Calls layout() method and verifies component structure."
    :strategy: "Check that returned component has expected structure."
    :contract:
     - pre: "Block is properly initialized."
     - post: "Layout returns a valid Card component with controls."

    """
    block = ControlPanelBlock(
        block_id="test_panel",
        datasource=datasource,
        title="Test Panel",
        controls=basic_controls,
    )

    layout = block.layout()

    # Check that layout is a Card (check type name)
    assert type(layout).__name__ == "Card"
    # Check that it has CardBody children
    assert len(layout.children) > 0


def test_control_panel_list_control_inputs(datasource, basic_controls):
    """
    Test that ControlPanelBlock returns empty list for control inputs.

    :hierarchy: [Tests | Blocks | ControlPanelBlock | Control Inputs]
    :covers:
     - object: "method: ControlPanelBlock.list_control_inputs"
     - requirement: "Control panels should not have block-centric callbacks"

    :scenario: "Calls list_control_inputs() and verifies it returns empty list."
    :strategy: "Check that ControlPanelBlock prevents block-centric callback registration."
    :contract:
     - pre: "Block is initialized with controls."
     - post: "Returns empty list to prevent block-centric callbacks."

    """
    block = ControlPanelBlock(
        block_id="test_panel",
        datasource=datasource,
        title="Test Panel",
        controls=basic_controls,
    )

    inputs = block.list_control_inputs()

    # ControlPanelBlock should return empty list to prevent block-centric callbacks
    # which would create circular dependencies and break the UI
    assert len(inputs) == 0
    assert inputs == []


def test_control_panel_build_control_elements(datasource, basic_controls):
    """
    Test that ControlPanelBlock builds control elements correctly.

    :hierarchy: [Tests | Blocks | ControlPanelBlock | Build Elements]
    :covers:
     - object: "method: ControlPanelBlock._build_control_elements"
     - requirement: "Control elements should be built with proper structure"

    :scenario: "Calls _build_control_elements() and verifies component structure."
    :strategy: "Check that returned component is a Row with control columns."
    :contract:
     - pre: "Block is initialized with controls."
     - post: "Returns Row component with all controls."

    """
    block = ControlPanelBlock(
        block_id="test_panel",
        datasource=datasource,
        title="Test Panel",
        controls=basic_controls,
    )

    elements = block._build_control_elements()

    # Check that it's a Row component (check type name)
    assert type(elements).__name__ == "Row"
    # Check that it has children (columns with controls)
    assert len(elements.children) == 2


def test_control_panel_empty_datasource(datasource_factory):
    """
    Test that ControlPanelBlock handles empty datasource gracefully.

    :hierarchy: [Tests | Blocks | ControlPanelBlock | Error Handling]
    :covers:
     - object: "method: ControlPanelBlock._initialize_control_values (error case)"
     - requirement: "Control panels should handle empty data gracefully"

    :scenario: "Creates a ControlPanelBlock with empty datasource and value_initializer."
    :strategy: "Verify that initialization doesn't fail and returns empty values."
    :contract:
     - pre: "Datasource returns empty DataFrame."
     - post: "Block initializes without error, returns empty initial values."

    """
    empty_df = pd.DataFrame()
    datasource = datasource_factory(get_processed_data=empty_df)

    def value_initializer(df):
        if df.empty:
            return {}
        return {"slider": 50}

    controls = {
        "slider": Control(
            component=dcc.Slider, props={"min": 0, "max": 100, "value": 50}
        ),
    }

    block = ControlPanelBlock(
        block_id="test_panel",
        datasource=datasource,
        title="Test Panel",
        controls=controls,
        value_initializer=value_initializer,
    )

    # Should not raise exception
    assert block._initial_control_values == {}


def test_control_panel_col_props(datasource):
    """Test that col_props are applied correctly to control elements."""
    controls = {
        "test_dropdown": Control(
            component=dcc.Dropdown,
            props={"options": ["a", "b"]},
            col_props={"xs": 12, "md": 4},
        ),
        "test_slider": Control(
            component=dcc.Slider,
            props={"min": 0, "max": 10},
            col_props={"xs": 12, "md": 8},
        ),
    }

    block = ControlPanelBlock(
        block_id="test_panel",
        datasource=datasource,
        title="Test",
        controls=controls,
    )

    control_elements = block._build_control_elements()

    # Check that col_props are applied
    dropdown_col = control_elements.children[0]
    slider_col = control_elements.children[1]

    # Verify col_props are set on the Col components
    assert dropdown_col.xs == 12
    assert dropdown_col.md == 4
    assert slider_col.xs == 12
    assert slider_col.md == 8


def test_control_panel_default_col_props(datasource):
    """Test that default col_props are used when not specified."""
    controls = {
        "test_dropdown": Control(
            component=dcc.Dropdown,
            props={"options": ["a", "b"]},
            # No col_props specified, should use defaults
        ),
    }

    block = ControlPanelBlock(
        block_id="test_panel",
        datasource=datasource,
        title="Test",
        controls=controls,
    )

    control_elements = block._build_control_elements()
    dropdown_col = control_elements.children[0]

    # Verify default col_props are applied (now md="auto" by default)
    assert dropdown_col.xs == 12
    assert dropdown_col.md == "auto"


def test_control_panel_update_controls(datasource, basic_controls):
    """
    Test that ControlPanelBlock._update_controls works correctly.

    :hierarchy: [Tests | Blocks | ControlPanelBlock | Update Logic]
    :covers:
     - object: "method: ControlPanelBlock._update_controls"
     - requirement: "Control panels should update in response to state changes"

    :scenario: "Calls _update_controls() and verifies component is returned."
    :strategy: "Invoke update method and check returned component."
    :contract:
     - pre: "Block is properly initialized."
     - post: "Returns updated control elements component."

    """
    block = ControlPanelBlock(
        block_id="test_panel",
        datasource=datasource,
        title="Test Panel",
        controls=basic_controls,
        subscribes_to="external_state",
    )

    result = block._update_controls()

    # Should return a component (Row with controls)
    assert result is not None
    assert type(result).__name__ == "Row"


def test_control_panel_auto_size_functionality(datasource):
    """Test that auto_size controls apply correct styling and column props."""
    controls = {
        "auto_dropdown": Control(
            component=dcc.Dropdown,
            props={"options": ["Short", "Very Long Option Name"]},
            auto_size=True,
            max_ch=40,
        ),
        "auto_input": Control(
            component=dcc.Input,
            props={"type": "text", "placeholder": "Enter text"},
            auto_size=True,
            max_ch=30,
        ),
        "disabled_auto": Control(
            component=dcc.Dropdown,
            props={"options": ["A", "B"]},
            auto_size=False,
            col_props={"xs": 12, "md": 6},
        ),
    }

    block = ControlPanelBlock(
        block_id="test_auto_size",
        datasource=datasource,
        title="Auto Size Test",
        controls=controls,
    )

    control_elements = block._build_control_elements()

    # Test auto-sized dropdown
    auto_dropdown_col = control_elements.children[0]
    assert auto_dropdown_col.md == "auto"  # Should use md="auto" for auto_size

    # Test auto-sized input
    auto_input_col = control_elements.children[1]
    assert auto_input_col.md == "auto"  # Should use md="auto" for auto_size

    # Test disabled auto-size
    disabled_col = control_elements.children[2]
    assert disabled_col.md == 6  # Should use explicit col_props when auto_size=False
