"""
Quick Dashboard Factory - Rapid dashboard assembly utility.

Provides quick_dashboard() factory for instant dashboard creation with
minimal code. Works in Jupyter notebooks, Python scripts, and anywhere
Dash runs. Supports two modes: simple (DataFrame + card specs) and
advanced (pre-built blocks).

:hierarchy: [Utils | QuickDashboard]
:relates-to:
 - motivated_by: "Users need rapid prototyping without boilerplate:
                  instant visualization in 3-5 lines for exploration"
 - implements: "quick_dashboard() factory with smart layout algorithm"
 - uses: ["BaseDataSource", "DashboardPage", "get_metric_row",
          "TypedChartBlock"]

:contract:
 - pre: "Valid DataFrame OR list of blocks (mutually exclusive),
         1-4 cards/blocks"
 - post: "Returns ready-to-run Dash app"
 - invariant: "No disk writes, no external state mutations,
               deterministic layout"

:complexity: 7
:decision_cache: "Smart layout over naive grid: metrics grouped via
                  get_metric_row (single row), charts max 2 per row
                  for notebook-friendly vertical scrolling"
"""

from typing import Any, Dict, List, Optional, Union

import dash
import dash_bootstrap_components as dbc
import pandas as pd

from dashboard_lego.blocks.base import BaseBlock
from dashboard_lego.blocks.metrics_factory import get_metric_row
from dashboard_lego.blocks.single_metric import SingleMetricBlock
from dashboard_lego.blocks.text import TextBlock
from dashboard_lego.blocks.typed_chart import TypedChartBlock
from dashboard_lego.core.data_builder import DataBuilder
from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.core.page import DashboardPage
from dashboard_lego.core.theme import ThemeConfig
from dashboard_lego.presets.layouts import one_column, two_column_6_6
from dashboard_lego.utils.logger import get_logger

logger = get_logger(__name__)


# LLM:METADATA
# :hierarchy: [Utils | QuickDashboard | InMemoryDataBuilder]
# :relates-to:
#  - motivated_by: "In-memory DataFrame wrapper for no-disk-I/O requirement:
#                   users pass DataFrame directly, no file loading,
#                   satisfies invariant of zero disk writes"
#  - implements: "DataBuilder subclass wrapping DataFrame in memory"
#  - uses: ["DataBuilder: base class for build protocol"]
# :contract:
#  - pre: "df is valid non-empty pandas DataFrame at initialization"
#  - post: "build() returns same DataFrame every call (cached in memory)"
#  - invariant: "no disk I/O, deterministic"
# :complexity: 2
# :decision_cache: "DataFrame stored at init over build-time loading:
#                   avoids repeated reads, guarantees no disk I/O"
# LLM:END


class InMemoryDataBuilder(DataBuilder):
    """
    In-memory DataFrame wrapper for Jupyter quick dashboards.

    Wraps a DataFrame directly without any file I/O or disk caching.
    Satisfies the invariant: no disk writes during runtime.

    Args:
        df: pandas DataFrame to wrap

    Example:
        >>> df = pd.read_csv("data.csv")
        >>> builder = InMemoryDataBuilder(df)
        >>> datasource = BaseDataSource(data_builder=builder, cache_ttl=0)
    """

    def __init__(self, df: pd.DataFrame, **kwargs: Any):
        """
        Initialize with DataFrame.

        Args:
            df: DataFrame to wrap
        """
        super().__init__(**kwargs)
        if df is None or not isinstance(df, pd.DataFrame):
            raise ValueError("df must be a valid pandas DataFrame")
        if df.empty:
            logger.warning("[InMemoryDataBuilder] Empty DataFrame provided")

        self._df = df.copy()  # Copy to avoid external mutations
        logger.debug(
            f"[Utils|JupyterFactory|InMemoryDataBuilder] Initialized | "
            f"rows={len(df)} | cols={len(df.columns)}"
        )

    def build(self, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Return the wrapped DataFrame.

        Args:
            params: Ignored (no build-time parameters needed)

        Returns:
            The wrapped DataFrame
        """
        logger.debug("[Utils|JupyterFactory|InMemoryDataBuilder] Returning DataFrame")
        return self._df


# LLM:METADATA
# :hierarchy: [Utils | JupyterFactory | _detect_jupyter]
# :relates-to:
#  - motivated_by: "JupyterDash requires detection of Jupyter environment to enable inline display mode, avoids ImportError in non-Jupyter Python scripts [jupyter-detection]"
#  - implements: "Helper function that checks for IPython kernel presence [_detect_jupyter]"
#  - uses: ["get_ipython: IPython builtin for kernel detection"]
# :contract:
#  - pre: "None (no parameters)"
#  - post: "returns True if in Jupyter/IPython kernel, False otherwise"
#  - invariant: "deterministic (same environment always returns same result), no side effects"
# :complexity: 1
# :decision_cache: "get_ipython() over sys.modules check: more reliable for detecting interactive kernel [decision-jupyter-detect-001]"
# LLM:END


def _detect_jupyter() -> bool:
    """
    Detect if running in Jupyter/IPython environment.

    Returns:
        True if in Jupyter kernel, False otherwise
    """
    try:
        get_ipython  # type: ignore
        return True
    except NameError:
        return False


# LLM:METADATA
# :hierarchy: [Utils | JupyterFactory | _get_theme_url_and_config]
# :relates-to:
#  - motivated_by: "Theme names need mapping to Bootstrap CDN URLs and ThemeConfig objects for consistent styling across simple/advanced modes [theme-mapping]"
#  - implements: "Helper that maps theme name string to tuple of (URL, ThemeConfig) [_get_theme_url_and_config]"
#  - uses: ["dbc.themes: Bootstrap CDN URLs", "ThemeConfig: theme configuration objects"]
# :contract:
#  - pre: "theme_name is string (supported: light, dark, lux, cyborg, bootstrap, etc.)"
#  - post: "returns tuple (theme_url: str, theme_config: ThemeConfig)"
#  - invariant: "deterministic mapping, unsupported names default to lux"
# :complexity: 2
# :decision_cache: "Centralized theme mapping over inline logic: reusable, single source of truth [decision-theme-map-001]"
# LLM:END


def _get_theme_url_and_config(theme_name: str) -> tuple:
    """
    Map theme name to Bootstrap URL and ThemeConfig.

    Args:
        theme_name: Theme name (lux, dark, light, cyborg, bootstrap, etc.)

    Returns:
        Tuple of (theme_url, theme_config)
    """
    theme_map = {
        "light": (dbc.themes.BOOTSTRAP, ThemeConfig.light_theme()),
        "dark": (dbc.themes.DARKLY, ThemeConfig.dark_theme()),
        "lux": (dbc.themes.LUX, ThemeConfig.from_dbc_theme(dbc.themes.LUX)),
        "cyborg": (dbc.themes.CYBORG, ThemeConfig.from_dbc_theme(dbc.themes.CYBORG)),
        "bootstrap": (
            dbc.themes.BOOTSTRAP,
            ThemeConfig.from_dbc_theme(dbc.themes.BOOTSTRAP),
        ),
        "cerulean": (
            dbc.themes.CERULEAN,
            ThemeConfig.from_dbc_theme(dbc.themes.CERULEAN),
        ),
        "cosmo": (dbc.themes.COSMO, ThemeConfig.from_dbc_theme(dbc.themes.COSMO)),
        "flatly": (dbc.themes.FLATLY, ThemeConfig.from_dbc_theme(dbc.themes.FLATLY)),
        "journal": (dbc.themes.JOURNAL, ThemeConfig.from_dbc_theme(dbc.themes.JOURNAL)),
        "litera": (dbc.themes.LITERA, ThemeConfig.from_dbc_theme(dbc.themes.LITERA)),
        "lumen": (dbc.themes.LUMEN, ThemeConfig.from_dbc_theme(dbc.themes.LUMEN)),
        "minty": (dbc.themes.MINTY, ThemeConfig.from_dbc_theme(dbc.themes.MINTY)),
        "pulse": (dbc.themes.PULSE, ThemeConfig.from_dbc_theme(dbc.themes.PULSE)),
        "sandstone": (
            dbc.themes.SANDSTONE,
            ThemeConfig.from_dbc_theme(dbc.themes.SANDSTONE),
        ),
        "simplex": (dbc.themes.SIMPLEX, ThemeConfig.from_dbc_theme(dbc.themes.SIMPLEX)),
        "sketchy": (dbc.themes.SKETCHY, ThemeConfig.from_dbc_theme(dbc.themes.SKETCHY)),
        "slate": (dbc.themes.SLATE, ThemeConfig.from_dbc_theme(dbc.themes.SLATE)),
        "solar": (dbc.themes.SOLAR, ThemeConfig.from_dbc_theme(dbc.themes.SOLAR)),
        "spacelab": (
            dbc.themes.SPACELAB,
            ThemeConfig.from_dbc_theme(dbc.themes.SPACELAB),
        ),
        "superhero": (
            dbc.themes.SUPERHERO,
            ThemeConfig.from_dbc_theme(dbc.themes.SUPERHERO),
        ),
        "united": (dbc.themes.UNITED, ThemeConfig.from_dbc_theme(dbc.themes.UNITED)),
        "yeti": (dbc.themes.YETI, ThemeConfig.from_dbc_theme(dbc.themes.YETI)),
    }

    if theme_name.lower() not in theme_map:
        logger.warning(
            f"[Utils|JupyterFactory] Unknown theme '{theme_name}', defaulting to 'lux'"
        )
        theme_name = "lux"

    return theme_map[theme_name.lower()]


# LLM:METADATA
# :hierarchy: [Utils | JupyterFactory | _create_block_from_spec]
# :relates-to:
#  - motivated_by: "Simple mode card specs need conversion to BaseBlock instances for DashboardPage layout API, factory pattern eliminates boilerplate [card-factory]"
#  - implements: "Factory function that creates SingleMetricBlock, TypedChartBlock, or TextBlock from dict spec [_create_block_from_spec]"
#  - uses: ["SingleMetricBlock, TypedChartBlock, TextBlock: block constructors", "BaseDataSource: data pipeline"]
# :contract:
#  - pre: "card_spec is dict with 'type' key and type-specific required fields (column/agg/title for metric, plot_type/x/y/title for chart, content for text)"
#  - post: "returns BaseBlock instance configured from spec"
#  - invariant: "deterministic (same spec + datasource → same block configuration)"
# :complexity: 3
# :decision_cache: "Type-based dispatch over subclass registry: simple, explicit, only 3 types needed [decision-card-factory-001]"
# LLM:END


def _create_block_from_spec(
    card_spec: Dict[str, Any],
    datasource: BaseDataSource,
    block_id: str,
) -> BaseBlock:
    """
    Create block from card specification.

    Args:
        card_spec: Card specification dict
        datasource: DataSource instance
        block_id: Unique block identifier

    Returns:
        BaseBlock instance

    Raises:
        ValueError: If card type unknown or required fields missing
    """
    card_type = card_spec.get("type")

    if card_type == "metric":
        # Validate required fields
        required = {"column", "agg", "title"}
        if not required.issubset(card_spec.keys()):
            missing = required - card_spec.keys()
            raise ValueError(
                f"Metric card missing required fields: {missing}. "
                f"Required: column, agg, title"
            )

        # Build metric spec
        metric_spec = {
            "column": card_spec["column"],
            "agg": card_spec["agg"],
            "title": card_spec["title"],
            "color": card_spec.get("color", "primary"),
            "dtype": card_spec.get("dtype"),
        }

        logger.debug(
            f"[Utils|JupyterFactory] Creating metric block | spec={metric_spec}"
        )

        return SingleMetricBlock(
            block_id=block_id,
            datasource=datasource,
            metric_spec=metric_spec,
        )

    elif card_type == "chart":
        # Validate required fields
        required = {"plot_type", "x", "y", "title"}
        if not required.issubset(card_spec.keys()):
            missing = required - card_spec.keys()
            raise ValueError(
                f"Chart card missing required fields: {missing}. "
                f"Required: plot_type, x, y, title"
            )

        # Build plot params
        plot_params = {"x": card_spec["x"], "y": card_spec["y"]}
        if "color" in card_spec:
            plot_params["color"] = card_spec["color"]
        if "size" in card_spec:
            plot_params["size"] = card_spec["size"]

        logger.debug(
            f"[Utils|JupyterFactory] Creating chart block | "
            f"plot_type={card_spec['plot_type']} | params={plot_params}"
        )

        return TypedChartBlock(
            block_id=block_id,
            datasource=datasource,
            plot_type=card_spec["plot_type"],
            plot_params=plot_params,
            plot_kwargs={"title": card_spec["title"]},
            title=card_spec["title"],
        )

    elif card_type == "text":
        # Validate required fields
        if "content" not in card_spec:
            raise ValueError("Text card missing required field: content")

        logger.debug("[Utils|JupyterFactory] Creating text block")

        # TextBlock requires content_generator function, not direct content
        content_text = card_spec["content"]
        return TextBlock(
            block_id=block_id,
            datasource=datasource,
            subscribes_to=[],  # No subscriptions for static text
            content_generator=lambda df: content_text,
        )

    else:
        raise ValueError(
            f"Unknown card type: '{card_type}'. "
            f"Supported: 'metric', 'chart', 'text'"
        )


# LLM:METADATA
# :hierarchy: [Utils | QuickDashboard | _smart_layout]
# :relates-to:
#  - motivated_by: "Notebook-friendly layout: metrics compact (all in one row
#                   via get_metric_row), charts large (max 2 per row),
#                   vertical scroll friendly"
#  - implements: "Smart layout algorithm separating metrics from charts"
#  - uses: ["get_metric_row: metrics factory", "two_column_6_6: chart pairs"]
# :contract:
#  - pre: "card_specs is list of card dicts, datasource valid"
#  - post: "returns layout rows: metrics_row first (if any), then charts"
#  - invariant: "deterministic, metrics always grouped in first row"
# :complexity: 4
# :decision_cache: "get_metric_row integration over individual metrics:
#                   optimized layout, single compact row for all metrics,
#                   consistent with showcase pattern"
# LLM:END


def _smart_layout(card_specs: List[Dict[str, Any]], datasource: BaseDataSource) -> List:
    """
    Create notebook-friendly layout with smart metric grouping.

    Algorithm:
    1. Separate metrics from non-metrics (charts, text)
    2. If metrics exist: create metrics_row via get_metric_row() (first row)
    3. Layout non-metrics: max 2 per row for readability
    4. Combine rows: [metrics_row, ...non_metric_rows]

    Args:
        card_specs: List of card specification dicts
        datasource: DataSource for metric blocks

    Returns:
        Layout rows for DashboardPage

    Raises:
        ValueError: If total cards > 4

    Example layouts:
        2M + 2C → [metrics_row(2), [chart1_50, chart2_50]]
        1M + 3C → [metrics_row(1), [chart1_full], [chart2_50, chart3_50]]
        0M + 3C → [[chart1_full], [chart2_50, chart3_50]]
    """
    if len(card_specs) > 4:
        raise ValueError(
            f"Too many cards: {len(card_specs)}. Maximum 4 for quick_dashboard()"
        )

    # Separate metrics from non-metrics
    metric_specs = []
    non_metric_specs = []

    for idx, spec in enumerate(card_specs):
        if spec["type"] == "metric":
            metric_specs.append((idx, spec))
        else:
            non_metric_specs.append((idx, spec))

    rows = []

    # Create metrics row if any (using get_metric_row factory)
    if metric_specs:
        # Validate metric specs
        for idx, spec in metric_specs:
            required = {"column", "agg", "title"}
            if not required.issubset(spec.keys()):
                missing = required - spec.keys()
                raise ValueError(
                    f"Invalid card spec at index {idx}: Metric card missing "
                    f"required fields: {missing}. Required: column, agg, title"
                )

        metrics_spec_dict = {
            f"metric_{idx}": {
                "column": spec["column"],
                "agg": spec["agg"],
                "title": spec["title"],
                "color": spec.get("color", "primary"),
                "dtype": spec.get("dtype"),
            }
            for idx, spec in metric_specs
        }

        logger.debug(
            f"[Utils|QuickDashboard] Creating metrics row | count={len(metric_specs)}"
        )

        metric_blocks, metric_row_opts = get_metric_row(
            metrics_spec=metrics_spec_dict,
            datasource=datasource,
            block_id_prefix="quick_metric",
        )

        # Build metrics row with equal widths
        metric_width = 12 // len(metric_blocks)
        metric_cells = [(block, {"md": metric_width}) for block in metric_blocks]
        rows.append((metric_cells, metric_row_opts))

    # Create non-metric blocks
    non_metric_blocks = []
    for idx, spec in non_metric_specs:
        block_id = f"quick_card_{idx}"
        block = _create_block_from_spec(spec, datasource, block_id)
        non_metric_blocks.append(block)

    # Layout non-metrics (max 2 per row for notebook readability)
    if len(non_metric_blocks) == 1:
        rows.extend(one_column(non_metric_blocks))
    elif len(non_metric_blocks) == 2:
        rows.extend(two_column_6_6(non_metric_blocks[0], non_metric_blocks[1]))
    elif len(non_metric_blocks) == 3:
        # First full width, then 2 in 50/50
        rows.extend(one_column([non_metric_blocks[0]]))
        rows.extend(two_column_6_6(non_metric_blocks[1], non_metric_blocks[2]))
    elif len(non_metric_blocks) == 4:
        # Two rows of 50/50
        rows.extend(two_column_6_6(non_metric_blocks[0], non_metric_blocks[1]))
        rows.extend(two_column_6_6(non_metric_blocks[2], non_metric_blocks[3]))

    logger.debug(
        f"[Utils|QuickDashboard] Smart layout created | "
        f"metrics={len(metric_specs)} | non_metrics={len(non_metric_specs)} | "
        f"rows={len(rows)}"
    )

    return rows


# LLM:METADATA
# :hierarchy: [Utils | JupyterFactory | quick_dashboard]
# :relates-to:
#  - motivated_by: "Jupyter users need rapid dashboard prototyping without boilerplate: instant visualization in 3-5 lines of code, eliminates need for DataBuilder/DashboardPage boilerplate for 90% of use cases [Feature: JupyterQuickStart, jupyter-quick-001]"
#  - implements: "Factory function accepting DataFrame + card specs OR pre-built blocks, returns ready-to-run app with optional JupyterDash inline display support [quick_dashboard]"
#  - uses: [
#      "InMemoryDataBuilder: wraps DataFrame for zero-disk-I/O data pipeline",
#      "BaseDataSource: in-memory data pipeline (cache_ttl=0 for no disk writes)",
#      "DashboardPage: layout assembly and theme integration",
#      "SingleMetricBlock, TypedChartBlock, TextBlock: card rendering from specs",
#      "_create_block_from_spec: card spec to block conversion factory",
#      "_select_layout: automatic grid selection (one_column, two_column_6_6, three_column_4_4_4, 2x2) based on 1-4 card count",
#      "_get_theme_url_and_config: theme name to Bootstrap URL + ThemeConfig mapper",
#      "_detect_jupyter: Jupyter environment detection for JupyterDash usage",
#      "dash.Dash or jupyter_dash.JupyterDash: app classes (optional dependency graceful fallback)"
#  ]
# :contract:
#  - pre: "df is valid non-empty DataFrame OR blocks is list of 1-4 BaseBlock instances (mutually exclusive, exactly one must be provided), valid card spec dicts with required fields (type='metric' requires column/agg/title, type='chart' requires plot_type/x/y/title, type='text' requires content), theme name valid (any Bootstrap theme name or lux/dark/light/cyborg), title is non-empty string"
#  - post: "returns Dash or JupyterDash app object with layout built, callbacks registered, theme applied, ready for .run_server() call (JupyterDash supports mode='inline' or mode='external', standard Dash opens new browser tab), no disk state created (cache_ttl=0, no temp files)"
#  - invariant: "no disk writes (no temp files, no cache files via cache_ttl=0), no external state mutations, deterministic layout from input specs (same df/cards/blocks/theme → same layout structure), pure function (no side effects except logger calls)"
# :complexity: 6
# :decision_cache: "Two-tier API (simple + advanced) over single complex API: simple mode for 90% use case (quick metrics/charts from DataFrame with 3-5 lines), advanced mode for full control (pre-built custom blocks), avoids 15+ parameter explosion and cognitive overload [decision-jupyter-api-001] | JupyterDash optional dependency over required: graceful fallback to standard Dash maintains compatibility, users without jupyter-dash still get functionality (opens new tab instead of inline), no ImportError failures [decision-jupyter-dep-002] | cache_ttl=0 over default caching: satisfies invariant of zero disk writes, Jupyter use case is interactive exploration with small data in memory, no need for disk cache [decision-jupyter-cache-001]"
# LLM:END


def quick_dashboard(
    df: Optional[pd.DataFrame] = None,
    cards: Optional[List[Dict[str, Any]]] = None,
    blocks: Optional[List[BaseBlock]] = None,
    title: str = "Quick Dashboard",
    theme: str = "lux",
) -> Union[dash.Dash, Any]:
    """
    Create a quick dashboard for Jupyter notebooks and Python scripts.

    Supports two modes: simple (DataFrame + card specs) and advanced (pre-built blocks).
    Returns a ready-to-run Dash app.

    Simple mode example (DataFrame + card specs):
        >>> import pandas as pd
        >>> from dashboard_lego.utils import quick_dashboard
        >>>
        >>> df = pd.DataFrame({
        ...     'Product': ['A', 'B', 'C'],
        ...     'Sales': [100, 200, 150],
        ...     'Revenue': [1000, 2000, 1500]
        ... })
        >>>
        >>> app = quick_dashboard(
        ...     df=df,
        ...     cards=[
        ...         {"type": "metric", "column": "Revenue", "agg": "sum",
        ...          "title": "Total Revenue", "color": "success"},
        ...         {"type": "chart", "plot_type": "bar", "x": "Product",
        ...          "y": "Sales", "title": "Sales by Product"}
        ...     ],
        ...     title="Sales Dashboard"
        ... )
        >>> app.run(debug=True)  # Opens in browser tab

    Advanced mode example (pre-built blocks):
        >>> from dashboard_lego.blocks import SingleMetricBlock, TypedChartBlock
        >>> from dashboard_lego.core import BaseDataSource, DataBuilder
        >>>
        >>> # Create custom blocks with full control
        >>> datasource = BaseDataSource(...)
        >>> blocks = [
        ...     SingleMetricBlock(block_id="m1", datasource=datasource, ...),
        ...     TypedChartBlock(block_id="c1", datasource=datasource, ...)
        ... ]
        >>>
        >>> app = quick_dashboard(blocks=blocks, title="Custom Dashboard")
        >>> app.run(debug=True)  # Opens in browser

    Args:
        df: DataFrame for simple mode (mutually exclusive with blocks).
            Must be non-empty pandas DataFrame.
        cards: List of card specifications (1-4 cards, simple mode only).
            Each card is a dict with:
            - Metric card: {"type": "metric", "column": str, "agg": str,
              "title": str, "color": str (optional)}
            - Chart card: {"type": "chart", "plot_type": str, "x": str,
              "y": str, "title": str, "color": str (optional), "size": str (optional)}
            - Text card: {"type": "text", "content": str}
        blocks: List of BaseBlock instances (1-4 blocks, advanced mode only).
            Mutually exclusive with df/cards.
        title: Dashboard title (default: "Quick Dashboard")
        theme: Theme name - any Bootstrap theme name or custom:
            light, dark, lux, cyborg, bootstrap, cerulean, cosmo, flatly, etc.
            Default: "lux"

    Returns:
        Dash app object ready to run.
        Works in Jupyter notebooks and standard Python scripts.
        Call app.run(debug=True) to start the server (opens in browser tab).

    Raises:
        ValueError: If both df and blocks provided, or neither provided, or
            card count not in 1-4 range, or invalid card specifications

    Note:
        No disk I/O: Uses in-memory data pipeline (cache_ttl=0).
        Works in Jupyter notebooks - dashboard opens in new browser tab.
    """
    logger.info(
        f"[Utils|JupyterFactory|quick_dashboard] ENTER | "
        f"mode={'simple' if df is not None else 'advanced'} | "
        f"title={title} | theme={theme}"
    )

    # Contract validation: mutually exclusive modes
    if df is not None and blocks is not None:
        raise ValueError(
            "Cannot provide both 'df' and 'blocks'. "
            "Use simple mode (df + cards) OR advanced mode (blocks), not both."
        )

    if df is None and blocks is None:
        raise ValueError(
            "Must provide either 'df' (simple mode) or 'blocks' (advanced mode)"
        )

    # Simple mode: build blocks from card specs using smart layout
    if df is not None:
        if cards is None or len(cards) == 0:
            raise ValueError("Simple mode requires 'cards' list with 1-4 card specs")

        if len(cards) > 4:
            raise ValueError(
                f"Too many cards: {len(cards)}. Maximum 4 cards for quick_dashboard()"
            )

        logger.debug(
            f"[Utils|QuickDashboard|quick_dashboard] Simple mode | "
            f"cards={len(cards)} | df_shape={df.shape}"
        )

        # Create in-memory datasource (cache_ttl=0 for no disk writes)
        datasource = BaseDataSource(
            data_builder=InMemoryDataBuilder(df),
            cache_ttl=0,  # No disk caching
        )

        # Use smart layout (creates blocks internally with get_metric_row)
        try:
            layout = _smart_layout(cards, datasource)
        except Exception as e:
            raise ValueError(f"Error creating layout: {e}") from e

    # Advanced mode: use blocks directly with simple layout
    else:
        if len(blocks) > 4:  # type: ignore
            raise ValueError(
                f"Too many blocks: {len(blocks)}. Maximum 4 blocks for quick_dashboard()"  # type: ignore
            )

        logger.debug(
            f"[Utils|QuickDashboard|quick_dashboard] Advanced mode | blocks={len(blocks)}"  # type: ignore
        )

        # For advanced mode, use simple layout (no smart grouping)
        count = len(blocks)  # type: ignore
        if count == 1:
            layout = one_column(blocks)  # type: ignore
        elif count == 2:
            layout = two_column_6_6(blocks[0], blocks[1])  # type: ignore
        elif count == 3:
            # 1 full + 2 in 50/50
            layout = [*one_column([blocks[0]]), *two_column_6_6(blocks[1], blocks[2])]  # type: ignore
        else:  # 4 blocks
            layout = [*two_column_6_6(blocks[0], blocks[1]), *two_column_6_6(blocks[2], blocks[3])]  # type: ignore

    # Get theme configuration
    theme_url, theme_config = _get_theme_url_and_config(theme)

    # Create page
    page = DashboardPage(
        title=title,
        blocks=layout,
        theme=theme_url,
        theme_config=theme_config,
    )

    # Always use standard Dash (JupyterDash compatibility issues with Dash 2.14+)
    # Note: JupyterDash is deprecated and has compatibility issues with modern Dash
    # Standard Dash works in Jupyter notebooks (opens in new tab)
    logger.info(
        "[Utils|JupyterFactory|quick_dashboard] Creating Dash app "
        "(compatible with Jupyter notebooks)"
    )
    app = dash.Dash(
        __name__,
        external_stylesheets=[theme_url],
        suppress_callback_exceptions=True,
    )

    # Build layout and register callbacks
    app.layout = page.build_layout()
    page.register_callbacks(app)

    card_count = len(cards) if df is not None else len(blocks)  # type: ignore
    logger.info(
        f"[Utils|QuickDashboard|quick_dashboard] EXIT | "
        f"app_type=Dash | cards={card_count} | ready=True"
    )

    return app
