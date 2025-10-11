.. _guide-contracts:

Contracts and Guarantees
========================

System contracts, lifecycle guarantees, and behavior specifications.

.. contents::
   :local:
   :depth: 2

Data Source Lifecycle (v0.15)
------------------------------

**Contract:**

.. code-block:: text

   initialization → pipeline → data access
        ↓              ↓            ↓
   __init__()    get_processed_data()
                 (2 stages)

**Pipeline Stages:**

.. code-block:: text

   get_processed_data(params) → classify → build → transform → return
                                    ↓        ↓         ↓
                                Context   Cache1    Cache2

**Guarantees:**

1. **Staged Caching:** Each pipeline stage caches independently
2. **Cache Efficiency:** Transform changes don't trigger build stage
3. **Cache Consistency:** Same params → same cached data at each stage
4. **Cache Expiration:** Data refreshes after ``cache_ttl`` seconds
5. **Error Handling:** ``DataLoadError`` raised on load failure
6. **Thread Safety:** Cache operations are thread-safe (diskcache)

**Pre-conditions:**

- ``DataBuilder.build()`` must return ``pd.DataFrame``
- ``DataTransformer.transform()`` must return ``pd.DataFrame``
- Cache directory must be writable (if specified)

**Post-conditions:**

- ``get_processed_data()`` returns filtered DataFrame or empty DataFrame
- All stages are properly cached
- Data is consistent with input parameters

Block Lifecycle
----------------

**Contract:**

.. code-block:: text

   instantiation → registration → layout → callbacks → updates
         ↓              ↓            ↓          ↓          ↓
     __init__()   _register_   layout()    bind_     update
                  state_                  callbacks  methods
                  interactions()

**Guarantees:**

1. **Unique IDs:** Each block has unique ``block_id``
2. **State Registration:** Blocks register before callbacks
3. **Theme Injection:** ``theme_config`` set before ``layout()`` called
4. **Callback Order:** Publishers registered before subscribers
5. **Error Handling:** Update methods never crash app (return fallback)

**Pre-conditions:**

- ``block_id`` is unique across dashboard
- ``datasource`` is valid ``BaseDataSource`` instance
- State IDs referenced in subscriptions exist

**Post-conditions:**

- ``layout()`` returns valid Dash Component (single component, not composite)
- ``output_target()`` returns unique (id, property) tuple
- Updates trigger correctly on state changes

Layout Height Contract (v0.16)
--------------------------------

**Contract:**

.. code-block:: text

   Row (auto height) → Col (content height) → Card (natural size)
         ↓                    ↓                      ↓
   Determined by     Independent sizing      Compact/tight
   tallest child     per block type          no empty space

**Guarantees:**

1. **Content-Driven Heights:** Blocks size naturally to their content
2. **No Fixed Heights:** No hardcoded px values (responsive to content)
3. **No Empty Space:** Cards are compact (especially metrics)
4. **Responsive Widths:** Bootstrap breakpoints (xs, sm, md, lg) preserved
5. **No Scrolling:** Cards expand to show all content

**Design Decision:**

Blocks in the same row MAY have different heights based on content.
This is **industry standard** (Grafana, Tableau, Looker, Metabase).

**Rationale:**

Bootstrap Flexbox ``align-items: stretch`` requires Row with defined height
to make columns equal height. With ``height: auto`` (content-driven),
equal heights require either:

- CSS Grid (breaks responsive breakpoints)
- JavaScript (complexity)
- Fixed heights (empty space in compact blocks)

**We choose content-driven sizing** to preserve Bootstrap responsive behavior
and avoid complexity.

**Pre-conditions:**

- Row has ``className="mb-4"`` for vertical spacing (auto-applied)
- Col has responsive width classes (xs, sm, md, lg) from user or defaults
- Card has ``className="h-100"`` to fill its column (applied by blocks)
- No fixed ``height`` or ``minHeight`` in inline styles

**Post-conditions:**

- Cards are compact (tight fit around content)
- Row height = max(card heights)
- Columns may have different heights (content-driven)
- Responsive breakpoints work correctly

**Example:**

.. code-block:: python

   # Metric (compact ~150px) + Chart (large ~500px) in same row
   metric = SingleMetricBlock(...)  # Compact card, natural height
   chart = TypedChartBlock(...)     # Larger card with graph

   page = DashboardPage(..., blocks=[[metric, chart]])

   # Result:
   # - Row height = 500px (tallest child)
   # - Metric card = 150px (compact, no empty space)
   # - Chart card = 500px (natural graph size)
   # - Both preserve responsive widths (col-md-4, col-md-8, etc.)

State Management Callbacks
---------------------------

**Contract:**

.. code-block:: text

   publisher change → callback trigger → subscribers update
           ↓                  ↓                  ↓
      Input(...)        function(*)        Output(...)

**Guarantees:**

1. **One Callback Per Block:** Each block has exactly one callback
2. **All Inputs Provided:** Callback receives all subscribed state values
3. **Positional Arguments:** State values passed as positional args in registration order
4. **Error Handling:** Failed callbacks return safe fallback values
5. **No Circular Dependencies:** Detected and prevented at compile time

**Pre-conditions:**

- No duplicate output targets (unless ``allow_duplicate=True``)
- All state IDs have publishers
- Callback functions have correct signature

**Post-conditions:**

- UI updates reflect all state changes
- No dangling callbacks
- Error states render safely

Cache Behavior (v0.15)
-----------------------

**Contract:**

.. code-block:: text

   get_processed_data(params) → classify → Stage 1 → Stage 2 → return
                                    ↓          ↓         ↓
                                Context    Cache1    Cache2

**Staged Caching Strategy:**

.. code-block:: python

   # Stage 1: Built Data (cached by build params only)
   cache_key_1 = f"built_{json(build_params)}"

   # Stage 2: Transformed Data (cached by transform params)
   cache_key_2 = f"transformed_{json(transform_params)}"

**Guarantees:**

1. **Key Stability:** Same params → same cache key (sorted JSON) per stage
2. **TTL Enforcement:** Expired entries refreshed automatically
3. **Isolation:** Different params → different cache entries
4. **Persistence:** Disk cache survives app restarts
5. **Stage Independence:** Transform changes don't invalidate build cache
6. **Efficiency:** Only affected stages recompute

**Cache Hit Scenarios:**

+-------------------+-------------+----------------+------------------+------------------+
| Scenario          | Stage 1     | Stage 2        | Performance      | Notes            |
|                   | (Build)     | (Transform)    |                  |                  |
+===================+=============+================+==================+==================+
| First load        | Miss        | Miss           | Full pipeline    | All stages run   |
+-------------------+-------------+----------------+------------------+------------------+
| Same params       | Hit         | Hit            | Instant          | All cached       |
+-------------------+-------------+----------------+------------------+------------------+
| Filter change     | Hit         | Miss           | Fast             | Only retransform |
+-------------------+-------------+----------------+------------------+------------------+
| Build change      | Miss        | Miss           | Full pipeline    | Rebuild needed   |
+-------------------+-------------+----------------+------------------+------------------+

**Pre-conditions:**

- ``DataBuilder.build()`` must be implemented
- ``DataTransformer.transform()`` must be implemented
- Both methods must return ``pd.DataFrame``
- Cache directory exists and is writable (if specified)
- Params are JSON-serializable

**Post-conditions:**

- Cache hit at any stage → no recomputation of that stage
- Cache miss at stage N → stages N, N+1 recompute
- Expired entry → treated as cache miss
- Both data attributes are populated: ``_built_data``, ``_transformed_data``
