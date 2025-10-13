"""
Quick Dashboard Example.

Demonstrates the quick_dashboard() factory for rapid prototyping.
Works in Jupyter notebooks and Python scripts.

Usage:
    python examples/jupyter_quick_dashboard.py
"""

import pandas as pd

from dashboard_lego.utils import quick_dashboard

# Create sample data
df = pd.DataFrame(
    {
        "Product": ["Widget", "Gadget", "Tool", "Device", "Widget", "Gadget"],
        "Category": [
            "Electronics",
            "Electronics",
            "Tools",
            "Electronics",
            "Electronics",
            "Tools",
        ],
        "Sales": [100, 200, 150, 180, 120, 90],
        "Revenue": [1000, 2000, 1500, 1800, 1200, 900],
        "Quantity": [10, 15, 8, 12, 9, 7],
    }
)

# Create quick dashboard with 4 cards (2x2 grid)
app = quick_dashboard(
    df=df,
    cards=[
        {
            "type": "metric",
            "column": "Revenue",
            "agg": "sum",
            "title": "Total Revenue",
            "color": "success",
        },
        {
            "type": "metric",
            "column": "Sales",
            "agg": "mean",
            "title": "Average Sales",
            "color": "info",
        },
        {
            "type": "chart",
            "plot_type": "bar",
            "x": "Product",
            "y": "Sales",
            "title": "Sales by Product",
        },
        {
            "type": "chart",
            "plot_type": "scatter",
            "x": "Sales",
            "y": "Revenue",
            "color": "Category",
            "title": "Sales vs Revenue",
        },
    ],
    title="Quick Sales Dashboard",
    theme="lux",
)

if __name__ == "__main__":
    print("=" * 70)
    print("Quick Dashboard Example")
    print("=" * 70)
    print("\nFeatures:")
    print("  ✓ 2 metric cards (Total Revenue, Average Sales)")
    print("  ✓ 2 chart cards (Bar chart, Scatter plot)")
    print("  ✓ Smart layout: metrics row + charts 50/50")
    print("  ✓ Zero disk I/O (cache_ttl=0)")
    print("  ✓ Lux theme")
    print("\nStarting server at http://127.0.0.1:8050/")
    print("Press Ctrl+C to stop")
    print("=" * 70)

    app.run(debug=True)
