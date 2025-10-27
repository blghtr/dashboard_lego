.. _guide-overview:

System Overview
===============

Architecture Hierarchy
----------------------

.. code-block:: text

   dashboard_lego/
   ├── core/                  # Core orchestration and state management
   │   ├── page.py           # DashboardPage: main orchestrator
   │   ├── state.py          # StateManager: publisher/subscriber coordination
   │   ├── datasource.py     # DataSource: concrete data interface (v0.15)
   │   ├── data_builder.py   # DataBuilder: data construction (v0.15)
   │   ├── data_transformer.py # DataTransformer: data transformation (v0.15)
   │   ├── theme.py          # ThemeConfig: styling system
   │   └── datasources/      # Concrete data source implementations
   │       ├── csv_source.py
   │       ├── parquet_source.py
   │       └── sql_source.py
   ├── blocks/               # Visual components
   │   ├── base.py          # BaseBlock: abstract block interface
   │   ├── typed_chart.py   # TypedChartBlock: unified chart block (v0.15)
   │   ├── metrics.py       # MetricsBlock: declarative metrics (v0.15)
   │   └── text.py          # TextBlock: markdown/HTML rendering
   ├── presets/             # Pre-built blocks and layouts
   │   ├── eda_presets.py   # EDA visualization blocks
   │   ├── ml_presets.py    # Machine learning visualization blocks
   │   ├── layouts.py       # Layout composition functions
   │   └── control_styles.py # UI styling utilities
   └── utils/               # Utilities
       ├── exceptions.py    # Custom exception hierarchy
       ├── logger.py        # Logging configuration
       └── formatting.py    # Data formatting utilities

Module Dependency Graph
-----------------------

.. code-block:: text

   DashboardPage (orchestrator)
       ├─> StateManager (state coordination)
       ├─> ThemeConfig (styling)
       ├─> BaseBlock (components)
       │   ├─> DataSource (data)
       │   └─> StateManager (registration)
       └─> Navigation (multi-section pages)

   BaseBlock (abstract)
       ├─> TypedChartBlock (replaces Static/Interactive)
       ├─> ControlPanelBlock
       ├─> MetricsBlock (replaces KPIBlock pattern)
       └─> TextBlock

   DataSource (concrete, uses composition)
       ├─> DataBuilder (build stage)
       └─> DataTransformer (transform stage)

   Presets (convenience)
       ├─> EDA Presets (extends TypedChartBlock)
       └─> ML Presets (extends TypedChartBlock)

Core Design Principles
----------------------

1. **Modularity**: Each block is independent and reusable
2. **Publisher/Subscriber Pattern**: Loose coupling through state management
3. **Caching**: Transparent disk-based caching at datasource level
4. **Type Safety**: Full type hints for IDE and static analysis support
5. **Theme System**: Consistent styling across all components
6. **Block-Centric Callbacks**: One callback per block for performance
