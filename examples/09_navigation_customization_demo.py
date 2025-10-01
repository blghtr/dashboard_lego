"""
Example demonstrating navigation customization in Dashboard Lego.

This example shows how to customize the appearance of the navigation sidebar
using the new style parameters in NavigationConfig.

:hierarchy: [Examples | Navigation | Customization Demo]
:relates-to:
 - motivated_by: "Phase 3: Demonstrate navigation customization capabilities"
 - implements: "example: 'navigation customization demo'"
 - uses: ["class: 'NavigationConfig'", "class: 'DashboardPage'"]

:rationale: "Shows practical usage of navigation style customization parameters."
:contract:
 - pre: "User wants to customize navigation appearance"
 - post: "Dashboard with custom-styled navigation is created and displayed"

"""

import pandas as pd

from dashboard_lego.core.datasources import CsvDataSource
from dashboard_lego.core.page import DashboardPage, NavigationConfig, NavigationSection
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
    df.to_csv("sample_nav_data.csv", index=False)

    # Create separate feature importance data
    feature_data = {
        "feature_name": ["feature1", "feature2", "feature3"],
        "importance": [0.3, 0.5, 0.2],
    }

    feature_df = pd.DataFrame(feature_data)
    feature_df.to_csv("sample_nav_feature_importance.csv", index=False)

    return "sample_nav_data.csv"


def create_eda_section():
    """Create EDA section with custom styling."""
    datasource = CsvDataSource("sample_nav_data.csv")
    # Initialize the datasource to ensure data is loaded
    datasource.init_data()

    # Create blocks with custom styling
    correlation_block = CorrelationHeatmapPreset(
        block_id="correlation",
        datasource=datasource,
        subscribes_to="dummy_state",
        title="Custom Correlation Heatmap",
        card_style={"backgroundColor": "#f8f9fa", "border": "2px solid #007bff"},
        card_className="custom-correlation-card",
        title_style={"color": "#007bff", "fontSize": "20px"},
        figure_layout={"title": {"text": "Custom Correlation Analysis"}},
    )

    histogram_block = GroupedHistogramPreset(
        block_id="histogram",
        datasource=datasource,
        title="Custom Distribution Analysis",
        card_style={"backgroundColor": "#e8f5e8", "border": "2px solid #28a745"},
        card_className="custom-histogram-card",
        controls_row_style={"backgroundColor": "#d4edda", "padding": "10px"},
        figure_layout={"title": {"text": "Custom Distribution Analysis"}},
    )

    missing_block = MissingValuesPreset(
        block_id="missing",
        datasource=datasource,
        subscribes_to="dummy_state",
        title="Custom Missing Values",
        card_style={"backgroundColor": "#fff3cd", "border": "2px solid #ffc107"},
        card_className="custom-missing-card",
        graph_style={"height": "400px"},
    )

    return [[correlation_block], [histogram_block], [missing_block]]


def create_ml_section():
    """Create ML section with custom styling."""
    datasource = CsvDataSource("sample_nav_data.csv")
    # Initialize the datasource to ensure data is loaded
    datasource.init_data()

    # Create blocks with custom styling
    confusion_block = ConfusionMatrixPreset(
        block_id="confusion",
        datasource=datasource,
        y_true_col="target",
        y_pred_col="prediction",
        title="Custom Confusion Matrix",
        card_style={"backgroundColor": "#f8d7da", "border": "2px solid #dc3545"},
        card_className="custom-confusion-card",
        figure_layout={"title": {"text": "Custom Confusion Matrix"}},
    )

    # Create separate datasource for feature importance
    feature_datasource = CsvDataSource("sample_nav_feature_importance.csv")
    # Initialize the datasource to ensure data is loaded
    feature_datasource.init_data()

    feature_block = FeatureImportancePreset(
        block_id="feature_importance",
        datasource=feature_datasource,
        feature_col="feature_name",
        importance_col="importance",
        title="Custom Feature Importance",
        card_style={"backgroundColor": "#d1ecf1", "border": "2px solid #17a2b8"},
        card_className="custom-feature-card",
        figure_layout={"title": {"text": "Custom Feature Importance"}},
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
        title="Custom Metrics",
        container_style={"backgroundColor": "#e2e3e5", "border": "2px solid #6c757d"},
        container_className="custom-metrics-container",
        kpi_card_style={"backgroundColor": "#f8f9fa", "border": "1px solid #dee2e6"},
    )

    return [[confusion_block], [feature_block], [metrics_block]]


def create_custom_navigation_dashboard():
    """Create a dashboard with custom navigation styling."""
    # Create sample data
    create_sample_data()

    # Create navigation sections
    sections = [
        NavigationSection(title="📊 EDA Analysis", block_factory=create_eda_section),
        NavigationSection(title="🤖 ML Models", block_factory=create_ml_section),
    ]

    # Create custom navigation configuration
    navigation_config = NavigationConfig(
        sections=sections,
        position="left",
        sidebar_width=3,
        default_section=0,
        # Custom sidebar styling
        sidebar_style={
            "backgroundColor": "#2c3e50",  # Dark blue-gray
            "color": "#ecf0f1",  # Light text
            "borderRight": "3px solid #3498db",  # Blue accent border
            "boxShadow": "2px 0 10px rgba(0,0,0,0.3)",  # Enhanced shadow
        },
        sidebar_className="custom-navigation-sidebar",
        # Custom content area styling
        content_style={
            "backgroundColor": "#f8f9fa",  # Light gray background
            "padding": "2rem",
            "minHeight": "100vh",
        },
        content_className="custom-content-area",
        # Custom navigation styling
        nav_style={
            "backgroundColor": "transparent",
        },
        nav_className="custom-navigation-nav",
        # Custom nav link styling
        nav_link_style={
            "color": "#ecf0f1",
            "borderRadius": "10px",
            "padding": "1rem 1.5rem",
            "marginBottom": "0.5rem",
            "transition": "all 0.3s ease",
            "border": "1px solid transparent",
        },
        nav_link_className="custom-nav-link",
        # Custom active nav link styling
        nav_link_active_style={
            "backgroundColor": "#3498db",  # Blue background for active
            "color": "#ffffff",
            "border": "1px solid #2980b9",
            "transform": "translateX(5px)",  # Slight movement
        },
        nav_link_active_className="custom-nav-link-active",
    )

    # Create dashboard page
    page = DashboardPage(title="Navigation Demo", navigation=navigation_config)

    return page


if __name__ == "__main__":
    import logging

    logger = logging.getLogger("dashboard_lego")

    try:
        logger.info("Starting navigation customization demo...")

        # Create sample data
        logger.info("Creating sample data files...")

        # Create and run the custom navigation dashboard
        logger.info("Creating dashboard page...")
        dashboard = create_custom_navigation_dashboard()
        logger.info("Dashboard page created successfully")

        # Create and configure Dash app
        logger.info("Creating Dash application...")
        from dash import Dash

        app = Dash(__name__, external_stylesheets=[dashboard.theme])

        # Build the layout and register callbacks
        logger.info("Building layout and registering callbacks...")
        app.layout = dashboard.build_layout()
        dashboard.register_callbacks(app)
        logger.info("Layout built and callbacks registered")

        print("🚀 Starting Custom Navigation Dashboard...")
        print("📊 Navigate between EDA Analysis and ML Models sections")
        print("🎨 Notice the custom styling applied to the navigation sidebar")
        print("🌐 Dashboard will be available at: http://localhost:8050")

        logger.info("Starting Dash server on port 8050...")
        app.run(debug=True, port=8050)

    except Exception as e:
        logger.exception("Failed to start navigation customization demo")
        # Force log flush
        import logging

        for handler in logging.getLogger("dashboard_lego").handlers:
            handler.flush()
        print(f"\n❌ Error: {e}")
        print("📋 Check examples/logs/dashboard_lego.log for details")
        raise
