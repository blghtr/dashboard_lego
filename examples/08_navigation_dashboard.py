"""
Demo: Navigation-based Dashboard with Lazy Loading

This example demonstrates the new navigation feature:
- Sidebar with multiple sections
- Lazy loading of section content
- Each section has its own blocks and layout
- Using StaticChartBlock with chart_generator functions

"""

import pandas as pd
import plotly.express as px
from dash import Dash

from dashboard_lego.blocks.chart import StaticChartBlock
from dashboard_lego.blocks.kpi import KPIBlock
from dashboard_lego.core import DashboardPage, NavigationConfig, NavigationSection
from dashboard_lego.core.datasources.csv_source import CsvDataSource


def create_sample_data():
    """Create sample sales data."""
    df = pd.DataFrame(
        {
            "Date": pd.date_range("2024-01-01", periods=100, freq="D"),
            "Sales": [100 + i * 2 + (i % 10) * 5 for i in range(100)],
            "Profit": [50 + i * 1.5 + (i % 7) * 3 for i in range(100)],
            "Category": ["A", "B", "C"] * 33 + ["A"],
            "Region": ["North", "South", "East", "West"] * 25,
        }
    )
    df.to_csv("sample_nav_data.csv", index=False)
    return "sample_nav_data.csv"


class SalesDataSource(CsvDataSource):
    """Extended CSV datasource with KPI calculations."""

    def get_kpis(self):
        """Calculate and return KPIs."""
        df = self.get_processed_data()
        return {
            "total_sales": df["Sales"].sum(),
            "total_profit": df["Profit"].sum(),
            "avg_sales": df["Sales"].mean(),
            "record_count": len(df),
        }


# ==================== Chart Generator Functions ====================


def plot_sales_trend(df, ctx):
    """Generate sales trend line chart."""
    fig = px.line(
        df,
        x="Date",
        y="Sales",
        title="Sales Trend Over Time",
        labels={"Sales": "Sales ($)", "Date": "Date"},
    )
    fig.update_layout(template="plotly_white")
    return fig


def plot_profit_trend(df, ctx):
    """Generate profit trend line chart."""
    fig = px.line(
        df,
        x="Date",
        y="Profit",
        title="Profit Trend Over Time",
        labels={"Profit": "Profit ($)", "Date": "Date"},
    )
    fig.update_layout(template="plotly_white")
    return fig


def plot_sales_scatter(df, ctx):
    """Generate sales scatter plot."""
    fig = px.scatter(
        df,
        x="Date",
        y="Sales",
        color="Category",
        title="Sales Data Points by Category",
        labels={"Sales": "Sales ($)", "Date": "Date"},
    )
    fig.update_layout(template="plotly_white")
    return fig


def plot_sales_by_category(df, ctx):
    """Generate sales by category bar chart."""
    category_sales = df.groupby("Category")["Sales"].sum().reset_index()
    fig = px.bar(
        category_sales,
        x="Category",
        y="Sales",
        title="Total Sales by Category",
        labels={"Sales": "Total Sales ($)"},
    )
    fig.update_layout(template="plotly_white")
    return fig


def plot_profit_by_region(df, ctx):
    """Generate profit by region bar chart."""
    region_profit = df.groupby("Region")["Profit"].sum().reset_index()
    fig = px.bar(
        region_profit,
        x="Region",
        y="Profit",
        title="Total Profit by Region",
        labels={"Profit": "Total Profit ($)"},
        color="Profit",
        color_continuous_scale="Viridis",
    )
    fig.update_layout(template="plotly_white")
    return fig


def plot_sales_distribution(df, ctx):
    """Generate sales distribution box plot."""
    fig = px.box(
        df,
        x="Category",
        y="Sales",
        title="Sales Distribution by Category",
        labels={"Sales": "Sales ($)"},
        color="Category",
    )
    fig.update_layout(template="plotly_white")
    return fig


def plot_sales_profit_correlation(df, ctx):
    """Generate sales vs profit scatter plot."""
    fig = px.scatter(
        df,
        x="Sales",
        y="Profit",
        color="Category",
        title="Sales vs Profit Correlation",
        labels={"Sales": "Sales ($)", "Profit": "Profit ($)"},
    )
    fig.update_layout(template="plotly_white")
    return fig


def plot_sales_histogram(df, ctx):
    """Generate sales distribution histogram."""
    fig = px.histogram(
        df,
        x="Sales",
        nbins=20,
        title="Sales Distribution Histogram",
        labels={"Sales": "Sales ($)"},
    )
    fig.update_layout(template="plotly_white")
    return fig


def plot_profit_histogram(df, ctx):
    """Generate profit distribution histogram."""
    fig = px.histogram(
        df,
        x="Profit",
        nbins=20,
        title="Profit Distribution Histogram",
        labels={"Profit": "Profit ($)"},
    )
    fig.update_layout(template="plotly_white")
    return fig


def overview_section():
    """Factory for Overview section - created lazily on first visit!"""
    print("🔨 Creating Overview section blocks...")

    ds = SalesDataSource(file_path="sample_nav_data.csv")
    ds.init_data()  # Load data into datasource

    # KPI Blocks
    kpi_sales = KPIBlock(
        block_id="overview-kpi-sales",
        datasource=ds,
        kpi_definitions=[
            {"key": "total_sales", "title": "Total Sales", "color": "success"}
        ],
        subscribes_to="nav_dummy_state",
    )

    kpi_profit = KPIBlock(
        block_id="overview-kpi-profit",
        datasource=ds,
        kpi_definitions=[
            {"key": "total_profit", "title": "Total Profit", "color": "info"}
        ],
        subscribes_to="nav_dummy_state",
    )

    # Chart Blocks
    chart1 = StaticChartBlock(
        block_id="overview-chart-1",
        datasource=ds,
        title="📈 Sales Trend",
        chart_generator=plot_sales_trend,
        subscribes_to="nav_dummy_state",
    )

    chart2 = StaticChartBlock(
        block_id="overview-chart-2",
        datasource=ds,
        title="💰 Profit Trend",
        chart_generator=plot_profit_trend,
        subscribes_to="nav_dummy_state",
    )

    chart3 = StaticChartBlock(
        block_id="overview-chart-3",
        datasource=ds,
        title="📊 Sales Data Points",
        chart_generator=plot_sales_scatter,
        subscribes_to="nav_dummy_state",
    )

    return [
        [(kpi_sales, {"md": 6}), (kpi_profit, {"md": 6})],
        [(chart1, {"md": 6}), (chart2, {"md": 6})],
        [chart3],
    ]


def analytics_section():
    """Factory for Analytics section - lazy loaded!"""
    print("🔨 Creating Analytics section blocks...")

    ds = SalesDataSource(file_path="sample_nav_data.csv")
    ds.init_data()  # Load data into datasource

    chart1 = StaticChartBlock(
        block_id="analytics-chart-1",
        datasource=ds,
        title="📊 Sales by Category",
        chart_generator=plot_sales_by_category,
        subscribes_to="nav_dummy_state",
    )

    chart2 = StaticChartBlock(
        block_id="analytics-chart-2",
        datasource=ds,
        title="🌍 Profit by Region",
        chart_generator=plot_profit_by_region,
        subscribes_to="nav_dummy_state",
    )

    chart3 = StaticChartBlock(
        block_id="analytics-chart-3",
        datasource=ds,
        title="📦 Sales Distribution by Category",
        chart_generator=plot_sales_distribution,
        subscribes_to="nav_dummy_state",
    )

    return [
        [(chart1, {"md": 4}), (chart2, {"md": 4}), (chart3, {"md": 4})],
    ]


def reports_section():
    """Factory for Reports section - lazy loaded!"""
    print("🔨 Creating Reports section blocks...")

    ds = SalesDataSource(file_path="sample_nav_data.csv")
    ds.init_data()  # Load data into datasource

    kpi_count = KPIBlock(
        block_id="reports-kpi-count",
        datasource=ds,
        kpi_definitions=[
            {
                "key": "record_count",
                "title": "Total Records",
                "color": "primary",
            }
        ],
        subscribes_to="nav_dummy_state",
    )

    kpi_avg = KPIBlock(
        block_id="reports-kpi-avg",
        datasource=ds,
        kpi_definitions=[
            {"key": "avg_sales", "title": "Avg Sales", "color": "warning"}
        ],
        subscribes_to="nav_dummy_state",
    )

    chart1 = StaticChartBlock(
        block_id="reports-chart-1",
        datasource=ds,
        title="💹 Sales vs Profit Correlation",
        chart_generator=plot_sales_profit_correlation,
        subscribes_to="nav_dummy_state",
    )

    chart2 = StaticChartBlock(
        block_id="reports-chart-2",
        datasource=ds,
        title="📊 Sales Distribution",
        chart_generator=plot_sales_histogram,
        subscribes_to="nav_dummy_state",
    )

    chart3 = StaticChartBlock(
        block_id="reports-chart-3",
        datasource=ds,
        title="💰 Profit Distribution",
        chart_generator=plot_profit_histogram,
        subscribes_to="nav_dummy_state",
    )

    return [
        [(kpi_count, {"md": 6}), (kpi_avg, {"md": 6})],
        [chart1],
        [(chart2, {"md": 6}), (chart3, {"md": 6})],
    ]


def main():
    """Main application entry point."""
    # Create sample data
    data_path = create_sample_data()
    print(f"✅ Sample data created at: {data_path}")

    # Define navigation configuration
    nav_config = NavigationConfig(
        sections=[
            NavigationSection(title="Overview", block_factory=overview_section),
            NavigationSection(title="Analytics", block_factory=analytics_section),
            NavigationSection(title="Reports", block_factory=reports_section),
        ],
        position="left",
        sidebar_width=3,
        default_section=0,
    )

    # Create dashboard page with navigation
    page = DashboardPage(
        title="📊 Sales Dashboard with Navigation",
        navigation=nav_config,
    )

    # Create Dash app with dark theme
    app = Dash(
        __name__,
        suppress_callback_exceptions=True,
        external_stylesheets=[
            "https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/css/all.min.css",
            "https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css",
        ],
    )
    app.layout = page.build_layout()
    page.register_callbacks(app)

    print("\n" + "=" * 60)
    print("🚀 Navigation Dashboard Starting...")
    print("=" * 60)
    print("📌 Features demonstrated:")
    print("  • Sidebar navigation with 3 sections")
    print("  • Lazy loading - sections created only when clicked")
    print("  • Each section has independent blocks and layout")
    print("  • Watch console for '🔨 Creating...' messages")
    print("=" * 60)
    print("\n🌐 Open: http://127.0.0.1:8050")
    print("💡 Click different sections and watch the console!")
    print("   First click = lazy creation, next clicks = cached\n")

    app.run(debug=True)


if __name__ == "__main__":
    main()
