"""
IPython magic functions for Dashboard Lego.

Provides convenient magic commands for rapid dashboard creation and Plotly export in Jupyter:
- %dashboard - Quick dashboard from DataFrame variable
- %%dashboard - Cell magic for dashboard with YAML/dict config
- %dashboard_theme - Set default theme for future dashboards
- %plotly_export - Export Plotly figure from dashboard block
- %plotly_show - Display Plotly figure in Jupyter notebook
- %%plotly_export - Cell magic for batch Plotly figure export

:hierarchy: [IPython | Magics]
:relates-to:
 - motivated_by: "Jupyter users need ultra-fast dashboard creation and Plotly export:
                  magic commands eliminate boilerplate for both dashboard creation and figure export"
 - implements: "IPython magic functions for Dashboard Lego"

:contract:
 - pre: "IPython environment, dashboard_lego installed"
 - post: "Magic functions registered and available in notebook"
 - invariant: "No disk writes, state stored in IPython user_ns only"

:complexity: 5
"""

import time
import uuid
from datetime import datetime
from typing import Any, Dict, List, Optional

import pandas as pd
import yaml
from IPython.core.magic import Magics, cell_magic, line_magic, magics_class
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring

from dashboard_lego.blocks.control_panel import ControlPanelBlock
from dashboard_lego.blocks.minimal_chart import MinimalChartBlock
from dashboard_lego.blocks.single_metric import SingleMetricBlock
from dashboard_lego.blocks.text import TextBlock
from dashboard_lego.blocks.typed_chart import Control, TypedChartBlock
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.utils.logger import get_logger
from dashboard_lego.utils.quick_dashboard import quick_dashboard
from dashboard_lego.utils.server import ManagedDashServer

logger = get_logger(__name__)


# LLM:METADATA
# :hierarchy: [IPython | Magics | DashboardMagics]
# :relates-to:
#  - motivated_by: "Ultra-fast dashboard creation and Plotly export: magic commands
#                   eliminate boilerplate for both dashboard creation and figure export"
#  - implements: "IPython Magics class with line and cell magics for dashboard and export"
#  - uses: ["quick_dashboard: underlying factory", "IPython.shell: access to user namespace",
#           "block.get_figure(): export functionality"]
# :contract:
#  - pre: "IPython shell available, dashboard_lego installed"
#  - post: "Magics registered: %dashboard, %%dashboard, %dashboard_theme, %plotly_export, %plotly_show, %%plotly_export"
#  - invariant: "Theme preference stored in shell.user_ns['_dashboard_theme']"
# :complexity: 6
# :decision_cache: "Added Plotly export magics to complement dashboard creation magics [magic-export]"
# LLM:END


@magics_class
class DashboardMagics(Magics):
    """
    IPython magic functions for Dashboard Lego.

    Provides convenient commands for rapid dashboard creation:
    - %dashboard: Create dashboard from DataFrame variable
    - %%dashboard: Create dashboard from cell config
    - %dashboard_theme: Set default theme

    Example:
        >>> %dashboard df --metric Sales sum "Total Sales" --chart bar Product Sales
        >>> %dashboard_theme cyborg
        >>> %%dashboard df
        ... metric: Sales, sum, "Total Sales", success
        ... chart: bar, Product, Sales, "Sales Chart"
    """

    def __init__(self, shell: Any):
        """Initialize magic functions."""
        super().__init__(shell)
        # Default theme stored in user namespace
        if "_dashboard_theme" not in shell.user_ns:
            shell.user_ns["_dashboard_theme"] = "lux"
        # Process registry for tracking background dashboard processes
        if "_dashboard_processes" not in shell.user_ns:
            shell.user_ns["_dashboard_processes"] = {}

    @line_magic
    @magic_arguments()
    @argument("dataframe", type=str, help="DataFrame variable name")
    @argument("--title", "-t", type=str, default=None, help="Dashboard title")
    @argument("--theme", type=str, default=None, help="Theme name")
    @argument("--port", "-p", type=int, default=8050, help="Server port")
    @argument(
        "--metric",
        "-m",
        nargs="+",
        action="append",
        help="Metric: column agg title [color]",
    )
    @argument(
        "--chart",
        "-c",
        nargs="+",
        action="append",
        help="Chart: plot_type x y title",
    )
    @argument("--text", "-x", type=str, action="append", help="Text content (Markdown)")
    @argument(
        "--nonblocking",
        "-nb",
        action="store_true",
        help="Run dashboard in background (non-blocking mode)",
    )
    def dashboard(self, line: str) -> None:
        """
        Create quick dashboard from DataFrame variable.

        Usage:
            %dashboard df --metric Sales sum "Total" success --chart bar Product Sales
            %dashboard df --nonblocking  # Run in background

        Args (via magic_arguments):
            dataframe: Name of DataFrame variable
            --title: Dashboard title
            --theme: Theme name (default: current preference)
            --port: Server port (default: 8050)
            --metric: Metric spec (can use multiple times)
            --chart: Chart spec (can use multiple times)
            --text: Text content (can use multiple times)
            --nonblocking: Run dashboard in background (non-blocking mode)

        Example:
            >>> df = pd.DataFrame({'Sales': [100, 200]})
            >>> %dashboard df -m Sales sum "Total Sales" success -c bar Product Sales
        """
        args = parse_argstring(self.dashboard, line)

        # Get DataFrame from user namespace
        df_name = args.dataframe
        if df_name not in self.shell.user_ns:
            print(f"❌ Error: DataFrame '{df_name}' not found in namespace")
            return

        df = self.shell.user_ns[df_name]
        if not isinstance(df, pd.DataFrame):
            print(f"❌ Error: '{df_name}' is not a DataFrame")
            return

        # Build cards from arguments
        cards = []

        # Add metrics
        if args.metric:
            for metric_args in args.metric:
                if len(metric_args) < 3:
                    print("⚠️  Skipping metric: need at least column, agg, title")
                    continue

                column, agg, title = metric_args[0], metric_args[1], metric_args[2]
                color = metric_args[3] if len(metric_args) > 3 else "primary"

                cards.append(
                    {
                        "type": "metric",
                        "column": column,
                        "agg": agg,
                        "title": title,
                        "color": color,
                    }
                )

        # Add charts
        if args.chart:
            for chart_args in args.chart:
                if len(chart_args) < 4:
                    print("⚠️  Skipping chart: need plot_type, x, y, title")
                    continue

                plot_type, x, y, title = (
                    chart_args[0],
                    chart_args[1],
                    chart_args[2],
                    chart_args[3],
                )

                cards.append(
                    {
                        "type": "chart",
                        "plot_type": plot_type,
                        "x": x,
                        "y": y,
                        "title": title,
                    }
                )

        # Add text cards
        if args.text:
            for content in args.text:
                cards.append({"type": "text", "content": content})

        # Validate card count
        if not cards:
            print("❌ Error: No cards specified. Use --metric, --chart, or --text")
            return

        if len(cards) > 4:
            print(f"❌ Error: Too many cards ({len(cards)}). Maximum 4 cards.")
            return

        # Get theme (from arg or saved preference)
        theme = args.theme or self.shell.user_ns.get("_dashboard_theme", "lux")
        title = args.title or f"{df_name} Dashboard"

        # Create and run dashboard
        print(f"🚀 Creating dashboard with {len(cards)} card(s)...")
        print(f"   Theme: {theme}")
        print(f"   Port: {args.port}")

        try:
            app = quick_dashboard(df=df, cards=cards, title=title, theme=theme)

            if args.nonblocking:
                # Run in background
                process_id = self._run_dashboard_in_background(app, args.port, title)
                print(f"⚠️  Dashboard running in background (process: {process_id})")
                print(f"   Access at: http://127.0.0.1:{args.port}/")
                print(f"💡 Use '%dashboard_kill {process_id}' to stop")
            else:
                # Run in foreground (blocking)
                server = ManagedDashServer(
                    app=app, host="127.0.0.1", port=args.port, title=title
                )
                print(f"✅ Dashboard ready at http://127.0.0.1:{args.port}/")
                try:
                    server.run_blocking()
                except KeyboardInterrupt:
                    print("\n✋ Dashboard stopped by user (Ctrl+C)")
                finally:
                    server.shutdown()
        except Exception as e:
            print(f"❌ Error creating dashboard: {e}")

    @cell_magic
    def dashboard_cell(self, line: str, cell: str) -> None:
        """
        Create dashboard from cell configuration.

        Cell format (simple YAML-like):
            nonblocking: true
            dataframe: df_name
            title: "My Dashboard"
            theme: lux
            port: 8050
            cards:
              - metric: Sales, sum, "Total Sales", success
              - chart: bar, Product, Sales, "Sales Chart"
              - text: "## Summary\\n\\nKey insights"

        Placeholder Support:
        - title: Static card title (no {{placeholders}})
        - plot_title: Dynamic plot title (supports {{placeholders}})
        - plot_params: x, y, color, size support {{placeholders}}
        - controls: name, options, value support {{placeholders}}

        Usage:
            %%dashboard_cell
            dataframe: df
            cards:
              - metric: Sales, sum, "Total Sales"
              - chart: bar, Product, Sales

            %%dashboard_cell
            nonblocking: true
            dataframe: df
            cards:
              - metric: Sales, sum, "Total Sales"

        Args:
            line: Line arguments (optional, for future extensions)
            cell: Cell content with configuration
        """
        print("📝 Parsing cell configuration...")

        config = self._parse_cell_config(cell)

        # Get DataFrame
        df_name = config.get("dataframe", None)
        df = self.shell.user_ns.get(str(df_name), None)

        # Get DataSource
        datasource_name = config.get("datasource", None)
        datasource = self.shell.user_ns.get(str(datasource_name), None)
        if datasource is not None and df is not None:
            print("❌ Error: 'dataframe:' or 'datasource:' not specified in cell")
            return
        # Get configuration
        title = config.get("title", f"{df_name} Dashboard")
        theme = config.get("theme", self.shell.user_ns.get("_dashboard_theme", "lux"))
        port = config.get("port", 8050)
        cards = config.get("cards", [])

        if not cards:
            print("❌ Error: No cards specified")
            return

        if len(cards) > 4:
            print(f"❌ Error: Too many cards ({len(cards)}). Maximum 4.")
            return

        # Create dashboard
        print(f"🚀 Creating dashboard with {len(cards)} card(s)...")

        try:
            app = quick_dashboard(
                df=df, datasource=datasource, cards=cards, title=title, theme=theme
            )

            if config.get("nonblocking", False):
                # Run in background
                process_id = self._run_dashboard_in_background(app, port, title)
                print(f"⚠️  Dashboard running in background (process: {process_id})")
                print(f"   Access at: http://127.0.0.1:{port}/")
                print(f"💡 Use '%dashboard_kill {process_id}' to stop")
            else:
                # Run in foreground (blocking) - CELL STAYS IN RUNNING STATE [*]
                server = ManagedDashServer(
                    app=app, host="127.0.0.1", port=port, title=title
                )
                print(f"\n📊 Dashboard ready at http://127.0.0.1:{port}/")
                print("⏸️  Cell is RUNNING - dashboard active")
                print(
                    "🛑 Stop with: Ctrl+C (in terminal) or stop button (in notebook)\n"
                )

                try:
                    # This will block until interrupted by Ctrl+C or notebook stop
                    server.run_blocking()
                except KeyboardInterrupt:
                    print("\n✋ Dashboard stopped by user (Ctrl+C)")
                except Exception as e:
                    print(f"\n❌ Dashboard error: {e}")
                    raise
                finally:
                    server.shutdown()
        except Exception as e:
            print(f"❌ Error: {e}")

    @line_magic
    def dashboard_theme(self, line: str) -> None:
        """
        Set default theme for future dashboards.

        Usage:
            %dashboard_theme cyborg
            %dashboard_theme lux

        Available themes:
            lux, dark, light, cyborg, slate, solar, superhero, minty, flatly,
            cosmo, cerulean, journal, litera, lumen, pulse, sandstone, simplex,
            sketchy, spacelab, united, yeti

        Args:
            line: Theme name
        """
        theme = line.strip()

        if not theme:
            current = self.shell.user_ns.get("_dashboard_theme", "lux")
            print(f"📊 Current theme: {current}")
            print("\nAvailable themes:")
            themes = [
                "lux",
                "dark",
                "light",
                "cyborg",
                "slate",
                "solar",
                "superhero",
                "minty",
                "flatly",
                "cosmo",
                "cerulean",
                "journal",
                "litera",
                "lumen",
                "pulse",
                "sandstone",
                "simplex",
                "sketchy",
                "spacelab",
                "united",
                "yeti",
            ]
            for t in themes:
                marker = "✓" if t == current else " "
                print(f"  [{marker}] {t}")
            return

        self.shell.user_ns["_dashboard_theme"] = theme
        print(f"✅ Theme set to: {theme}")

    @line_magic
    @magic_arguments()
    @argument("block", type=str, help="Dashboard Lego block variable name")
    @argument(
        "--format",
        "-f",
        type=str,
        default="html",
        choices=["html", "png", "json", "svg"],
        help="Export format",
    )
    @argument("--output", "-o", type=str, help="Output file path")
    @argument("--title", "-t", type=str, help="Figure title (for HTML)")
    @argument("--width", "-w", type=int, default=800, help="Figure width")
    @argument("--height", "-h", type=int, default=600, help="Figure height")
    @argument(
        "--params",
        "-p",
        type=str,
        help="JSON string of parameters for block.get_figure()",
    )
    def plotly_export(self, line: str) -> None:
        """
        Export Plotly figure from dashboard_lego block.

        Usage:
            %plotly_export chart_block --format html --output chart.html --title "My Chart"
            %plotly_export chart_block -f png -o chart.png --width 1000 --height 800
            %plotly_export chart_block -f json -o chart.json

        Args:
            block: Name of dashboard_lego block variable
            --format: Export format (html, png, json, svg)
            --output: Output file path (required)
            --title: Figure title (for HTML export)
            --width: Figure width (for image formats)
            --height: Figure height (for image formats)
            --params: JSON parameters for block.get_figure()

        Example:
            >>> chart = TypedChartBlock(...)
            >>> %plotly_export chart -f html -o my_chart.html -t "Sales Analysis"
        """
        args = parse_argstring(self.plotly_export, line)

        # Validate required arguments
        if not args.output:
            print("❌ Error: --output/-o is required")
            return

        if args.block not in self.shell.user_ns:
            print(f"❌ Error: Block variable '{args.block}' not found")
            return

        block = self.shell.user_ns[args.block]

        # Check if block has get_figure method
        if not hasattr(block, "get_figure"):
            print(f"❌ Error: Block '{args.block}' does not support figure export")
            return

        try:
            # Parse parameters if provided
            params = {}
            if args.params:
                import json

                params = json.loads(args.params)

            # Get figure from block
            print(f"📊 Exporting figure from '{args.block}'...")
            fig = block.get_figure(params)

            # Set title if provided
            if args.title:
                fig.update_layout(title_text=args.title, title_x=0.5)

            # Export based on format
            if args.format == "html":
                fig.write_html(args.output)
                print(f"✅ Exported HTML to: {args.output}")

            elif args.format == "png":
                fig.write_image(args.output, width=args.width, height=args.height)
                print(f"✅ Exported PNG to: {args.output}")

            elif args.format == "svg":
                fig.write_image(
                    args.output, format="svg", width=args.width, height=args.height
                )
                print(f"✅ Exported SVG to: {args.output}")

            elif args.format == "json":
                # Save as JSON
                import json

                with open(args.output, "w") as f:
                    f.write(fig.to_json())
                print(f"✅ Exported JSON to: {args.output}")

        except Exception as e:
            print(f"❌ Error exporting figure: {e}")
            import traceback

            traceback.print_exc()

    @line_magic
    @magic_arguments()
    @argument("block", type=str, help="Dashboard Lego block variable name")
    @argument("--title", "-t", type=str, help="Figure title")
    @argument("--width", "-w", type=int, default=800, help="Figure width")
    @argument("--height", "-h", type=int, default=600, help="Figure height")
    @argument(
        "--params",
        "-p",
        type=str,
        help="JSON string of parameters for block.get_figure()",
    )
    def plotly_show(self, line: str) -> None:
        """
        Display Plotly figure from dashboard_lego block in Jupyter notebook.

        Usage:
            %plotly_show chart_block
            %plotly_show chart_block --title "My Chart" --width 1000 --height 800

        Args:
            block: Name of dashboard_lego block variable
            --title: Figure title
            --width: Display width
            --height: Display height
            --params: JSON parameters for block.get_figure()

        Example:
            >>> chart = TypedChartBlock(...)
            >>> %plotly_show chart -t "Sales Analysis"
        """
        args = parse_argstring(self.plotly_show, line)

        if args.block not in self.shell.user_ns:
            print(f"❌ Error: Block variable '{args.block}' not found")
            return

        block = self.shell.user_ns[args.block]

        # Check if block has get_figure method
        if not hasattr(block, "get_figure"):
            print(f"❌ Error: Block '{args.block}' does not support figure export")
            return

        try:
            # Parse parameters if provided
            params = {}
            if args.params:
                import json

                params = json.loads(args.params)

            # Get figure from block
            print(f"📊 Displaying figure from '{args.block}'...")
            fig = block.get_figure(params)

            # Set title if provided
            if args.title:
                fig.update_layout(title_text=args.title, title_x=0.5)

            # Update layout for display
            fig.update_layout(width=args.width, height=args.height)

            # Display in Jupyter
            fig.show()

        except Exception as e:
            print(f"❌ Error displaying figure: {e}")
            import traceback

            traceback.print_exc()

    def _parse_cell_config(self, cell: str) -> Dict[str, Any]:
        """
        Parse YAML cell configuration with environment variable interpolation.

        Format:
            dataframe: session_hp_datasource
            title: "Dashboard Title"
            theme: lux

            environment:
              - session_hp_datasource  # Variables to take from user_ns
              - metric_options
              - color_palette

            cards:
              - type: chart
                plot_type: scatter
                x: session_length
                y: max_idle
                controls:
                  - name: metric_selector
                    type: dropdown
                    options: $metric_options  # Will be interpolated

        Variable interpolation:
        - $var_name: Replace with variable from IPython user_ns
        - Supports all YAML types: strings, dicts, lists, numbers, bools
        - Security: Only access to variables declared in environment list

        Args:
            cell: Cell content string (YAML format)

        Returns:
            Configuration dict with interpolated variables

        Raises:
            ValueError: If YAML is invalid or environment variable not found
        """

        # Parse YAML
        try:
            raw_config = yaml.safe_load(cell)
        except yaml.YAMLError as e:
            print(f"❌ Invalid YAML format: {e}")
            raise ValueError(f"Failed to parse YAML: {e}")

        if not raw_config:
            print("❌ Empty configuration")
            raise ValueError("Configuration is empty")

        if not isinstance(raw_config, dict):
            print("❌ Configuration must be a YAML dictionary")
            raise ValueError("Configuration must be a YAML dictionary")

        # Extract environment variables list
        environment = raw_config.pop("environment", [])

        if not isinstance(environment, list):
            print("❌ 'environment' must be a list of variable names")
            raise ValueError("'environment' must be a list of variable names")

        # Build interpolation map: {var_name: var_value}
        env_map = {}
        for var_name in environment:
            if not isinstance(var_name, str):
                print(
                    f"❌ Environment variable name must be string, got {type(var_name)}"
                )
                raise ValueError(
                    f"Environment variable name must be string, got {type(var_name)}"
                )

            if var_name not in self.shell.user_ns:
                available = [
                    k for k in self.shell.user_ns.keys() if not k.startswith("_")
                ]
                print(f"❌ Environment variable '{var_name}' not found in namespace")
                print(f"   Available: {', '.join(available[:10])}")
                raise ValueError(f"Variable '{var_name}' not found in user namespace")

            env_map[var_name] = self.shell.user_ns[var_name]
            logger.debug(
                f"[DashboardMagics|Config] Loaded env: {var_name} = {type(env_map[var_name])}"
            )

        # Recursively interpolate $variable references in config
        try:
            config = self._interpolate_config(raw_config, env_map)
        except ValueError as e:
            print(f"❌ Interpolation error: {e}")
            raise

        logger.debug(
            f"[DashboardMagics|Config] Parsed config with {len(environment)} env vars"
        )
        return config

    def _interpolate_config(self, obj: Any, env_map: Dict[str, Any]) -> Any:
        """
        Recursively interpolate $variable references in config structure.

        Supports: strings, lists, dicts, nested structures.
        All YAML types (int, float, bool, None) passed through as-is.

        Args:
            obj: Config object (str, dict, list, or other)
            env_map: {variable_name: variable_value} mapping

        Returns:
            Config with interpolated values

        Raises:
            ValueError: If referenced variable not in env_map
        """
        if isinstance(obj, str):
            # Replace $var_name with env_map[var_name]
            import re

            # CASE 1: Standalone variable (entire string is "$var") → return object as-is
            m = re.fullmatch(r"\$([a-zA-Z_][a-zA-Z0-9_]*)", obj)
            if m:
                var_name = m.group(1)
                if var_name not in env_map:
                    raise ValueError(
                        f"Variable '${var_name}' not found in environment. "
                        f"Available: {', '.join(env_map.keys())}"
                    )
                return env_map[var_name]

            # CASE 2: Interpolation inside a larger string → only allow string env values
            def replace_var(match):
                var_name = match.group(1)
                if var_name not in env_map:
                    raise ValueError(
                        f"Variable '${var_name}' not found in environment. "
                        f"Available: {', '.join(env_map.keys())}"
                    )
                value = env_map[var_name]
                if isinstance(value, str):
                    return value
                # Non-string inside a larger text → explicit guidance
                raise ValueError(
                    f"Cannot interpolate non-string variable '${var_name}' of type {type(value).__name__} into a string. "
                    f"Use standalone form: key: ${var_name}"
                )

            try:
                return re.sub(r"\$([a-zA-Z_][a-zA-Z0-9_]*)", replace_var, obj)
            except ValueError as e:
                raise ValueError(f"Interpolation failed: {e}")

        elif isinstance(obj, dict):
            return {
                key: self._interpolate_config(value, env_map)
                for key, value in obj.items()
            }

        elif isinstance(obj, list):
            return [self._interpolate_config(item, env_map) for item in obj]

        else:
            # Return as-is (int, float, bool, None, etc.)
            return obj

    def _build_controls_from_spec(
        self, controls_spec: Optional[List[Dict[str, Any]]]
    ) -> Dict[str, Control]:
        """
        Build Control objects from YAML specification using shared helper.

        Args:
            controls_spec: List of control specifications from YAML

        Returns:
            {control_name: Control} dict
        """
        from dashboard_lego.blocks.control_helpers import build_controls_from_spec

        return build_controls_from_spec(controls_spec)

    def _create_block_from_spec_yaml(
        self,
        card_spec: Dict[str, Any],
        datasource: DataSource,
        block_id: str,
    ) -> Any:
        """
        Create block from YAML card specification (YAML = kwargs + type).

        YAML must match block constructor kwargs exactly (plus 'type' field).
        Supports: metric, chart, minimal_chart, text, control_panel

        Args:
            card_spec: Card specification dict from YAML matching block constructor
            datasource: DataSource instance
            block_id: Unique block identifier

        Returns:
            BaseBlock instance

        Raises:
            ValueError: If required fields missing
        """
        card_type = card_spec.get("type")
        if not card_type:
            raise ValueError("Card spec missing required field: 'type'")

        # Prepare kwargs by copying card_spec (excluding 'type')
        kwargs = card_spec.copy()
        kwargs.pop("type", None)
        kwargs["block_id"] = block_id
        kwargs["datasource"] = datasource

        if card_type == "metric":
            # Require metric_spec dict
            if "metric_spec" not in kwargs:
                raise ValueError("Metric card missing required: metric_spec")
            return SingleMetricBlock(**kwargs)

        elif card_type in ["chart", "minimal_chart"]:
            # Require plot_params dict
            if "plot_params" not in kwargs:
                raise ValueError(f"{card_type} card missing required: plot_params")

            # Handle controls if present
            if "controls" in kwargs:
                kwargs["controls"] = self._build_controls_from_spec(kwargs["controls"])

            # Determine block class
            if card_type == "chart":
                if "plot_type" not in kwargs:
                    raise ValueError("Chart card missing required: plot_type")
                block_class = TypedChartBlock
            else:  # minimal_chart
                block_class = MinimalChartBlock

            return block_class(**kwargs)

        elif card_type == "text":
            # Require content_generator (can be string, will be wrapped)
            if "content_generator" not in kwargs:
                raise ValueError("Text card missing required: content_generator")

            # If content_generator is a string, wrap it in a lambda
            content_gen = kwargs["content_generator"]
            if isinstance(content_gen, str):
                kwargs["content_generator"] = lambda df: content_gen

            return TextBlock(**kwargs)

        elif card_type == "control_panel":
            # Require title
            if "title" not in kwargs:
                raise ValueError("Control panel missing required: title")

            # Controls can be list of specs - ControlPanelBlock will convert it
            return ControlPanelBlock(**kwargs)

        else:
            raise ValueError(
                f"Unknown card type: '{card_type}'. Supported: metric, chart, minimal_chart, text, control_panel"
            )

    def _generate_process_id(self) -> str:
        """Generate unique process ID."""
        return f"dashboard_{int(time.time())}_{uuid.uuid4().hex[:8]}"

    # LLM:METADATA
    # :hierarchy: [IPython | Magics | DashboardMagics | Registry]
    # :relates-to:
    #  - motivated_by: "Dashboards started in background require tracking for kill commands and cleanup"
    #  - uses: ["ManagedDashServer.shutdown: lifecycle control", "datetime.now: capture start time"]
    # :contract:
    #  - pre: "process_id unique, server running"
    #  - post: "Registry entry accessible via _dashboard_processes"
    #  - invariant: "Each entry stores shutdown-capable server reference"
    # :complexity: 2
    # LLM:END
    def _register_process(
        self, process_id: str, port: int, server: ManagedDashServer, title: str
    ) -> None:
        """Register a dashboard process in the registry."""
        process_info = {
            "id": process_id,
            "port": port,
            "server": server,
            "start_time": datetime.now(),
            "title": title,
        }
        self.shell.user_ns["_dashboard_processes"][process_id] = process_info
        print(f"🔗 Registered process: {process_id} (port {port})")

    def _run_dashboard_in_background(self, app: Any, port: int, title: str) -> str:
        """Run dashboard in background thread and return process ID."""
        process_id = self._generate_process_id()
        server = ManagedDashServer(app=app, host="127.0.0.1", port=port, title=title)

        def _on_exit() -> None:
            processes = self.shell.user_ns.get("_dashboard_processes", {})
            if process_id in processes:
                del processes[process_id]
                print(f"🛑 Dashboard '{title}' stopped (process: {process_id})")

        try:
            server.run_background(on_exit=_on_exit)
            self._register_process(process_id, port, server, title)
            print(
                f"🚀 Dashboard '{title}' running in background at http://127.0.0.1:{port}/"
            )
            return process_id
        except Exception:
            server.shutdown()
            raise

    def _kill_process(self, process_id: str) -> bool:
        """Kill a specific dashboard process."""
        processes = self.shell.user_ns["_dashboard_processes"]

        if process_id not in processes:
            print(f"❌ Process '{process_id}' not found")
            return False

        process_info = processes[process_id]

        try:
            server: Optional[ManagedDashServer] = process_info.get("server")
            if server is not None:
                server.shutdown()
            del processes[process_id]
            print(f"✅ Process '{process_id}' stopped (port {process_info['port']})")
            return True
        except Exception as e:
            print(f"❌ Error stopping process '{process_id}': {e}")
            return False

    def _kill_all_processes(self) -> int:
        """Kill all registered dashboard processes."""
        processes = self.shell.user_ns["_dashboard_processes"]
        killed_count = 0

        for process_id in list(processes.keys()):
            if self._kill_process(process_id):
                killed_count += 1

        print(f"🛑 Stopped {killed_count} dashboard process(es)")
        return killed_count

    @line_magic
    def dashboard_kill(self, line: str) -> None:
        """
        Kill dashboard process(es).

        Usage:
            %dashboard_kill process_id    # Kill specific process
            %dashboard_kill all           # Kill all processes
            %dashboard_kill               # Show active processes

        Args:
            line: Process ID to kill, 'all' to kill all, or empty to list processes
        """
        processes = self.shell.user_ns["_dashboard_processes"]

        if not line.strip():
            # Show active processes
            if not processes:
                print("📊 No active dashboard processes")
                return

            print("📊 Active dashboard processes:")
            for pid, info in processes.items():
                start_time = info["start_time"].strftime("%H:%M:%S")
                print(
                    f"  {pid}: {info['title']} (port {info['port']}, started {start_time})"
                )
            return

        target = line.strip().lower()

        if target == "all":
            count = self._kill_all_processes()
            if count > 0:
                print(f"✅ Killed all {count} dashboard process(es)")
        else:
            # Try to kill specific process
            if self._kill_process(target):
                print(f"✅ Killed process '{target}'")
            else:
                print(f"❌ Process '{target}' not found")
                print("💡 Use '%dashboard_kill' (no arguments) to see active processes")

    @cell_magic
    def plotly_export_cell(self, line: str, cell: str) -> None:
        """
        Batch export multiple Plotly figures from cell configuration.

        Cell format (YAML-like):
            exports:
              - block: chart1
                format: html
                output: chart1.html
                title: "Chart 1"
              - block: chart2
                format: png
                output: chart2.png
                width: 1000
                height: 800

        Usage:
            %%plotly_export_cell
            exports:
              - block: sales_chart
                format: html
                output: sales_report.html
                title: "Sales Analysis"
              - block: profit_chart
                format: png
                output: profit_analysis.png

        Args:
            line: Line arguments (optional)
            cell: Cell content with export configuration
        """
        print("📦 Parsing batch export configuration...")

        # Parse cell configuration similar to dashboard_cell
        config = self._parse_plotly_export_config(cell)

        exports = config.get("exports", [])

        if not exports:
            print("❌ Error: No exports specified in cell")
            return

        success_count = 0
        error_count = 0

        for export_spec in exports:
            try:
                # Get block from user namespace
                block_name = export_spec["block"]
                if block_name not in self.shell.user_ns:
                    print(f"❌ Error: Block '{block_name}' not found")
                    error_count += 1
                    continue

                block = self.shell.user_ns[block_name]

                # Check if block supports figure export
                if not hasattr(block, "get_figure"):
                    print(
                        f"❌ Error: Block '{block_name}' does not support figure export"
                    )
                    error_count += 1
                    continue

                # Parse parameters if provided
                params = export_spec.get("params", {})

                # Get figure from block
                print(f"📊 Exporting '{block_name}' to {export_spec['format']}...")
                fig = block.get_figure(params)

                # Set title if provided
                if "title" in export_spec:
                    fig.update_layout(title_text=export_spec["title"], title_x=0.5)

                # Export based on format
                output_path = export_spec["output"]
                export_format = export_spec["format"]

                if export_format == "html":
                    fig.write_html(output_path)
                    print(f"  ✅ HTML: {output_path}")

                elif export_format == "png":
                    width = export_spec.get("width", 800)
                    height = export_spec.get("height", 600)
                    fig.write_image(output_path, width=width, height=height)
                    print(f"  ✅ PNG: {output_path}")

                elif export_format == "svg":
                    width = export_spec.get("width", 800)
                    height = export_spec.get("height", 600)
                    fig.write_image(
                        output_path, format="svg", width=width, height=height
                    )
                    print(f"  ✅ SVG: {output_path}")

                elif export_format == "json":
                    with open(output_path, "w") as f:
                        f.write(fig.to_json())
                    print(f"  ✅ JSON: {output_path}")

                success_count += 1

            except Exception as e:
                print(
                    f"❌ Error exporting '{export_spec.get('block', 'unknown')}': {e}"
                )
                error_count += 1

        print(
            f"\n📊 Batch export complete: {success_count} success, {error_count} errors"
        )

    def _parse_plotly_export_config(self, cell: str) -> Dict[str, Any]:
        """
        Parse cell configuration for plotly export.

        Format:
            exports:
            - block: block_name
                format: html|png|svg|json
                output: file_path
                title: "Figure Title" (optional)
                width: 800 (optional, for images)
                height: 600 (optional, for images)
                params: {"key": "value"} (optional)

        Args:
            cell: Cell content string

        Returns:
            Configuration dict with 'exports' list
        """
        config: Dict[str, Any] = {"exports": []}

        lines = cell.strip().split("\n")
        current_export = None

        for line in lines:
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            if line.startswith("exports:"):
                continue
            elif line.startswith("- block:"):
                if current_export:
                    config["exports"].append(current_export)
                current_export = {"block": line.split("block:")[1].strip()}
            elif current_export and ":" in line:
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip().strip("\"'")

                if key in ["width", "height"]:
                    try:
                        current_export[key] = int(value)
                    except ValueError:
                        print(
                            f"⚠️  Warning: Invalid {key} value '{value}', using default"
                        )
                elif key == "params":
                    try:
                        import json

                        current_export[key] = json.loads(value)
                    except json.JSONDecodeError:
                        print(
                            f"⚠️  Warning: Invalid params JSON '{value}', using empty dict"
                        )
                        current_export[key] = {}
                else:
                    current_export[key] = value

        if current_export:
            config["exports"].append(current_export)

        return config


def load_ipython_extension(ipython: Any) -> None:
    """
    Load Dashboard Lego magic functions into IPython.

    Called when user runs: %load_ext dashboard_lego.ipython_magics

    Args:
        ipython: IPython InteractiveShell instance
    """
    ipython.register_magics(DashboardMagics)
    print("✅ Dashboard Lego magics loaded!")
    print("\nAvailable commands:")
    print(
        "  %dashboard df --metric col agg title [color] --chart type x y title [--nonblocking]"
    )
    print("  %%dashboard_cell  # Use YAML config in cell")
    print("  %dashboard_theme [theme_name]")
    print("  %dashboard_kill [process_id|all]  # New: Kill background processes")
    print("  %plotly_export block --format html --output file.html --title 'Title'")
    print("  %plotly_show block --title 'Title' --width 800 --height 600")
    print("  %%plotly_export_cell")
    print("\nExamples:")
    print('  %dashboard df -m Sales sum "Total Sales" success -c bar Product Sales')
    print("  %dashboard df --nonblocking  # Run in background")
    print("  %dashboard_kill dashboard_12345  # Stop specific process")
    print("  %dashboard_kill all  # Stop all processes")
    print('  %plotly_export chart -f html -o my_chart.html -t "Sales Analysis"')
    print("\nCell magic YAML format:")
    print("  %%dashboard_cell")
    print("  nonblocking: true")
    print("  dataframe: $df  # Variable interpolation")
    print('  title: "Dashboard for $dataset"')
    print("  cards:")
    print('    - metric: $sales_col, sum, "Total $sales_col"')
    print('    - chart: bar, $x_col, $y_col, "$x_col vs $y_col"')
    print("\nTry: %dashboard_theme to see available themes")
    print("Try: %dashboard_kill to see active processes")


def unload_ipython_extension(ipython: Any) -> None:
    """
    Unload Dashboard Lego magic functions.

    Args:
        ipython: IPython InteractiveShell instance
    """
    pass  # Magics are automatically unregistered
