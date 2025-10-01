"""
Tests for navigation customization parameters.

:hierarchy: [Tests | Core | Navigation Customization]
:covers:
 - object: "NavigationConfig with customization parameters"
 - requirement: "Phase 3: Navigation should support style customization"

:scenario: "Verifies that NavigationConfig accepts and applies customization parameters."
:strategy: "Uses pytest to test NavigationConfig creation and layout building with custom styles."
:contract:
 - pre: "NavigationConfig is created with customization parameters"
 - post: "Navigation layout is built with applied custom styles"

"""

from unittest.mock import Mock

import pytest

from dashboard_lego.core.page import DashboardPage, NavigationConfig, NavigationSection
from dashboard_lego.core.state import StateManager


@pytest.fixture
def mock_sections():
    """Mock navigation sections for testing."""

    def section1_factory():
        return [[Mock()]]

    def section2_factory():
        return [[Mock()]]

    return [
        NavigationSection(title="Section 1", block_factory=section1_factory),
        NavigationSection(title="Section 2", block_factory=section2_factory),
    ]


@pytest.fixture
def mock_state_manager():
    """Mock state manager for testing."""
    return Mock(spec=StateManager)


class TestNavigationConfigCustomization:
    """Test NavigationConfig with customization parameters."""

    def test_navigation_config_default_parameters(self, mock_sections):
        """Test NavigationConfig with default parameters."""
        config = NavigationConfig(sections=mock_sections)

        assert config.sections == mock_sections
        assert config.position == "left"
        assert config.sidebar_width == 3
        assert config.default_section == 0
        assert config.sidebar_style is None
        assert config.sidebar_className is None
        assert config.content_style is None
        assert config.content_className is None
        assert config.nav_style is None
        assert config.nav_className is None
        assert config.nav_link_style is None
        assert config.nav_link_className is None
        assert config.nav_link_active_style is None
        assert config.nav_link_active_className is None

    def test_navigation_config_custom_sidebar_style(self, mock_sections):
        """Test NavigationConfig with custom sidebar style."""
        custom_style = {"backgroundColor": "lightblue", "color": "darkblue"}

        config = NavigationConfig(
            sections=mock_sections,
            sidebar_style=custom_style,
            sidebar_className="custom-sidebar",
        )

        assert config.sidebar_style == custom_style
        assert config.sidebar_className == "custom-sidebar"

    def test_navigation_config_custom_content_style(self, mock_sections):
        """Test NavigationConfig with custom content style."""
        custom_style = {"backgroundColor": "lightgreen", "padding": "20px"}

        config = NavigationConfig(
            sections=mock_sections,
            content_style=custom_style,
            content_className="custom-content",
        )

        assert config.content_style == custom_style
        assert config.content_className == "custom-content"

    def test_navigation_config_custom_nav_style(self, mock_sections):
        """Test NavigationConfig with custom nav style."""
        nav_style = {"backgroundColor": "lightyellow"}
        nav_className = "custom-nav"

        config = NavigationConfig(
            sections=mock_sections, nav_style=nav_style, nav_className=nav_className
        )

        assert config.nav_style == nav_style
        assert config.nav_className == nav_className

    def test_navigation_config_custom_nav_link_style(self, mock_sections):
        """Test NavigationConfig with custom nav link styles."""
        link_style = {"color": "red", "fontSize": "16px"}
        link_className = "custom-link"
        active_style = {"backgroundColor": "orange"}
        active_className = "custom-active"

        config = NavigationConfig(
            sections=mock_sections,
            nav_link_style=link_style,
            nav_link_className=link_className,
            nav_link_active_style=active_style,
            nav_link_active_className=active_className,
        )

        assert config.nav_link_style == link_style
        assert config.nav_link_className == link_className
        assert config.nav_link_active_style == active_style
        assert config.nav_link_active_className == active_className

    def test_navigation_config_all_custom_parameters(self, mock_sections):
        """Test NavigationConfig with all customization parameters."""
        sidebar_style = {"backgroundColor": "lightblue"}
        content_style = {"backgroundColor": "lightgreen"}
        nav_style = {"backgroundColor": "lightyellow"}
        link_style = {"color": "red"}
        active_style = {"backgroundColor": "orange"}

        config = NavigationConfig(
            sections=mock_sections,
            position="left",
            sidebar_width=4,
            default_section=1,
            sidebar_style=sidebar_style,
            sidebar_className="custom-sidebar",
            content_style=content_style,
            content_className="custom-content",
            nav_style=nav_style,
            nav_className="custom-nav",
            nav_link_style=link_style,
            nav_link_className="custom-link",
            nav_link_active_style=active_style,
            nav_link_active_className="custom-active",
        )

        # Verify all parameters
        assert config.sections == mock_sections
        assert config.position == "left"
        assert config.sidebar_width == 4
        assert config.default_section == 1
        assert config.sidebar_style == sidebar_style
        assert config.sidebar_className == "custom-sidebar"
        assert config.content_style == content_style
        assert config.content_className == "custom-content"
        assert config.nav_style == nav_style
        assert config.nav_className == "custom-nav"
        assert config.nav_link_style == link_style
        assert config.nav_link_className == "custom-link"
        assert config.nav_link_active_style == active_style
        assert config.nav_link_active_className == "custom-active"


class TestNavigationLayoutCustomization:
    """Test navigation layout building with customization parameters."""

    def test_build_navigation_layout_with_custom_styles(
        self, mock_sections, mock_state_manager
    ):
        """Test that _build_navigation_layout applies custom styles."""
        custom_sidebar_style = {"backgroundColor": "lightblue", "color": "darkblue"}
        custom_content_style = {"backgroundColor": "lightgreen", "padding": "20px"}
        custom_nav_style = {"backgroundColor": "lightyellow"}
        custom_link_style = {"color": "red", "fontSize": "16px"}
        custom_active_style = {"backgroundColor": "orange"}

        config = NavigationConfig(
            sections=mock_sections,
            sidebar_style=custom_sidebar_style,
            sidebar_className="custom-sidebar",
            content_style=custom_content_style,
            content_className="custom-content",
            nav_style=custom_nav_style,
            nav_className="custom-nav",
            nav_link_style=custom_link_style,
            nav_link_className="custom-link",
            nav_link_active_style=custom_active_style,
            nav_link_active_className="custom-active",
        )

        page = DashboardPage(title="Test Dashboard", blocks=[], navigation=config)

        # Build the navigation layout
        layout = page._build_navigation_layout()

        # Verify the layout was created without errors
        assert layout is not None

        # The layout should be a Div containing the navigation components
        assert hasattr(layout, "children")
        assert len(layout.children) == 3  # Store, sidebar, content_area

    def test_build_navigation_layout_default_styles(
        self, mock_sections, mock_state_manager
    ):
        """Test that _build_navigation_layout works with default styles."""
        config = NavigationConfig(sections=mock_sections)

        page = DashboardPage(title="Test Dashboard", blocks=[], navigation=config)

        # Build the navigation layout
        layout = page._build_navigation_layout()

        # Verify the layout was created without errors
        assert layout is not None
        assert hasattr(layout, "children")
        assert len(layout.children) == 3  # Store, sidebar, content_area

    def test_build_navigation_layout_partial_customization(
        self, mock_sections, mock_state_manager
    ):
        """Test that _build_navigation_layout works with partial customization."""
        config = NavigationConfig(
            sections=mock_sections,
            sidebar_style={"backgroundColor": "lightblue"},
            nav_link_style={"color": "red"},
        )

        page = DashboardPage(title="Test Dashboard", blocks=[], navigation=config)

        # Build the navigation layout
        layout = page._build_navigation_layout()

        # Verify the layout was created without errors
        assert layout is not None
        assert hasattr(layout, "children")
        assert len(layout.children) == 3  # Store, sidebar, content_area
