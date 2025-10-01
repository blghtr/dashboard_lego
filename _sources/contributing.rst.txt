Contributing to Dashboard Lego
===============================

We welcome contributions to Dashboard Lego! This guide will help you get started.

Getting Started
---------------

1. **Fork the Repository**: Fork the project on GitHub
2. **Clone Your Fork**: Clone your fork locally
3. **Set Up Development Environment**: Install dependencies and tools
4. **Create a Branch**: Create a feature branch for your changes

Development Setup
-----------------

Install development dependencies:

.. code-block:: bash

   # Clone your fork
   git clone https://github.com/YOUR_USERNAME/dashboard-lego.git
   cd dashboard-lego

   # Create virtual environment
   uv venv
   uv pip install -e .[dev,docs,ml,sql]

   # Install pre-commit hooks
   pre-commit install

Code Style
----------

Dashboard Lego follows these coding standards:

* **Black** for code formatting (88 character line length)
* **Flake8** for linting
* **MyPy** for type checking
* **Sphinx** for documentation

Run code quality checks:

.. code-block:: bash

   # Format code
   uv run black .

   # Check linting
   uv run flake8 .

   # Check types
   uv run mypy dashboard_lego

Documentation Standards
-----------------------

All code must include comprehensive documentation:

Docstring Format
~~~~~~~~~~~~~~~~

Use the project's Sphinx-compatible format:

.. code-block:: python

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

Testing
-------

All new code must include tests:

Test Structure
~~~~~~~~~~~~~~

.. code-block:: python

   def test_my_function_behavior(self, sample_data):
       """
       Test that my_function behaves correctly.

       :hierarchy: [Unit Tests | MyModule | MyFunction | Behavior]
       :covers:
        - object: "function: 'my_function'"
        - requirement: "Function must process data correctly"

       :scenario: "Verifies that my_function processes sample data as expected"
       :strategy: "Uses pytest fixtures and assertions to validate behavior"
       :contract:
        - pre: "sample_data is a valid DataFrame"
        - post: "Function returns expected result"
       """
       result = my_function(sample_data)
       assert result is not None
       assert len(result) > 0

Running Tests
~~~~~~~~~~~~~

.. code-block:: bash

   # Run all tests
   uv run pytest

   # Run with coverage
   uv run pytest --cov=dashboard_lego --cov-report=html

   # Run specific test file
   uv run pytest tests/unit/test_my_module.py

Creating Presets
----------------

EDA Presets
~~~~~~~~~~~

Create presets for common exploratory data analysis tasks:

.. code-block:: python

   class MyEDAPreset(StaticChartBlock):
       """
       Description of what this preset does.

       :hierarchy: [Presets | EDA | MyEDAPreset]
       :relates-to:
        - motivated_by: "Common EDA pattern for [specific analysis]"
        - implements: "preset: 'MyEDAPreset'"
        - uses: ["block: 'StaticChartBlock'"]
       """

       def _create_chart(self, df: pd.DataFrame, ctx) -> go.Figure:
           """Create the specific chart for this EDA preset."""
           # Implementation here
           pass

ML Presets
~~~~~~~~~~

Create presets for machine learning visualizations:

.. code-block:: python

   class MyMLPreset(KPIBlock):
       """
       ML-specific preset for [specific ML visualization].

       :hierarchy: [Presets | ML | MyMLPreset]
       :relates-to:
        - motivated_by: "ML workflow requires [specific visualization]"
        - implements: "preset: 'MyMLPreset'"
        - uses: ["block: 'KPIBlock'"]
       """
       pass

Pull Request Process
--------------------

1. **Create Feature Branch**: ``git checkout -b feature/your-feature-name``
2. **Make Changes**: Implement your feature with tests and documentation
3. **Run Quality Checks**: Ensure all tests pass and code quality checks succeed
4. **Commit Changes**: Use descriptive commit messages
5. **Push Branch**: Push your branch to your fork
6. **Create Pull Request**: Submit PR with detailed description

PR Template
~~~~~~~~~~~

.. code-block:: markdown

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

Release Process
---------------

Versioning follows Semantic Versioning (MAJOR.MINOR.PATCH):

* **MAJOR**: Breaking API changes
* **MINOR**: New features (backward compatible)
* **PATCH**: Bug fixes (backward compatible)

Getting Help
------------

* **Issues**: Report bugs and request features
* **Discussions**: Ask questions and discuss ideas
* **Email**: team@dashboard-lego.com

Thank you for contributing to Dashboard Lego! 🧱✨
