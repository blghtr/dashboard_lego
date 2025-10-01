# 🤝 Contributing to Dashboard Lego

Thank you for your interest in contributing to Dashboard Lego! This guide will help you contribute to the development of the library.

## 🚀 Quick Start

### 1. Fork and Clone

```powershell
# Fork the repository on GitHub, then clone
git clone https://github.com/YOUR_USERNAME/dashboard-lego.git
cd dashboard-lego

# Add upstream repository
git remote add upstream https://github.com/ORIGINAL_OWNER/dashboard-lego.git
```

### 2. Environment Setup

```powershell
# Create virtual environment (recommended: use uv)
uv venv

# Activate environment (Windows)
venv\Scripts\activate

# Install dependencies
uv pip install -e .[dev,docs,ml,sql]
```

### 3. Create a Branch

```powershell
# Create branch for new feature
git checkout -b feature/your-feature-name

# Or for bug fix
git checkout -b fix/bug-description
```

## 📋 Development Process

### 1. Planning

- [ ] Create an Issue to discuss the new feature
- [ ] Ensure the feature aligns with the project architecture
- [ ] Get approval from maintainers

### 2. Development

- [ ] Follow existing code patterns
- [ ] Add type hints for all functions
- [ ] Write docstrings for new classes and methods using the project's Sphinx-compatible format
- [ ] Add tests for new functionality
- [ ] Update documentation as needed

### 3. Testing

```powershell
# Run tests
uv run pytest

# Run with coverage
uv run pytest --cov=dashboard_lego --cov-report=html

# Check code style
uv run black --check .
uv run flake8 .
uv run mypy dashboard_lego
```

### 4. Commit

```powershell
# Add changes
git add .

# Create commit with descriptive message
git commit -m "feat: Add new chart type for time series analysis"
```

## 📝 Code Standards

### Code Style

- Use **Black** for code formatting
- Follow **PEP 8** standards
- Maximum line length: 88 characters
- Use **type hints** for all functions

### Docstrings

Use the project's Sphinx-compatible & AI-friendly format with hierarchical documentation:

```python
def create_chart(data: pd.DataFrame, chart_type: str) -> go.Figure:
    """
    Creates a chart based on the provided data and type.

    :hierarchy: [Core | Chart Creation | create_chart]
    :relates-to:
     - motivated_by: "PRD: Need flexible chart generation for different data types"
     - implements: "function: 'create_chart'"
     - uses: ["interface: 'pd.DataFrame'", "interface: 'go.Figure'"]

    :rationale: "Chose factory pattern for chart creation to support multiple chart types with consistent interface."

    :contract:
     - pre: "data is a valid DataFrame with required columns for chart_type"
     - post: "Returns a configured Plotly Figure ready for display"

    Args:
        data: DataFrame containing the data to visualize
        chart_type: Type of chart to create ('bar', 'line', 'scatter')

    Returns:
        Plotly Figure object

    Raises:
        ValueError: If chart_type is not supported
    """
    pass
```

### Naming Conventions

- **Classes**: PascalCase (`BaseBlock`, `InteractiveChartBlock`)
- **Functions and variables**: snake_case (`create_chart`, `chart_data`)
- **Constants**: UPPER_SNAKE_CASE (`DEFAULT_COLORS`)
- **Private methods**: start with `_` (`_generate_id`)

## 🧪 Testing

### Test Structure

```
tests/
├── unit/
│   ├── test_blocks/
│   ├── test_core/
│   ├── test_presets/
│   └── test_utils/
├── integration/
│   ├── test_dashboard_integration.py
│   ├── test_dashboard_simple_e2e.py
│   └── test_performance.py
└── fixtures/
    └── sample_data.py
```

### Writing Tests

```python
import pytest
from dashboard_lego.blocks.kpi import KPIBlock
from dashboard_lego.core.datasource import BaseDataSource

class TestKPIBlock:
    """Test suite for KPIBlock functionality."""

    def test_kpi_block_initialization(self, mock_datasource):
        """
        Test that KPIBlock initializes correctly.

        :hierarchy: [Unit Tests | Blocks | KPIBlock | Initialization]
        :covers:
         - object: "class: 'KPIBlock'"
         - requirement: "KPIBlock must initialize with valid parameters"

        :scenario: "Verifies that KPIBlock creates a valid instance with given parameters"
        :strategy: "Uses pytest fixtures to create mock datasource and asserts block properties"
        :contract:
         - pre: "Valid datasource and KPI definitions provided"
         - post: "KPIBlock instance created with correct block_id and definitions"

        """
        kpi_definitions = [
            {"key": "total", "title": "Total", "icon": "📊", "color": "primary"}
        ]

        block = KPIBlock(
            block_id="test-kpi",
            datasource=mock_datasource,
            kpi_definitions=kpi_definitions,
            subscribes_to="test_state"
        )

        assert block.block_id == "test-kpi"
        assert len(block.kpi_definitions) == 1
```

### Running Tests

```powershell
# All tests
uv run pytest

# Specific file
uv run pytest tests/unit/test_blocks/test_kpi.py

# With coverage
uv run pytest --cov=dashboard_lego --cov-report=html

# Only fast tests
uv run pytest -m "not slow"
```

## 🎨 Creating Presets

### EDA Presets

EDA (Exploratory Data Analysis) presets are pre-built blocks for common data analysis tasks.

#### Creating a New EDA Preset

1. **Inherit from appropriate base class:**
   ```python
   from blocks.chart import StaticChartBlock
   from core.datasource import BaseDataSource

   class MyEDAPreset(StaticChartBlock):
       """
       Description of what this preset does.

       :hierarchy: [Presets | EDA | MyEDAPreset]
       :relates-to:
        - motivated_by: "Common EDA pattern for [specific analysis]"
        - implements: "preset: 'MyEDAPreset'"
        - uses: ["block: 'StaticChartBlock'"]
       """
   ```

2. **Implement the chart generator:**
   ```python
   def _create_chart(self, df: pd.DataFrame, ctx) -> go.Figure:
       """
       Creates the specific chart for this EDA preset.

       :hierarchy: [Presets | EDA | MyEDAPreset | Chart Generation]
       :covers:
        - object: "method: '_create_chart'"
        - requirement: "Generate appropriate visualization for [analysis type]"
       """
       # Implementation here
       pass
   ```

3. **Add tests:**
   ```python
   def test_my_eda_preset_creates_correct_chart(self, sample_dataframe):
       """Test that MyEDAPreset generates expected chart."""
       # Test implementation
   ```

#### EDA Preset Guidelines

- **Focus on common patterns**: Create presets for frequently used visualizations
- **Handle edge cases**: Ensure presets work with various data types and sizes
- **Provide good defaults**: Set sensible default parameters
- **Document data requirements**: Specify what columns/data types are needed

### ML Presets

ML presets are specialized blocks for machine learning visualizations.

#### Creating a New ML Preset

1. **Choose appropriate base class:**
   ```python
   # For metrics display
   from blocks.kpi import KPIBlock

   class MyMLPreset(KPIBlock):
       """
       ML-specific preset for [specific ML visualization].

       :hierarchy: [Presets | ML | MyMLPreset]
       :relates-to:
        - motivated_by: "ML workflow requires [specific visualization]"
        - implements: "preset: 'MyMLPreset'"
        - uses: ["block: 'KPIBlock'"]
       """
   ```

2. **Implement ML-specific logic:**
   ```python
   def _calculate_ml_metrics(self, df: pd.DataFrame, model=None) -> dict:
       """Calculate ML-specific metrics."""
       # Implementation using scikit-learn or other ML libraries
       pass
   ```

#### ML Preset Guidelines

- **Use scikit-learn integration**: Leverage existing ML libraries
- **Handle model objects**: Accept trained models as parameters
- **Provide metric calculations**: Implement common ML metrics
- **Support different data types**: Handle both classification and regression

### Layout Presets

Layout presets provide common dashboard layouts.

#### Creating a New Layout Preset

1. **Add function to `presets/layouts.py`:**
   ```python
   def my_layout_preset(block1: BaseBlock, block2: BaseBlock) -> list:
       """
       Custom layout for specific dashboard pattern.

       :hierarchy: [Presets | Layouts | my_layout_preset]
       :relates-to:
        - motivated_by: "Common dashboard pattern for [use case]"
        - implements: "function: 'my_layout_preset'"
        - uses: ["interface: 'BaseBlock'"]

       :contract:
        - pre: "Two valid BaseBlock instances provided"
        - post: "Returns layout specification compatible with DashboardPage"
       """
       return [
           [(block1, {'md': 8}), (block2, {'md': 4})],
           # Additional rows as needed
       ]
   ```

#### Layout Preset Guidelines

- **Follow responsive design**: Use Bootstrap grid classes appropriately
- **Document breakpoints**: Specify which screen sizes the layout targets
- **Provide flexibility**: Allow customization of block properties
- **Test responsiveness**: Ensure layouts work across different screen sizes

## 📚 Documentation

### Updating README

- Update README when adding new features
- Add usage examples
- Update dependency lists
- Keep installation instructions current

### API Documentation

- Add docstrings for all public methods using the project's format
- Use type hints for better documentation
- Update examples in docstrings
- Maintain consistency with existing documentation style

### Documentation Structure

```
docs/
├── source/
│   ├── api/
│   │   ├── blocks.rst
│   │   ├── core.rst
│   │   ├── presets.rst
│   │   └── utils.rst
│   ├── conf.py
│   └── index.rst
└── build/
```

## 🔄 Pull Request Process

### 1. Preparing PR

```powershell
# Ensure your branch is up to date
git fetch upstream
git rebase upstream/main

# Run all checks
uv run pytest
uv run black --check .
uv run flake8 .
uv run mypy dashboard_lego
```

### 2. Creating PR

- Fill out the Pull Request template
- Describe changes and their motivation
- Reference related Issues
- Add screenshots for UI changes

### 3. PR Template

```markdown
## Description
Brief description of changes

## Type of Changes
- [ ] Bug fix
- [ ] New feature
- [ ] Refactoring
- [ ] Documentation
- [ ] Tests

## Related Issues
Closes #123

## Testing
- [ ] Added tests
- [ ] All tests pass
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project standards
- [ ] Documentation added/updated
- [ ] CHANGELOG updated
- [ ] Preset guidelines followed (if applicable)
```

## 🏷️ Versioning

The project uses [Semantic Versioning](https://semver.org/):

- **MAJOR**: Breaking API changes
- **MINOR**: New functionality (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

## 🐛 Reporting Bugs

### Bug Report Template

```markdown
## Bug Description
Brief description of the problem

## Steps to Reproduce
1. Go to '...'
2. Click on '...'
3. See error

## Expected Behavior
What should have happened

## Actual Behavior
What actually happened

## Environment
- OS: [e.g. Windows 10]
- Python: [e.g. 3.10.0]
- Dashboard Lego: [e.g. 1.0.0]

## Additional Information
Screenshots, logs, code to reproduce
```

## 💡 Feature Requests

### Feature Request Template

```markdown
## Feature Description
What you want to add

## Motivation
Why this feature is needed

## Proposed Solution
How you envision the implementation

## Alternatives
Other possible solutions

## Additional Information
Usage examples, links to similar solutions
```

## 🎯 Development Priorities

### High Priority
- [ ] Performance improvements
- [ ] Extended chart types
- [ ] Documentation improvements
- [ ] New EDA presets

### Medium Priority
- [ ] Additional ML presets
- [ ] Theme customization
- [ ] Data export functionality
- [ ] Layout preset expansion

### Low Priority
- [ ] Database integration presets
- [ ] Web-based configuration interface
- [ ] Mobile optimization

## 📞 Communication

- **Issues**: For bugs and feature requests
- **Discussions**: For general questions and discussions
- **Email**: team@dashboard-lego.com

## 🙏 Acknowledgments

Thank you to all contributors! Your contributions make the project better.

---

**Thank you for contributing to Dashboard Lego! 🧱✨**
