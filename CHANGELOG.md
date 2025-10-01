# Changelog

All notable changes to the Dashboard Lego project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive documentation updates in English
- Enhanced contributing guidelines with presets sections
- Updated project description and metadata

### Changed
- Documentation language changed from Russian to English
- Improved code examples and installation instructions

## [0.9.0] - 2024-01-XX

### Added
- Initial release of Dashboard Lego library
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
