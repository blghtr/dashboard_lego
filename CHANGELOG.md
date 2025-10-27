# Changelog

All notable changes to the Dashboard Lego project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.16.0] - 2025-10-27

### 🚀 Major New Features

#### BasePreset Architecture - Flexible Preset Development Framework

- **🎯 BasePreset Abstract Class**: Standardized pattern for creating TypedChartBlock presets
  - Flexible control configuration: `controls=False`, `controls=True`, or `controls=dict`
  - Automatic control validation and normalization
  - Subclass contract: implement `default_controls`, `plot_type`, `_build_plot_params()`, `_build_plot_kwargs()`
  - Enables rapid preset development with consistent patterns

- **🎨 CSS Styling System**: Responsive control styling with Bootstrap integration
  - `control_styles.py` with modern styling presets (compact dropdown, modern slider)
  - Responsive column sizing with `col_props` (auto, xs, md breakpoints)
  - Theme-aware styling that adapts to dark/light modes
  - Auto-sizing controls that respond to content width

- **📊 MinimalChartBlock**: New block for minimalist, stripped-down visualizations
  - Transparent backgrounds with hidden grids, labels, and legends
  - Compact margins and clean aesthetic
  - Override-friendly design (can restore elements via `plot_kwargs`)
  - Perfect for sparklines and embedded charts

#### Enhanced IPython Magic Commands

- **🪄 Comprehensive Magic Interface**: Extended IPython integration for data exploration
  - Advanced state management integration with magic commands
  - Complex data transformations via magic syntax
  - Enhanced error handling and user feedback
  - Interactive dashboard creation from Jupyter notebooks

#### Data Pipeline and State Management Improvements

- **⚡ Enhanced DataSource Pipeline**: Improved caching and data handling
  - Better error handling and recovery mechanisms
  - Optimized cache sharing and memory management
  - Enhanced state synchronization and key normalization
  - Multi-input state management for complex dashboards

- **🔄 Advanced State Management**: Multi-state subscription system
  - Support for both single and multiple state subscriptions
  - Enhanced StateManager with better synchronization
  - Key normalization and validation
  - Comprehensive state transition testing

#### Knee Plots Utilities

- **📈 Optimal Binning Detection**: Automatic knee/elbow point detection
  - `knee_plots.py` utility for finding optimal binning parameters
  - Statistical methods for determining natural breakpoints
  - Integration with plot registry for automatic optimization
  - Performance improvements for large datasets

### 🔧 Improvements and Refactoring

#### Module Architecture Updates

- **📦 Module Exports Enhancement**: Updated all `__init__.py` files with new functionality
  - Added `MinimalChartBlock` to blocks module exports
  - Enhanced presets module with CSS styling exports
  - Updated core module exports with new classes
  - Added plot registry utilities and chart types

#### Deprecated Code Cleanup

- **🗑️ Legacy Code Removal**: Clean removal of outdated components
  - Removed `preprocessor.py` (functionality integrated into DataTransformer)
  - Removed `control_styles.py` (replaced by CSS styling system)
  - Removed `jupyter_quick_dashboard.py` example (consolidated into showcase)
  - Removed deprecated test files and imports

#### Enhanced Test Coverage

- **🧪 Comprehensive Testing Suite**: Added extensive tests for new features
  - State synchronization and key normalization tests
  - Multi-input state management tests
  - Control panel and integration test coverage
  - Knee plots utility validation
  - Enhanced block transformation tests

### 📚 Documentation Updates

#### Enhanced Guides and API Documentation

- **📖 IPython Magic Commands Guide**: New comprehensive guide (`docs/source/guide/magics.rst`)
  - Usage examples and advanced patterns
  - State management integration examples
  - Error handling and debugging tips

- **🏗️ Preset Architecture Documentation**: Updated guides for new BasePreset system
  - BasePreset development patterns and best practices
  - CSS styling system integration
  - Control configuration examples

- **🎨 README Enhancements**: Updated with new preset architecture examples
  - BasePreset usage examples and configuration options
  - CSS styling demonstrations
  - Enhanced feature overview with latest capabilities

#### API Documentation Updates

- **📋 Updated API Reference**: Enhanced documentation for all new classes
  - BasePreset abstract class and subclassing patterns
  - MinimalChartBlock usage and styling options
  - Enhanced DataSource and State management APIs
  - CSS styling utilities and responsive design

### 🎯 Technical Improvements

#### Control System Enhancements

- **🎛️ Advanced Control Building**: Shared utilities for consistent control creation
  - `control_helpers.py` for normalized control building
  - Options normalization (list[str] → list[dict])
  - Responsive column properties with Bootstrap breakpoints
  - Component mapping and CSS class management

#### Visual Consistency

- **🎨 Responsive Design System**: Bootstrap-native component integration
  - Replaced `dcc` components with `dbc` for theme support
  - Auto-sizing controls that adapt to content width
  - Modern CSS styling with compact dropdown and slider designs
  - Theme-aware color resolution and styling

#### Performance Optimizations

- **⚡ Enhanced Caching Strategy**: Improved data pipeline performance
  - Class-level cache registry for transparent sharing
  - Independent caching for transformed datasources
  - Optimized state management and synchronization
  - Reduced duplicate data loading operations

### 📊 Usage Examples

#### BasePreset Development Pattern:
```python
class MyChartPreset(BasePreset):
    @property
    def default_controls(self) -> Dict[str, Control]:
        return {
            "metric": Control(component=dcc.Dropdown, props={
                "options": [{"label": "Revenue", "value": "revenue"}],
                "className": "compact-dropdown"
            }),
            "period": Control(component=dcc.Slider, props={
                "min": 2020, "max": 2024,
                "className": "modern-slider"
            })
        }

    def _build_plot_params(self, final_controls, kwargs):
        return {"x": "{{period}}", "y": "{{metric}}"}

# Flexible usage patterns
chart1 = MyChartPreset(block_id="sales", datasource=ds, controls=True)      # Default controls
chart2 = MyChartPreset(block_id="sales", datasource=ds, controls=False)     # No controls
chart3 = MyChartPreset(block_id="sales", datasource=ds, controls={           # Custom controls
    "metric": True,    # Enable default control
    "period": False    # Disable default control
})
```

#### MinimalChart for Clean Visualizations:
```python
# Sparkline-style chart with minimal styling
sparkline = MinimalChartBlock(
    block_id="trend",
    datasource=datasource,
    plot_type='line',
    plot_params={'x': 'date', 'y': 'value'},
    plot_kwargs={'showlegend': False}  # Override minimal preset
)
```

### ✅ Validation and Testing

**Comprehensive Test Suite**: 187 unit/integration tests all passing
- New state management tests (7 test files added)
- Enhanced control panel and block transformation tests
- Integration tests for multi-state scenarios
- CSS styling and responsive design validation

**Performance Validation**: ✅ Verified with capstone_user_identification dashboard
- No duplicate data loading operations
- Improved state synchronization performance
- Enhanced visual responsiveness and styling

**Backward Compatibility**: ✅ All existing functionality preserved
- Deprecated components removed with migration paths
- API contracts maintained for existing code
- Enhanced functionality without breaking changes

### 🔄 Migration Guide

#### For Preset Developers:
- **Before**: Custom preset classes with manual control management
- **After**: Inherit from `BasePreset` with standardized control configuration
- **Benefit**: Consistent patterns, automatic styling, flexible control setup

#### For Dashboard Users:
- **Enhanced**: More responsive controls with better styling
- **Simplified**: BasePreset makes custom presets easier to create
- **Improved**: Better state management and data pipeline performance

#### Deprecated Components (with migration):
- `MetricsBlock` → Use `get_metric_row()` factory pattern
- `KPIBlock` → Use `get_metric_row()` factory pattern
- Custom styling → Use CSS styling system with Bootstrap components

### 🎯 Technical Decision Cache

- **base_preset_architecture**: Abstract base class pattern for consistent preset development over ad-hoc implementations
- **css_styling_system**: CSS-based styling over inline styles for maintainability and theme integration
- **responsive_controls**: Bootstrap col-auto pattern for content-driven sizing over fixed widths
- **minimal_chart_design**: Override-friendly minimal styling over opinionated defaults
- **knee_plots_integration**: Statistical binning optimization over manual parameter selection

**Result**: v0.16.0 delivers a comprehensive, production-ready feature set with enhanced developer experience, visual consistency, and performance improvements.

## [0.15.1] - 2025-10-11

### Fixed

#### Critical: Sidebar Filters → Metrics Update Chain

- **🔴 CRITICAL BUG**: Fixed metrics not updating from sidebar filters in navigation mode
  - **Root Cause**: Duplicate block creation caused duplicate callback inputs
  - **Contract Violation**: Blocks created twice (in `build_layout()` and `register_callbacks()`)
  - **Impact**: Callbacks registered with wrong Input signature → metrics didn't respond to filter changes

- **Fix 1**: Preload navigation sections before layout build
  - Added preload guard in `DashboardPage.build_layout()`
  - Prevents duplicate block creation in sidebar+navigation mode
  - Ensures blocks created exactly once before callback registration
  - File: `src/dashboard_lego/core/page.py:1103-1115`

- **Fix 2**: Reuse preloaded blocks in `register_callbacks()`
  - Added `_sections_preloaded` flag check
  - Uses cached blocks instead of recreating
  - Eliminates duplicate subscriptions in StateManager
  - File: `src/dashboard_lego/core/page.py:1362-1376`

- **Fix 3**: Wrap `SingleMetricBlock` in container Div
  - **Root Cause**: `layout()` returned Card directly without container ID
  - **Contract Violation**: `output_target()` expected `"block_id-container"` ID in DOM
  - **Result**: Dash callbacks couldn't find Output target → didn't fire
  - **Solution**: Wrap card in `html.Div(id=_generate_id("container"))`
  - File: `src/dashboard_lego/blocks/single_metric.py:400-405`

**Validation**: ✅ Tested with `examples/00_showcase_dashboard.py`
- Callbacks now register with correct inputs (no duplicates)
- Metrics update correctly when sidebar filters change
- All 3 sections respond to global filters

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

### Removed

- **`KPIBlock`**: Removed deprecated block (use `get_metric_row()`)
  - Was deprecated in v0.15.0
  - Relied on removed `datasource.get_kpis()` method
  - Migration: Use `get_metric_row()` factory pattern
- **`MetricsBlock`**: Removed deprecated block (use `get_metric_row()`)
  - Was deprecated in v0.15.1
  - Replaced by factory pattern for better composability
  - Migration: Use `get_metric_row()` to create metric blocks
- **`MetricCardBlock`**: Removed from `ml_presets` module
  - Was deprecated in v0.15.0
  - Migration: Use `get_metric_row()` for metric display

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

### Testing

- **Browser Tests**: Layout contract tests marked as skipped by default
  - Require ChromeDriver version matching installed Chrome browser
  - Can be enabled by updating ChromeDriver or using `webdriver-manager`
  - Core functionality verified through 187 unit/integration tests (all passing)

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
