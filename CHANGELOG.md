# Changelog

All notable changes to the Dashboard Lego project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.13.0] - 2025-10-07

### Added
- **Theme-Aware Styling System**
  - Integration of theme configuration into `BaseBlock` and related classes
  - Automatic styling based on user-defined themes in `create_eda_section` and `create_ml_section`
  - New control panel styles and layouts for improved user interaction
  - Sample datasets: `sample_feature_importance.csv` and `sample_theme_data.csv`

### Changed
- Enhanced responsiveness and visual consistency across dashboard components
- Improved control panel layouts for better user experience

## [0.12.0] - 2025-10-06

### Fixed
- Corrected syntax in `_normalize_subscribes_to` method signature (trailing comma for style consistency)

## [0.11.2] - 2025-10-05

### Added
- **Multi-State Subscriptions Support**
  - `BaseBlock` and subclasses now accept both single state IDs and lists of state IDs for `subscribes_to` parameter
  - New `_normalize_subscribes_to` method for consistent subscription handling
  - Enhanced `StateManager` to manage multi-state subscriptions
  - Integration tests for multi-state subscription behavior

### Changed
- Improved flexibility for complex data interactions across dashboard blocks

## [0.11.0] - 2025-10-02

### Added
- **Enhanced Output and Error Management**
  - New `allow_duplicate_output` parameter in `BaseBlock` and `StaticChartBlock`
  - Comprehensive error handling for Dash callbacks in `DashboardPage`
  - Enhanced `StateManager` with duplicate output validation and detailed logging
  - New `_get_fallback_output` method for safe outputs when errors occur
  - Sample navigation data file: `sample_nav_data.csv`

### Changed
- Updated `DashboardPage` styles to use camelCase for CSS properties
- Enhanced documentation structure with improved Sphinx configuration
- Improved error handling in content loading process

### Fixed
- Documentation paths for src-layout structure
- API documentation to include proper dashboard_lego namespace

## [0.10.0] - 2025-10-01

### Added
- **NEW FEATURE**: Navigation Panel System
  - `NavigationConfig` and `NavigationSection` classes for multi-section dashboards
  - Lazy loading of dashboard sections with factory functions
  - Fixed sidebar navigation with dynamic width calculation
  - Section caching to prevent recreation on revisit
  - Support for Font Awesome icons and Bootstrap styling
  - Example: `examples/08_navigation_dashboard.py`

### Changed
- Enhanced `DashboardPage` to support both standard and navigation modes
- Improved visual styling with custom CSS and responsive design
- Updated validation to require either `blocks` or `navigation` parameter

### Technical Details
- Added 12 comprehensive tests for navigation functionality
- Maintained 85% test coverage across all modules
- All 124 tests pass without regressions

## [0.9.2] - 2025-10-01

### Changed
- **BREAKING CHANGE**: Restructured package to src-layout architecture
  - All modules moved to `src/dashboard_lego/` directory
  - All imports must now use `dashboard_lego.*` prefix (e.g., `from dashboard_lego.blocks import ...`)
  - Migration: `from blocks.chart import X` → `from dashboard_lego.blocks.chart import X`
- Updated package metadata with author information and project URLs
- Improved CI workflows with updated paths for new structure
- Code formatting improvements (isort, flake8 compliance)

### Fixed
- Package installation issue where only `.dist-info` was created without actual code modules
- Import formatting and linter warnings in `__init__.py`

### Added
- PyPI publish workflow for automated releases
- `__all__` export in main `__init__.py` for explicit module exports

## [0.9.0] - 2025-10-01

### Added
- Initial release of Dashboard Lego library
- Comprehensive Sphinx documentation with automatic GitHub Pages deployment
- CHANGELOG and CONTRIBUTING guidelines
- Multiple example dashboards (simple, interactive, presets, ML, layouts)
- Modular architecture with BaseBlock and BaseDataSource
- Core dashboard components:
  - StaticChartBlock for non-interactive charts
  - InteractiveChartBlock for charts with controls
  - KPIBlock for key performance indicators
  - TextBlock for text content
- State management system for block interactivity
- Data source implementations:
  - CSV data source with caching
  - Parquet data source for high-performance loading
  - SQL data source via SQLAlchemy
- EDA presets for common analysis tasks:
  - CorrelationHeatmapPreset
  - GroupedHistogramPreset
  - MissingValuesPreset
  - BoxPlotPreset
- ML presets for machine learning visualizations:
  - MetricCardBlock
  - ConfusionMatrixPreset
  - FeatureImportancePreset
  - ROC_CurvePreset
- Layout presets for common dashboard patterns:
  - one_column, two_column_8_4, three_column_4_4_4
  - kpi_row_top and other specialized layouts
- Comprehensive testing suite:
  - Unit tests for all components
  - Integration tests for dashboard functionality
  - Performance tests and benchmarks
- Development tools and configuration:
  - Black code formatting
  - Flake8 linting
  - MyPy type checking
  - Pre-commit hooks
  - Pytest testing framework
- Documentation:
  - README with examples and quick start guide
  - Contributing guidelines
  - API documentation structure
  - Example dashboards in multiple scenarios
- MIT license
- Python package configuration (pyproject.toml)
- Development dependencies and testing setup

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

---

## Change Types

- **Added** - for new features
- **Changed** - for changes in existing functionality
- **Deprecated** - for soon-to-be removed features
- **Removed** - for removed features
- **Fixed** - for bug fixes
- **Security** - for vulnerability fixes
