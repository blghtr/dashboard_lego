# Dashboard Lego 🧱

A modular Python library for building interactive dashboards using Dash and Plotly.

Dashboard Lego allows you to build complex dashboards from independent, reusable "blocks" like building with LEGO bricks. This simplifies development, improves code readability, and promotes component reusability.

---

## ✨ Key Features

- **Modular Architecture**: Build dashboards from independent blocks (KPIs, charts, text)
- **Reactive State Management**: Built-in state manager for easy interactivity between blocks (filters, drill-down, etc.)
- **Flexible Grid System**: Position blocks in any configuration using a grid system based on `dash-bootstrap-components`
- **Data Caching**: Built-in caching at the data source level for improved performance
- **Easy Extension**: Easily create custom blocks and data sources by inheriting from base classes
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
import plotly.graph_objects as go

from core.datasource import BaseDataSource
from core.page import DashboardPage
from blocks.kpi import KPIBlock
from blocks.chart import StaticChartBlock
from presets.layouts import one_column

# 1. Define a data source
class SalesDataSource(BaseDataSource):
    def __init__(self, file_path):
        self.file_path = file_path
        super().__init__()

    def _load_data(self, params: dict) -> pd.DataFrame:
        return pd.read_csv(self.file_path)

    def get_kpis(self) -> dict:
        if self._data is None: return {}
        return {
            "total_sales": self._data["Sales"].sum(),
            "total_units": self._data["UnitsSold"].sum()
        }

    def get_filter_options(self, filter_name: str) -> list:
        return []

    def get_summary(self) -> str:
        return ""

# 2. Define a plotting function
def plot_sales_by_fruit(df: pd.DataFrame, ctx) -> go.Figure:
    sales_by_fruit = df.groupby("Fruit")["Sales"].sum().reset_index()
    return px.bar(sales_by_fruit, x="Fruit", y="Sales", title="Sales by Fruit")

# 3. Initialize your data source and blocks
datasource = SalesDataSource(file_path="examples/sample_data.csv")
datasource.init_data()

kpi_block = KPIBlock(
    block_id="sales_kpis",
    datasource=datasource,
    kpi_definitions=[
        {"key": "total_sales", "title": "Total Sales", "color": "success"},
        {"key": "total_units", "title": "Total Units Sold", "color": "info"},
    ],
    subscribes_to="dummy_state"
)

chart_block = StaticChartBlock(
    block_id="sales_chart",
    datasource=datasource,
    title="Fruit Sales",
    chart_generator=plot_sales_by_fruit,
    subscribes_to="dummy_state"
)

# 4. Assemble the dashboard page using layout presets
dashboard_page = DashboardPage(
    title="Simple Sales Dashboard",
    blocks=one_column([kpi_block, chart_block]),  # Stack blocks vertically
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

## 🚀 Roadmap

- [ ] Enhanced chart types and customization options
- [ ] Real-time data streaming capabilities
- [ ] Advanced theming and styling system
- [ ] Export functionality (PDF, PNG, etc.)
- [ ] Web-based dashboard builder interface
- [ ] Additional ML visualization presets
- [ ] Database connection presets
- [ ] Mobile-responsive optimizations

---

**Build amazing dashboards with Dashboard Lego! 🧱✨**
