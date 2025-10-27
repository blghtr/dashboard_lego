"""
Unit tests for the Navigation feature in DashboardPage.

    :hierarchy: [Testing | Core | Navigation Tests]
    :relates-to:
     - motivated_by: "Ensure navigation panel feature works correctly with lazy loading"
     - implements: "test suite for NavigationConfig and NavigationSection"
     - uses: ["class: 'DashboardPage'", "dataclass: 'NavigationConfig'"]

    :rationale: "Comprehensive testing of navigation feature to ensure reliability."
    :contract:
     - pre: "Navigation feature is implemented in DashboardPage"
     - post: "All navigation scenarios are tested including lazy loading and caching"

"""

from unittest.mock import MagicMock, call

import pytest
from dash import html

from dashboard_lego.blocks.base import BaseBlock
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.core.page import DashboardPage, NavigationConfig, NavigationSection
from dashboard_lego.utils.exceptions import ConfigurationError


class MockBlock(BaseBlock):
    """Mock block for testing."""

    def __init__(self, block_id, datasource=None, **kwargs):
        if datasource is None:
            datasource = MagicMock(spec=DataSource)
        super().__init__(block_id, datasource, **kwargs)
        self._layout = html.Div(self.block_id, id=self._generate_id("container"))

    def layout(self):
        return self._layout


@pytest.fixture
def mock_app():
    """Fixture for mock Dash app."""
    app = MagicMock()
    app.callback = MagicMock(return_value=lambda f: f)
    return app


@pytest.fixture
def mock_datasource():
    """Fixture for mock datasource."""
    return MagicMock(spec=DataSource)


def test_navigation_config_creation():
    """Test that NavigationConfig can be created with valid parameters."""

    def factory1():
        return [[MockBlock("b1")]]

    def factory2():
        return [[MockBlock("b2")]]

    config = NavigationConfig(
        sections=[
            NavigationSection(title="Section 1", block_factory=factory1),
            NavigationSection(title="Section 2", block_factory=factory2),
        ],
        position="left",
        sidebar_width=3,
        default_section=0,
    )

    assert len(config.sections) == 2
    assert config.position == "left"
    assert config.sidebar_width == 3
    assert config.default_section == 0


def test_page_init_with_navigation(mock_datasource):
    """Test DashboardPage initialization with navigation config."""

    def section_factory():
        return [[MockBlock("nav_block1", datasource=mock_datasource)]]

    nav_config = NavigationConfig(
        sections=[NavigationSection(title="Section 1", block_factory=section_factory)],
    )

    page = DashboardPage(title="Nav Page", navigation=nav_config)

    assert page.navigation is not None
    assert len(page.navigation.sections) == 1
    assert page.blocks == []  # Blocks not loaded yet (lazy)


def test_page_init_without_blocks_and_navigation_raises_error():
    """Test that page requires either blocks or navigation."""

    with pytest.raises(
        ConfigurationError,
        match="Either 'blocks' or 'navigation' must be provided",
    ):
        DashboardPage(title="Invalid Page")


def test_build_navigation_layout_creates_sidebar(mock_datasource):
    """Test that navigation layout creates fixed sidebar with nav items."""

    def factory1():
        return [[MockBlock("b1", datasource=mock_datasource)]]

    def factory2():
        return [[MockBlock("b2", datasource=mock_datasource)]]

    nav_config = NavigationConfig(
        sections=[
            NavigationSection(title="Overview", block_factory=factory1),
            NavigationSection(title="Analytics", block_factory=factory2),
        ],
        sidebar_width=3,
    )

    page = DashboardPage(title="Test", navigation=nav_config)
    layout = page.build_layout()

    # Check that layout is a Div (root container)
    assert layout.__class__.__name__ == "Div"
    assert len(layout.children) == 3  # Store, Sidebar, Content

    # Check for Store component (active section tracker)
    store = layout.children[0]
    assert store.__class__.__name__ == "Store"
    assert store.id == "active-section-store"

    # Check sidebar has fixed position style
    sidebar = layout.children[1]
    assert sidebar.__class__.__name__ == "Div"
    assert "position" in sidebar.style
    assert sidebar.style["position"] == "fixed"

    # Check content area wrapper (body-wrapper contains nav-content-area)
    body_wrapper = layout.children[2]
    assert body_wrapper.__class__.__name__ == "Div"
    assert body_wrapper.id == "body-wrapper"
    # The actual content area is inside body-wrapper
    assert len(body_wrapper.children) > 0
    content_area = body_wrapper.children[0]
    assert content_area.id == "nav-content-area"


def test_navigation_section_lazy_loading(mocker, mock_datasource):
    """Test that sections are loaded lazily on demand."""

    factory_called = {"count": 0}

    def section_factory():
        factory_called["count"] += 1
        return [
            [
                MockBlock(
                    f"lazy_block_{factory_called['count']}", datasource=mock_datasource
                )
            ]
        ]

    nav_config = NavigationConfig(
        sections=[
            NavigationSection(title="Lazy Section", block_factory=section_factory)
        ]
    )

    page = DashboardPage(title="Test", navigation=nav_config)

    # Factory should not be called during init
    assert factory_called["count"] == 0

    # Manually trigger section loading (simulating callback)
    content = page._create_section_content(0)

    # Factory should be called once
    assert factory_called["count"] == 1
    assert len(content) > 0

    # Loading same section again should use cache
    content2 = page._create_section_content(0)

    # Factory should still be called only once (cached)
    assert factory_called["count"] == 1


def test_navigation_section_caching(mock_datasource):
    """Test that loaded sections are cached properly."""

    def section_factory():
        return [[MockBlock("cached_block", datasource=mock_datasource)]]

    nav_config = NavigationConfig(
        sections=[NavigationSection(title="Cached", block_factory=section_factory)]
    )

    page = DashboardPage(title="Test", navigation=nav_config)

    # Load section first time
    page._create_section_content(0)

    # Check that cache is populated
    assert 0 in page._section_blocks_cache
    assert len(page._section_blocks_cache[0]) == 1
    assert page._section_blocks_cache[0][0].block_id == "cached_block"


def test_navigation_blocks_registration(mocker, mock_datasource):
    """Test that blocks are registered with StateManager when loaded."""

    spy_register = mocker.spy(MockBlock, "_register_state_interactions")

    def section_factory():
        block1 = MockBlock("nav_b1", datasource=mock_datasource)
        block2 = MockBlock("nav_b2", datasource=mock_datasource)
        return [[block1, block2]]

    nav_config = NavigationConfig(
        sections=[NavigationSection(title="Test", block_factory=section_factory)]
    )

    page = DashboardPage(title="Test", navigation=nav_config)

    # Load section
    page._create_section_content(0)

    # Check that blocks were registered
    assert spy_register.call_count == 2


def test_navigation_with_multiple_sections(mock_datasource):
    """Test navigation with multiple sections."""

    def factory1():
        return [[MockBlock("section1_block", datasource=mock_datasource)]]

    def factory2():
        return [[MockBlock("section2_block", datasource=mock_datasource)]]

    def factory3():
        return [[MockBlock("section3_block", datasource=mock_datasource)]]

    nav_config = NavigationConfig(
        sections=[
            NavigationSection(title="Section 1", block_factory=factory1),
            NavigationSection(title="Section 2", block_factory=factory2),
            NavigationSection(title="Section 3", block_factory=factory3),
        ]
    )

    page = DashboardPage(title="Multi-Section", navigation=nav_config)

    # Load each section
    page._create_section_content(0)
    page._create_section_content(1)
    page._create_section_content(2)

    # Check all sections are cached
    assert len(page._section_blocks_cache) == 3
    assert page._section_blocks_cache[0][0].block_id == "section1_block"
    assert page._section_blocks_cache[1][0].block_id == "section2_block"
    assert page._section_blocks_cache[2][0].block_id == "section3_block"


def test_navigation_factory_error_handling(mock_datasource):
    """Test that errors in factory functions are handled properly."""

    def bad_factory():
        raise ValueError("Factory error!")

    nav_config = NavigationConfig(
        sections=[NavigationSection(title="Bad", block_factory=bad_factory)]
    )

    page = DashboardPage(title="Test", navigation=nav_config)

    # Loading section should raise ConfigurationError
    with pytest.raises(ConfigurationError, match="Factory error!"):
        page._create_section_content(0)


def test_navigation_factory_returns_invalid_layout(mock_datasource):
    """Test that factory returning invalid layout raises error."""

    def invalid_factory():
        # Returns invalid object instead of BaseBlock
        return [[html.Div("Not a block")]]

    nav_config = NavigationConfig(
        sections=[NavigationSection(title="Invalid", block_factory=invalid_factory)]
    )

    page = DashboardPage(title="Test", navigation=nav_config)

    # Loading section should raise ConfigurationError
    with pytest.raises(
        ConfigurationError, match="All layout items must be of type BaseBlock"
    ):
        page._create_section_content(0)


def test_navigation_register_callbacks(mocker, mock_app, mock_datasource):
    """Test that navigation callbacks are registered properly."""

    def section_factory():
        return [[MockBlock("b1", datasource=mock_datasource)]]

    nav_config = NavigationConfig(
        sections=[NavigationSection(title="Test", block_factory=section_factory)]
    )

    page = DashboardPage(title="Test", navigation=nav_config)

    # Spy on navigation callback registration
    spy_nav_callbacks = mocker.spy(page, "_register_navigation_callbacks")

    # Register callbacks
    page.register_callbacks(mock_app)

    # Check that navigation callbacks were registered
    spy_nav_callbacks.assert_called_once_with(mock_app)


def test_navigation_top_position_not_implemented(mock_datasource):
    """Test that top navigation position raises NotImplementedError."""

    def section_factory():
        return [[MockBlock("b1", datasource=mock_datasource)]]

    nav_config = NavigationConfig(
        sections=[NavigationSection(title="Test", block_factory=section_factory)],
        position="top",
    )

    page = DashboardPage(title="Test", navigation=nav_config)

    # Building layout with top position should raise NotImplementedError
    with pytest.raises(
        NotImplementedError, match="Top navigation position is not yet implemented"
    ):
        page.build_layout()
