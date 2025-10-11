# Changelog

All notable changes to the Dashboard Lego project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.15.1] - 2025-10-11

### Added

#### Metrics Factory Pattern

- **`SingleMetricBlock`**: Atomic block for displaying a single metric value
  - Compact card design (content-driven height)
  - Theme-aware color resolution via `ThemeConfig`
  - Supports conditional coloring via `color_rules` parameter
  - Example: `SingleMetricBlock(block_id="revenue", datasource=ds, metric_spec={...})`

- **`get_metric_row()` Factory Function**: Creates rows of individual metric blocks
  - Returns `(List[SingleMetricBlock], row_options)` tuple
  - Compatible with `DashboardPage` layout format
  - Enables natural composition with other blocks
  - Example: `metrics, opts = get_metric_row(metrics_spec={...}, datasource=ds)`

- **Layout Height Contract Documentation**: Formalized content-driven height behavior
  - Blocks size naturally to content (industry standard)
  - No fixed heights or CSS hacks
  - Preserves Bootstrap responsive breakpoints
  - Reference: Grafana, Tableau, Looker, Metabase pattern

#### Sidebar Enhancements

- **Adaptive Layout**: Sidebar pushes content instead of overlaying (desktop)
  - `push_content` parameter in `SidebarConfig` (default: `True`)
  - CSS transitions for smooth content shifting
  - Mobile-responsive: overlays on small screens
  - CSS in `examples/assets/offcanvas-controls.css`

### Changed

- **`MetricsBlock`**: Deprecated in favor of factory pattern
  - Added deprecation warning in `__init__`
  - Maintained for backward compatibility
  - Violates layout contracts (returns `dbc.Row` instead of single component)
  - Migration guide in `docs/source/guide/blocks.rst`

- **Block Card Styling**: Removed `mb-4` from base classes
  - `TypedChartBlock`: Card uses `h-100` only (spacing handled by Row)
  - `TextBlock`: Card uses `h-100` only
  - `ControlPanelBlock`: Card uses `h-100` only
  - Rationale: Row-level spacing prevents flexbox interference

- **`TypedChartBlock`**: Removed default `minHeight` on graphs
  - Previous: `minHeight: "400px"` caused empty space
  - Current: Natural graph sizing (content-driven)
  - Preserves user `graph_style` overrides

### Fixed

- **`kpi_row_top()` Layout Preset**: Fixed tuple concatenation error
  - Root cause: Attempted to concatenate tuple + list
  - Solution: Build result as list, append rows consistently
  - Result: Works with factory-created metric blocks

### Documentation

- **`docs/source/guide/blocks.rst`**: Added Metrics Factory Pattern section
  - Usage examples with `get_metric_row()`
  - Migration guide from `MetricsBlock`
  - Conditional coloring examples
  - Theme integration documentation

- **`docs/source/guide/contracts.rst`**: Updated Layout Height Contract
  - Documented content-driven height behavior
  - Explained Bootstrap flexbox limitations
  - Industry standard justification
  - Design decision rationale

### Technical Details

**Metrics Factory Pattern:**
```python
# Factory creates atomic blocks
metrics, row_opts = get_metric_row(
    metrics_spec={
        'revenue': {'column': 'Revenue', 'agg': 'sum', 'color': 'success'}
    },
    datasource=datasource
)

# Use in page layout
page = DashboardPage(..., blocks=[
    (metrics, row_opts),  # Metrics row
    [chart1, chart2]      # Charts row
])
```

**Decision Cache:**
- `metric_architecture`: Factory pattern over composite block for layout compliance
- `layout_heights`: Content-driven sizing (industry standard) over forced equal heights
- `theme_colors`: Bootstrap theme names resolved via ThemeConfig (no hardcoded hex)

## [0.15.0] - 2025-10-10

### Breaking Changes

#### Core Architecture Changes

- **2-Stage Pipeline (Simplified)**: Data flows through Build → Transform (was: Load → Preprocess → Filter)
  - Stage 1: **Build** (load + process) - handles data loading AND transformation
  - Stage 2: **Transform** (filter + aggregate) - applies transformations and filtering

- **PreProcessor renamed to DataBuilder**: Better semantic clarity
  - `PreProcessor` → `DataBuilder` (combines loading + processing)
  - Method: `process()` → `build()`

- **DataFilter renamed to DataTransformer**: Broader semantic contract
  - `DataFilter` → `DataTransformer` (filter + aggregate + reshape)
  - Method: `filter()` → `transform()`
  - Enables aggregation, pivoting, and any df→df transformation

- **BaseDataSource is now concrete**: No more abstract methods!
  - Removed: `_load_raw_data()`, `get_kpis()`, `get_filter_options()`, `get_summary()`
  - Pattern: Pass `DataBuilder` and `DataTransformer` to constructor

- **New MetricsBlock**: Replaces `datasource.get_kpis()` pattern
  - Calculate metrics in blocks, not datasources
  - Supports custom aggregation functions (str or callable)
  - Optional dtype conversion

### Added

#### Block-Level Data Transformations (v0.15)

- **`transform_fn` parameter in BaseBlock/TypedChartBlock**: Apply block-specific transformations
  - Enables aggregation, pivoting, filtering AFTER global filters
  - Example: `transform_fn=lambda df: df.groupby('Product')['Revenue'].sum().head(10)`
  - Use case: Different charts need different aggregations of same filtered data

- **Symmetric DataSource API**: Factory methods for lambda-based customization
  - `with_builder_fn(lambda params: df)` - Custom data loading/building with lambda
  - `with_transform_fn(lambda df: df)` - Custom transformation (chained after global filters)
  - `with_builder(builder_instance)` - Replace builder with DataBuilder instance
  - `with_transformer(transformer_instance)` - Replace transformer with DataTransformer instance
  - All methods preserve immutability (return new datasource instances)
  - Independent caching for specialized datasources
  - Example: `agg_ds = main_ds.with_transform_fn(lambda df: df.groupby('x').sum())`

- **`ChainedTransformer`**: New DataTransformer subclass
  - Applies two transformers sequentially
  - Used internally by `with_transform_fn()` to chain global filters + block transforms
  - Maintains 2-stage caching integrity

#### Sidebar and Navigation Enhancements

- **Collapsible Sidebar Feature**: Global controls sidebar with fixed IDs
  - `SidebarConfig` dataclass for sidebar configuration
  - `dbc.Offcanvas` integration for responsive, animated sidebar
  - Fixed string IDs for sidebar blocks (no pattern-matching)
  - Enables cross-section `State()` subscriptions in pattern-matching callbacks
  - Collapse/expand toggle button with state persistence
  - Works standalone or combined with navigation
  - Unified sidebar+navigation in single Offcanvas panel
  - Theme-aware styling with `--bs-offcanvas-bg` and `--bs-offcanvas-color`

- **Bootstrap Native Components**: Theme integration improvements
  - Replaced `dcc.Dropdown` with `dbc.Select` in examples
  - Replaced `dcc.Input` with `dbc.Input` in examples
  - Native Bootstrap components automatically adapt to themes
  - Minimal CSS overrides for Offcanvas panel controls

#### Other Additions

- **DataBuilder class**: Semantic replacement for PreProcessor
  - Method `build(params)` combines loading and processing
  - Clearer responsibility: "build complete dataset"
  - Used by composition, not inheritance

- **DataTransformer class**: Semantic evolution of DataFilter
  - Broader contract: filter + aggregate + reshape + any df→df transformation
  - Method `transform(data, params)` for data transformations
  - Enables aggregation, pivot, melt operations
  - DataFilter kept as deprecated alias

- **TypedChartBlock.update_from_controls()**: Override for block-centric callback support
  - Enables embedded controls to trigger chart updates
  - Passes `control_values` dict directly to `_update_chart()`

- **DashboardPage._preload_all_section_blocks()**: Pre-register navigation callbacks
  - Loads all section blocks before `app.run()` to satisfy Dash lifecycle

- **Enhanced Logging**: Detailed DEBUG logging for callback registration and execution
  - Shows control value extraction, parameter resolution, callback triggering

### Changed

- **BaseBlock ID Generation**: Add `is_sidebar_block` attribute
  - Sidebar blocks use fixed string IDs (e.g., `"block_id-component"`)
  - Navigation blocks continue using pattern-matching dict IDs
  - Resolves Dash limitation where `State({"section": 0, ...})` cannot be resolved from other sections

- **BaseDataSource**: Now fully concrete (no abstract methods)
  - Constructor takes `data_builder` and `data_transformer` instances
  - Pipeline: Build → Transform (was: Load → Preprocess → Filter)
  - Method: `get_processed_data()` runs 2-stage pipeline
  - New methods: `with_builder()`, `with_transform()` for immutable derivation

- **TypedChartBlock**: Simplified state management
  - Removed complex state registration overrides
  - Now uses BaseBlock's automatic registration (same pattern as other blocks)
  - Added `transform_fn` parameter for block-level transformations

- **All Concrete DataSources**: Updated to use DataBuilder pattern
  - `CsvDataSource`: Uses `CsvDataBuilder` internally
  - `ParquetDataSource`: Uses `ParquetDataBuilder` internally
  - `SqlDataSource`: Uses `SqlDataBuilder` internally
  - All follow composition pattern (builder + transformer)

- **core/__init__.py**: Updated exports
  - Exports: `DataBuilder` (was: `PreProcessor`)
  - Exports: `DataTransformer` (was: `DataFilter`)
  - Still exports: `DataProcessingContext`

### Removed

- **Abstract methods from BaseDataSource**:
  - `_load_raw_data()` - replaced by DataBuilder pattern
  - `get_kpis()` - replaced by MetricsBlock
  - `get_filter_options()` - moved to application code
  - `get_summary()` - moved to application code

### Fixed

- **TypedChartBlock Interactive Controls**: Fixed embedded controls not triggering callbacks
  - Root cause: `BaseBlock.update_from_controls()` returned `None` for blocks with empty `subscribes` dict
  - Solution: Added `update_from_controls()` override in `TypedChartBlock`
  - Result: Interactive controls in preset blocks now work correctly

- **Navigation Link Visibility**: Fixed navigation titles being invisible
  - Root cause: Bootstrap CSS variable precedence
  - Solution: Scoped CSS variable overrides + callback style updates
  - Result: Navigation links properly display with theme colors

- **Pattern-Matching Callback Registration**: Fixed dict key order
  - Root cause: Dash requires exact dict structure match including key order
  - Solution: Consistent `{"section": N, "type": "..."}` order everywhere
  - Result: Pattern-matching callbacks now match HTML component IDs

- **Scatter Plot NaN Handling**: Added automatic NaN filtering in `plot_scatter()`
  - Result: Scatter plots no longer crash on missing values

- **Navigation Lazy-Loading**: Fixed callback registration for lazy-loaded sections
  - Root cause: Dash requires all callbacks registered before `app.run()`
  - Solution: Pre-load all section blocks during `register_callbacks()` phase
  - Result: Interactive controls work in all navigation sections

- **Sidebar Controls Theming**: Fixed controls appearing with wrong theme
  - Solution: Use `dbc.Select` and `dbc.Input` instead of `dcc` components
  - Added minimal CSS for Offcanvas panel controls
  - Result: Controls automatically adapt to dark/light themes

### Benefits

- **Simpler Architecture**: 2 stages instead of 3
- **Semantic Clarity**: "Build" clearly means "construct complete dataset", "Transform" means "any df→df"
- **No Subclassing**: BaseDataSource is concrete, use composition
- **Block-Based Metrics**: Metrics calculated in blocks, not datasources
- **Block-Level Transformations**: Each block can transform data independently via `transform_fn`
- **Better Performance**: Staged caching + independent caching for transformed datasources
- **Working Interactive Controls**: TypedChartBlock embedded controls fully functional
- **Proper Navigation**: Multi-section dashboards with working callbacks in all sections
- **Theme Integration**: Native Bootstrap components for automatic theme support

### Technical Details

**New Pipeline Flow:**
```
Build Stage (cached by build params)
  ↓
Transform Stage (cached by transform params)
  ↓
Block Transform (optional, via transform_fn)
```

**Cache Strategy:**
- Stage 1 (Build): Cached by build params only
- Stage 2 (Transform): Cached by transform params only
- Block Transform: Independent cache per specialized datasource

Changing filter params only triggers Stage 2, reusing cached build results.

**Decision Cache:**
- `data_pipeline_architecture`: Chose 2-stage over 3-stage for simplicity (build combines load+process)
- `transformer_naming`: Chose DataTransformer over DataFilter for broader semantic contract (supports aggregation)
- `block_transforms`: Chose `transform_fn` + `with_transform()` pattern for block-specific transformations without plot function proliferation
- `theming_components`: Chose `dbc.Select`/`dbc.Input` over `dcc` components for native Bootstrap theme support

## [0.14.0] - 2025-10-08

### Changed
- Refactored `InteractiveChartBlock` and `ControlPanelBlock` to delay state interaction setup
- Updated `DASHBOARD_LEGO_GUIDE.md` to align with code changes

### Fixed
- Fixed `InteractiveChartBlock` not handling positional arguments from `StateManager`
- Fixed data filtering in `02_interactive_dashboard.py` example

## [0.13.0] - 2025-10-07

### Added
- **Theme-Aware Styling System**
  - Integration of theme configuration into `BaseBlock`
  - Automatic styling based on user-defined themes
  - New control panel styles and layouts
  - Sample datasets for examples

### Changed
- Enhanced responsiveness and visual consistency across components

## [0.12.0] - 2025-10-06

### Fixed
- Corrected syntax in `_normalize_subscribes_to` method signature

## [0.11.2] - 2025-10-05

### Added
- **Multi-State Subscriptions Support**
  - `BaseBlock` accepts both single state IDs and lists for `subscribes_to`
  - New `_normalize_subscribes_to` method
  - Enhanced `StateManager` for multi-state subscriptions
  - Integration tests for multi-state behavior

## [0.11.0] - 2025-10-02

### Added
- **Enhanced Output and Error Management**
  - `allow_duplicate_output` parameter in blocks
  - Comprehensive error handling for Dash callbacks
  - Duplicate output validation and detailed logging
  - `_get_fallback_output` method for safe error recovery

### Changed
- Updated styles to use camelCase for CSS properties
- Enhanced documentation structure

### Fixed
- Documentation paths for src-layout structure
- API documentation namespace

## [0.10.0] - 2025-10-01

### Added
- **Navigation Panel System**
  - `NavigationConfig` and `NavigationSection` classes
  - Lazy loading of sections with factory functions
  - Fixed sidebar navigation with dynamic width
  - Section caching
  - Font Awesome icons support
  - Example: `examples/08_navigation_dashboard.py`

### Changed
- Enhanced `DashboardPage` to support navigation mode
- Improved visual styling with custom CSS

## [0.9.2] - 2025-10-01

### Changed
- **BREAKING CHANGE**: Restructured to src-layout architecture
  - All modules moved to `src/dashboard_lego/`
  - All imports require `dashboard_lego.*` prefix

### Fixed
- Package installation issue
- Import formatting warnings

### Added
- PyPI publish workflow
- `__all__` export in `__init__.py`

## [0.9.0] - 2025-10-01

### Added
- Initial release of Dashboard Lego library
- Core components: StaticChartBlock, InteractiveChartBlock, KPIBlock, TextBlock
- State management system
- Data sources: CSV, Parquet, SQL
- EDA and ML presets
- Layout presets
- Comprehensive testing suite
- Documentation and examples
- MIT license

---

## Change Types

- **Added** - for new features
- **Changed** - for changes in existing functionality
- **Deprecated** - for soon-to-be removed features
- **Removed** - for removed features
- **Fixed** - for bug fixes
- **Security** - for vulnerability fixes
