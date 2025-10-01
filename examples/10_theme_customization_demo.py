"""
Example demonstrating theme customization in Dashboard Lego.

This example shows how to use ThemeConfig to create custom themes
and apply them globally across all dashboard components.

:hierarchy: [Examples | Theme | Customization Demo]
:relates-to:
 - motivated_by: "Phase 4: Demonstrate theme customization capabilities"
 - implements: "example: 'theme customization demo'"
 - uses: ["class: 'ThemeConfig'", "class: 'DashboardPage'"]

:rationale: "Shows practical usage of theme system for consistent styling."
:contract:
 - pre: "User wants to customize global theme appearance"
 - post: "Dashboard with custom theme is created and displayed"

"""

import pandas as pd

from dashboard_lego.core.datasources import CsvDataSource
from dashboard_lego.core.page import DashboardPage, NavigationConfig, NavigationSection
from dashboard_lego.core.theme import ColorScheme, Spacing, ThemeConfig, Typography
from dashboard_lego.presets.eda_presets import (
    CorrelationHeatmapPreset,
    GroupedHistogramPreset,
    MissingValuesPreset,
)
from dashboard_lego.presets.ml_presets import (
    ConfusionMatrixPreset,
    FeatureImportancePreset,
    MetricCardBlock,
)


def create_sample_data():
    """Create sample data for the demo."""
    # Create main dataset
    main_data = {
        "feature1": [1, 2, None, 4, 5, 6, 7, 8, 9, 10],  # Add missing values
        "feature2": [2, 4, 6, 8, 10, 12, 14, 16, 18, 20],
        "feature3": [1, 1, 2, 2, None, 3, 4, 4, 5, 5],  # Add missing values
        "category": ["A", "B", "A", "B", "A", "B", "A", "B", "A", "B"],
        "target": [0, 1, 0, 1, 0, 1, 0, 1, 0, 1],
        "prediction": [
            0,
            1,
            0,
            1,
            0,
            1,
            0,
            1,
            0,
            1,
        ],  # Binary predictions for confusion matrix
        "Sales": [100, 200, 150, 300, 250, 400, 350, 500, 450, 600],  # For KPI
        "UnitsSold": [10, 20, 15, 30, 25, 40, 35, 50, 45, 60],  # For KPI
    }

    df = pd.DataFrame(main_data)
    # Ensure proper data types for GroupedHistogramPreset
    df["feature1"] = df["feature1"].astype("float64")
    df["feature2"] = df["feature2"].astype("float64")
    df["feature3"] = df["feature3"].astype("float64")
    df["target"] = df["target"].astype("int64")
    df["prediction"] = df["prediction"].astype("int64")
    df.to_csv("sample_theme_data.csv", index=False)

    # Create separate feature importance data
    feature_data = {
        "feature_name": ["feature1", "feature2", "feature3"],
        "importance": [0.3, 0.5, 0.2],
    }

    feature_df = pd.DataFrame(feature_data)
    feature_df.to_csv("sample_feature_importance.csv", index=False)

    return "sample_theme_data.csv"


def create_custom_purple_theme():
    """Create a custom purple theme."""
    colors = ColorScheme(
        # Purple color scheme
        primary="#6f42c1",
        secondary="#6c757d",
        success="#28a745",
        danger="#dc3545",
        warning="#ffc107",
        info="#17a2b8",
        # Light purple backgrounds
        background="#f8f5ff",
        surface="#f0e6ff",
        card_background="#ffffff",
        # Dark purple text
        text_primary="#2d1b69",
        text_secondary="#6c757d",
        text_muted="#9d7ce8",
        # Purple borders
        border="#d1c4e9",
        border_light="#e1bee7",
        # Purple navigation
        nav_background="#4a148c",
        nav_text="#ffffff",
        nav_active="#7b1fa2",
        nav_hover="#6a1b9a",
    )

    typography = Typography(
        font_family="'Inter', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        font_size_base="15px",
        font_size_h1="2.75rem",
        font_size_h2="2.25rem",
        font_size_h3="1.875rem",
        font_size_h4="1.5rem",
        font_weight_bold="600",
    )

    spacing = Spacing(
        base_unit="0.25rem",
        card_padding="2rem",
        border_radius="0.75rem",
        border_radius_lg="1rem",
    )

    return ThemeConfig.custom_theme(
        name="purple_modern", colors=colors, typography=typography, spacing=spacing
    )


def create_custom_dark_blue_theme():
    """Create a custom dark blue theme."""
    colors = ColorScheme(
        # Blue color scheme
        primary="#2196f3",
        secondary="#607d8b",
        success="#4caf50",
        danger="#f44336",
        warning="#ff9800",
        info="#00bcd4",
        # Dark blue backgrounds
        background="#0d1421",
        surface="#1a2332",
        card_background="#263238",
        # Light blue text
        text_primary="#e3f2fd",
        text_secondary="#90caf9",
        text_muted="#64b5f6",
        # Blue borders
        border="#37474f",
        border_light="#455a64",
        # Dark blue navigation
        nav_background="#0a0e1a",
        nav_text="#e3f2fd",
        nav_active="#1976d2",
        nav_hover="#1a2332",
    )

    typography = Typography(
        font_family="'Roboto', 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif",
        font_size_base="14px",
        font_size_h1="2.5rem",
        font_size_h2="2rem",
        font_size_h3="1.75rem",
        font_size_h4="1.5rem",
        font_weight_bold="500",
    )

    spacing = Spacing(
        base_unit="0.25rem", card_padding="1.5rem", border_radius="0.5rem"
    )

    return ThemeConfig.custom_theme(
        name="dark_blue", colors=colors, typography=typography, spacing=spacing
    )


def create_eda_section():
    """Create EDA section with no parameters (as per NavigationSection contract)."""
    datasource = CsvDataSource("sample_theme_data.csv")
    datasource.init_data()

    correlation_block = CorrelationHeatmapPreset(
        block_id="correlation",
        datasource=datasource,
        subscribes_to="dummy_state",
        title="Correlation Analysis",
    )

    histogram_block = GroupedHistogramPreset(
        block_id="histogram", datasource=datasource, title="Distribution Analysis"
    )

    missing_block = MissingValuesPreset(
        block_id="missing",
        datasource=datasource,
        subscribes_to="dummy_state",
        title="Missing Values",
    )

    return [[correlation_block], [histogram_block], [missing_block]]


def create_ml_section():
    """Create ML section with no parameters (as per NavigationSection contract)."""
    datasource = CsvDataSource("sample_theme_data.csv")
    datasource.init_data()

    confusion_block = ConfusionMatrixPreset(
        block_id="confusion",
        datasource=datasource,
        y_true_col="target",
        y_pred_col="prediction",
        title="Confusion Matrix",
    )

    # Create separate datasource for feature importance
    feature_datasource = CsvDataSource("sample_feature_importance.csv")
    # Initialize the datasource to ensure data is loaded
    feature_datasource.init_data()

    feature_block = FeatureImportancePreset(
        block_id="feature_importance",
        datasource=feature_datasource,
        feature_col="feature_name",
        importance_col="importance",
        title="Feature Importance",
    )

    metrics_block = MetricCardBlock(
        block_id="metrics",
        datasource=datasource,
        kpi_definitions=[
            {"key": "total_sales", "title": "Total Sales"},
            {"key": "total_units", "title": "Total Units"},
            {"key": "avg_price", "title": "Average Price"},
        ],
        subscribes_to="dummy_state",
        title="Model Metrics",
    )

    return [[confusion_block], [feature_block], [metrics_block]]


def create_themed_dashboard(theme_name="light"):
    """Create a dashboard with the specified theme."""
    # Create sample data
    create_sample_data()

    # Select theme
    if theme_name == "light":
        theme_config = ThemeConfig.light_theme()
    elif theme_name == "dark":
        theme_config = ThemeConfig.dark_theme()
    elif theme_name == "purple":
        theme_config = create_custom_purple_theme()
    elif theme_name == "dark_blue":
        theme_config = create_custom_dark_blue_theme()
    else:
        theme_config = ThemeConfig.light_theme()

    # Create navigation sections
    sections = [
        NavigationSection(title="📊 EDA Analysis", block_factory=create_eda_section),
        NavigationSection(title="🤖 ML Models", block_factory=create_ml_section),
    ]

    # Create navigation configuration with theme-based styling
    navigation_config = NavigationConfig(
        sections=sections,
        position="left",
        sidebar_width=3,
        default_section=0,
        # Apply theme-based navigation styling
        sidebar_style=theme_config.get_component_style("navigation", "sidebar"),
        sidebar_className="themed-sidebar",
        content_style=theme_config.get_component_style("navigation", "content"),
        content_className="themed-content",
        nav_style=theme_config.get_component_style("navigation", "nav"),
        nav_className="themed-nav",
        nav_link_style=theme_config.get_component_style("navigation", "link"),
        nav_link_className="themed-nav-link",
        nav_link_active_style=theme_config.get_component_style(
            "navigation", "link_active"
        ),
        nav_link_active_className="themed-nav-link-active",
    )

    # Create dashboard page with theme
    page = DashboardPage(
        title=f"🎨 {theme_config.name.title()} Theme Dashboard",
        blocks=[],  # Empty blocks since we're using navigation
        navigation=navigation_config,
        theme_config=theme_config,
    )

    return page, theme_config


def create_theme_comparison_dashboard():
    """Create a dashboard comparing different themes."""
    # Create sample data
    csv_file = create_sample_data()
    datasource = CsvDataSource(csv_file)
    # Initialize the datasource to ensure data is loaded
    datasource.init_data()

    # Create blocks for each theme
    light_theme = ThemeConfig.light_theme()
    dark_theme = ThemeConfig.dark_theme()
    purple_theme = create_custom_purple_theme()
    dark_blue_theme = create_custom_dark_blue_theme()

    themes = [
        ("Light Theme", light_theme),
        ("Dark Theme", dark_theme),
        ("Purple Theme", purple_theme),
        ("Dark Blue Theme", dark_blue_theme),
    ]

    # Create blocks for each theme
    blocks = []
    for theme_name, theme in themes:
        # Create themed blocks
        correlation_block = CorrelationHeatmapPreset(
            block_id=f"correlation_{theme_name.lower().replace(' ', '_')}",
            datasource=datasource,
            subscribes_to="dummy_state",
            title=f"{theme_name} - Correlation",
            card_style=theme.get_component_style("card", "background"),
            title_style=theme.get_component_style("card", "title"),
        )

        kpi_block = MetricCardBlock(
            block_id=f"kpi_{theme_name.lower().replace(' ', '_')}",
            datasource=datasource,
            kpi_definitions=[
                {"key": "total_sales", "title": "Total Sales"},
                {"key": "total_units", "title": "Total Units"},
                {"key": "avg_price", "title": "Average Price"},
            ],
            subscribes_to="dummy_state",
            title=f"{theme_name} - Metrics",
            container_style=theme.get_component_style("kpi", "container"),
            kpi_card_style=theme.get_component_style("kpi", "card"),
            value_style=theme.get_component_style("kpi", "value"),
            title_style=theme.get_component_style("kpi", "title"),
        )

        blocks.append([correlation_block, kpi_block])

    # Create dashboard page
    page = DashboardPage(
        title="🎨 Theme Comparison Dashboard",
        blocks=blocks,
        theme_config=light_theme,  # Use light theme as base
    )

    return page, light_theme


if __name__ == "__main__":
    import logging
    import sys

    logger = logging.getLogger("dashboard_lego")

    try:
        logger.info("Starting theme customization demo...")

        # Get theme from command line argument or use default
        theme_name = sys.argv[1] if len(sys.argv) > 1 else "light"
        logger.info(f"Selected theme: {theme_name}")

        # Create sample data
        logger.info("Creating sample data files...")

        if theme_name == "comparison":
            # Create theme comparison dashboard
            logger.info("Creating theme comparison dashboard...")
            dashboard, _ = create_theme_comparison_dashboard()
            print("🎨 Creating Theme Comparison Dashboard...")
        else:
            # Create themed dashboard
            logger.info(f"Creating {theme_name} themed dashboard...")
            dashboard, theme_config = create_themed_dashboard(theme_name)
            print(f"🎨 Creating {theme_config.name.title()} Theme Dashboard...")

        logger.info("Dashboard created successfully")

        # Create and configure Dash app
        logger.info("Creating Dash application...")
        from dash import Dash

        app = Dash(__name__, external_stylesheets=[dashboard.theme])

        # Build the layout and register callbacks
        logger.info("Building layout and registering callbacks...")
        app.layout = dashboard.build_layout()
        dashboard.register_callbacks(app)
        logger.info("Layout built and callbacks registered")

        print("🚀 Starting Theme Customization Dashboard...")
        print("🌐 Dashboard will be available at: http://localhost:8050")
        print(
            "💡 Try different themes: uv run 10_theme_customization_demo.py [light|dark|custom]"
        )

        logger.info("Starting Dash server on port 8050...")
        app.run(debug=True, port=8050)

    except Exception as e:
        logger.exception("Failed to start theme customization demo")
        # Force log flush
        import logging

        for handler in logging.getLogger("dashboard_lego").handlers:
            handler.flush()
        print(f"\n❌ Error: {e}")
        print("📋 Check examples/logs/dashboard_lego.log for details")
        raise
