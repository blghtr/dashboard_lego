# Dashboard Lego 🧱

<div align="center">
  <img src="example.png" alt="Dashboard Lego v0.15 Showcase - Cyborg Theme" width="800"/>
  <p><em>Dashboard Lego v0.15 Showcase Dashboard with Cyborg Theme</em></p>
</div>

A modular Python library for building interactive dashboards using Dash and Plotly.

Dashboard Lego allows you to build complex dashboards from independent, reusable "blocks" like building with LEGO bricks. This simplifies development, improves code readability, and promotes component reusability.

---

## ✨ Key Features

- **Modular Architecture**: Build dashboards from independent blocks (KPIs, charts, text)
- **Reactive State Management**: Built-in state manager for easy interactivity between blocks (filters, drill-down, etc.)
- **Navigation System**: Multi-section dashboards with sidebar/tab navigation and lazy-loaded sections
- **Flexible Grid System**: Position blocks in any configuration using a grid system based on `dash-bootstrap-components`
- **Theme System**: Comprehensive theming with pre-built themes (light, dark, and 10+ Bootstrap themes) and custom theme support
- **Data Caching**: 2-stage pipeline with independent caching (Build → Filter) for optimal performance
- **No Subclassing Required**: Use composition pattern with `DataBuilder` + `DataFilter` instead of inheriting from `BaseDataSource`
- **TypedChartBlock System**: Plot registry pattern for reusable chart components with embedded controls
- **Presets & Layouts**: Pre-built EDA and ML visualization blocks, plus layout presets for common dashboard patterns
- **Comprehensive Testing**: Full test coverage with unit, integration, and performance tests

## 📦 Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/your-username/dashboard-lego.git
   cd dashboard-lego
   ```

2. **Create a virtual environment and install dependencies:**
   We recommend using `uv` for fast installation.
   ```bash
   # Install uv
   pip install uv

   # Create environment and install dependencies
   uv venv
   uv pip install -e .[dev]
   ```

## 🚀 Quick Start

Below is an example of a simple dashboard. The complete code can be found in `examples/01_simple_dashboard.py`.

```python
# examples/01_simple_dashboard.py

import dash
import dash_bootstrap_components as dbc
import plotly.express as px
import pandas as pd

from dashboard_lego.core import BaseDataSource, DataBuilder, DashboardPage
from dashboard_lego.blocks.metrics import MetricsBlock
from dashboard_lego.blocks.typed_chart import TypedChartBlock
from dashboard_lego.presets.layouts import one_column

# 1. Define a DataBuilder (v0.15+ pattern)
class SalesDataBuilder(DataBuilder):
    def __init__(self, file_path):
        super().__init__()
        self.file_path = file_path

    def build(self, params):
        """Load CSV and add calculated fields."""
        df = pd.read_csv(self.file_path)
        # Add any calculated fields here
        return df

# 2. Create datasource using composition (no inheritance!)
datasource = BaseDataSource(
    data_builder=SalesDataBuilder("examples/sample_data.csv")
)

# 3. Create blocks using v0.15 API
# MetricsBlock replaces get_kpis() pattern
metrics_block = MetricsBlock(
    block_id="sales_metrics",
    datasource=datasource,
    metrics_spec={
        "total_sales": {
            "column": "Sales",
            "agg": "sum",
            "title": "Total Sales",
            "color": "success"
        },
        "total_units": {
            "column": "UnitsSold",
            "agg": "sum",
            "title": "Total Units Sold",
            "color": "info"
        }
    },
    subscribes_to="dummy_state"
)

# TypedChartBlock with block-level transform
chart_block = TypedChartBlock(
    block_id="sales_chart",
    datasource=datasource,
    plot_type="bar",
    plot_params={"x": "Fruit", "y": "Sales"},
    plot_kwargs={"title": "Sales by Fruit"},
    title="Fruit Sales",
    subscribes_to="dummy_state",
    # Optional: aggregate data at block level
    transform_fn=lambda df: df.groupby("Fruit")["Sales"].sum().reset_index()
)

# 4. Assemble the dashboard page
dashboard_page = DashboardPage(
    title="Simple Sales Dashboard",
    blocks=one_column([metrics_block, chart_block]),
    theme=dbc.themes.LUX
)

# 5. Run the application
app = dash.Dash(__name__, external_stylesheets=[dashboard_page.theme])
app.layout = dashboard_page.build_layout()
dashboard_page.register_callbacks(app)

if __name__ == "__main__":
    app.run_server(debug=True)
```

To run this example:
```bash
python examples/01_simple_dashboard.py
```

For a comprehensive API reference with detailed contracts, hierarchies, and advanced patterns, see **[DASHBOARD_LEGO_GUIDE.md](DASHBOARD_LEGO_GUIDE.md)**.

## 🎯 Quick Dashboard

For rapid prototyping in Jupyter notebooks, Python scripts, or anywhere Dash runs, use the `quick_dashboard()` factory:

```python
from dashboard_lego.utils.quick_dashboard import quick_dashboard
import pandas as pd

# Load your data
df = pd.DataFrame({
    'Product': ['Widget', 'Gadget', 'Tool', 'Device'],
    'Sales': [100, 200, 150, 180],
    'Revenue': [1000, 2000, 1500, 1800]
})

# Create dashboard with 3 lines of code
app = quick_dashboard(
    df=df,
    cards=[
        {"type": "metric", "column": "Revenue", "agg": "sum",
         "title": "Total Revenue", "color": "success"},
        {"type": "chart", "plot_type": "bar", "x": "Product", "y": "Sales",
         "title": "Sales by Product"}
    ],
    title="Sales Dashboard",
    theme="lux"
)

# Run (opens in browser tab)
app.run(debug=True)
```

**Card Types:**
- **Metric**: `{"type": "metric", "column": str, "agg": str, "title": str, "color": str}`
- **Chart**: `{"type": "chart", "plot_type": str, "x": str, "y": str, "title": str}`
- **Text**: `{"type": "text", "content": str}`

**Installation:**
```bash
pip install dashboard-lego
```

### IPython Magic Commands

For ultra-fast dashboard creation in Jupyter, use magic commands:

```python
# Load extension once per session
%load_ext dashboard_lego.ipython_magics

# Create dashboard in one line
%dashboard df -m Sales sum "Total Sales" success -c bar Product Sales "Sales Chart"

# Set theme preference
%dashboard_theme cyborg

# Or use cell magic for multi-line config
%%dashboard_cell
dataframe: df
cards:
  - metric: Revenue, sum, "Total Revenue"
  - chart: bar, Product, Sales, "Sales"
```

Magic commands reduce typing and are perfect for quick exploration.

## 🔗 Interactivity

`dashboard-lego` makes it easy to link blocks together. One block can publish its state (e.g., a filter value), and other blocks can subscribe to that state and update accordingly.

This is implemented through the `StateManager`, which automatically creates Dash callbacks.

See the complete interactive dashboard example in `examples/02_interactive_dashboard.py`.

## 🎨 Presets and Layouts

### EDA Presets

Presets are ready-to-use blocks for standard data analysis tasks (EDA) that significantly reduce boilerplate code:

- **`CorrelationHeatmapPreset`**: Automatically builds a correlation heatmap for all numeric columns in your data
- **`GroupedHistogramPreset`**: Creates an interactive histogram with dropdowns for column and grouping selection
- **`MissingValuesPreset`**: Displays a bar chart showing the percentage of missing values for each column, helping quickly assess data quality
- **`BoxPlotPreset`**: Allows comparing distributions of a numeric feature across different categories using interactive box plot charts

Example usage of presets can be found in `examples/03_presets_dashboard.py`.

### ML Presets

Machine learning visualization presets for common ML workflows:

- **`MetricCardBlock`**: Compact display for ML metrics in a list format
- **`ConfusionMatrixPreset`**: Interactive confusion matrix visualization
- **`FeatureImportancePreset`**: Feature importance charts for model interpretation
- **`ROC_CurvePreset`**: ROC curve visualization for classification models

### Layout Presets

`DashboardPage` supports declarative layout schemas:

- Cell: `Block` or `(Block, { 'xs|sm|md|lg|xl': int, 'offset': int, 'align': str, 'className': str, 'style': dict, 'children': [row_specs] })`
- Row: `[cells]` or `([cells], { 'align': str, 'justify': str, 'g': int, 'className': str, 'style': dict })`

If widths are not specified, for backward compatibility, automatic equal division is set via `width`.

The `presets/layouts.py` module provides common templates: `one_column`, `two_column_8_4`, `three_column_4_4_4`, `kpi_row_top`, etc.

## 📊 Data Sources

Dashboard Lego supports multiple data source types:

- **CSV Source**: Load data from CSV files with automatic caching
- **Parquet Source**: High-performance columnar data loading
- **SQL Source**: Connect to databases via SQLAlchemy
- **Custom Sources**: Inherit from `BaseDataSource` to create your own data providers

## 🧪 Testing

The library is covered by comprehensive tests. To run tests:

```bash
# Make sure you have dev dependencies installed
# uv pip install -e .[dev,docs,ml,sql]

# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=dashboard_lego --cov-report=html
```

## 📚 Documentation

### API Reference Guide

For AI agents, LLMs, and developers, we provide a comprehensive API reference:
- **[Dashboard Lego API Guide](DASHBOARD_LEGO_GUIDE.md)**: Complete, machine-parseable API documentation with contracts, hierarchies, and examples for all modules

### Building Documentation Locally

```bash
cd docs

# Build and serve locally (opens http://localhost:8000)
make serve

# Just build HTML
make html

# Clean and rebuild
make clean && make html

# Check docs build without errors
make check
```

### Documentation Structure

- **API Reference**: `DASHBOARD_LEGO_GUIDE.md` - Comprehensive API documentation
- **API Documentation**: Automatically generated from docstrings
- **User Guides**: Installation, quick start, and concepts
- **Examples**: Check the `examples/` directory for various use cases
- **Contributing**: See `CONTRIBUTING.md` for development guidelines
- **Changelog**: Track changes in `CHANGELOG.md`

### Publishing Documentation

**Automatic (Recommended):**
- Documentation is automatically built and published to GitHub Pages when tests pass on `main` branch
- Available at: `https://blghtr.github.io/dashboard_lego/`

**Note:** No manual publishing needed! CI handles everything automatically.

## 🛠️ Development

### Prerequisites

- Python 3.10+
- uv (recommended) or pip

### Development Setup

```bash
# Clone and setup
[uv] pip install dashboard-lego

# Run pre-commit hooks
pre-commit install

# Run tests
uv run pytest
```

### Code Style

- **Black** for code formatting
- **Flake8** for linting
- **MyPy** for type checking
- **Pre-commit** hooks for automated checks

## 🤝 Contributing

We welcome contributions! Please see `CONTRIBUTING.md` for detailed information on:

- Development setup and guidelines
- Code style and standards
- Testing requirements
- Pull request process
- Creating presets and custom blocks

## 📄 License

This project is distributed under the MIT License. See the `LICENSE` file for details.


---

**Build amazing dashboards with Dashboard Lego! 🧱✨**
