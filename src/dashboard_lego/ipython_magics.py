"""
IPython magic functions for Dashboard Lego.

Provides convenient magic commands for rapid dashboard creation in Jupyter:
- %dashboard - Quick dashboard from DataFrame variable
- %%dashboard - Cell magic for dashboard with YAML/dict config
- %dashboard_theme - Set default theme for future dashboards

:hierarchy: [IPython | Magics]
:relates-to:
 - motivated_by: "Jupyter users need ultra-fast dashboard creation: one-line
                  magic commands eliminate even quick_dashboard() boilerplate"
 - implements: "IPython magic functions for Dashboard Lego"

:contract:
 - pre: "IPython environment, dashboard_lego installed"
 - post: "Magic functions registered and available in notebook"
 - invariant: "No disk writes, state stored in IPython user_ns only"

:complexity: 5
"""

from typing import Any, Dict

import pandas as pd
from IPython.core.magic import Magics, cell_magic, line_magic, magics_class
from IPython.core.magic_arguments import argument, magic_arguments, parse_argstring

from dashboard_lego.utils.quick_dashboard import quick_dashboard

# LLM:METADATA
# :hierarchy: [IPython | Magics | DashboardMagics]
# :relates-to:
#  - motivated_by: "Ultra-fast dashboard creation: %dashboard df reduces
#                   boilerplate to single line, stores theme preference in
#                   IPython session state"
#  - implements: "IPython Magics class with line and cell magics"
#  - uses: ["quick_dashboard: underlying factory", "IPython.shell:
#           access to user namespace"]
# :contract:
#  - pre: "IPython shell available, dashboard_lego installed"
#  - post: "Magics registered: %dashboard, %%dashboard, %dashboard_theme"
#  - invariant: "Theme preference stored in shell.user_ns['_dashboard_theme']"
# :complexity: 5
# :decision_cache: "Store theme in user_ns over global var: survives cell
#                   re-execution, accessible across magic calls [magic-state]"
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
    def dashboard(self, line: str) -> None:
        """
        Create quick dashboard from DataFrame variable.

        Usage:
            %dashboard df --metric Sales sum "Total" success --chart bar Product Sales

        Args (via magic_arguments):
            dataframe: Name of DataFrame variable
            --title: Dashboard title
            --theme: Theme name (default: current preference)
            --port: Server port (default: 8050)
            --metric: Metric spec (can use multiple times)
            --chart: Chart spec (can use multiple times)
            --text: Text content (can use multiple times)

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
            print(f"✅ Dashboard ready at http://127.0.0.1:{args.port}/")
            app.run(debug=True, port=args.port)
        except Exception as e:
            print(f"❌ Error creating dashboard: {e}")

    @cell_magic
    def dashboard_cell(self, line: str, cell: str) -> None:
        """
        Create dashboard from cell configuration.

        Cell format (simple YAML-like):
            dataframe: df_name
            title: "My Dashboard"
            theme: lux
            cards:
              - metric: Sales, sum, "Total Sales", success
              - chart: bar, Product, Sales, "Sales Chart"
              - text: "## Summary\\n\\nKey insights"

        Usage:
            %%dashboard_cell
            dataframe: df
            cards:
              - metric: Sales, sum, "Total Sales"
              - chart: bar, Product, Sales

        Args:
            line: Line arguments (optional)
            cell: Cell content with configuration
        """
        print("📝 Parsing cell configuration...")

        config = self._parse_cell_config(cell)

        # Get DataFrame
        df_name = config.get("dataframe")
        if not df_name:
            print("❌ Error: 'dataframe:' not specified in cell")
            return

        if df_name not in self.shell.user_ns:
            print(f"❌ Error: DataFrame '{df_name}' not found")
            return

        df = self.shell.user_ns[df_name]

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
            app = quick_dashboard(df=df, cards=cards, title=title, theme=theme)
            print(f"✅ Dashboard ready at http://127.0.0.1:{port}/")
            app.run(debug=True, port=port)
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

    def _parse_cell_config(self, cell: str) -> Dict[str, Any]:
        """
        Parse simple YAML-like cell configuration.

        Format:
            dataframe: df_name
            title: "My Dashboard"
            theme: lux
            port: 8050
            cards:
              - metric: column, agg, title, [color]
              - chart: plot_type, x, y, title
              - text: "content"

        Args:
            cell: Cell content string

        Returns:
            Configuration dict
        """
        config: Dict[str, Any] = {"cards": []}
        current_section = None

        for line in cell.strip().split("\n"):
            line = line.strip()
            if not line or line.startswith("#"):
                continue

            # Section headers
            if line == "cards:":
                current_section = "cards"
                continue

            # Top-level config
            if ":" in line and not line.startswith("-"):
                key, value = line.split(":", 1)
                key = key.strip()
                value = value.strip().strip('"').strip("'")

                if key in ("dataframe", "title", "theme"):
                    config[key] = value
                elif key == "port":
                    try:
                        config[key] = int(value)
                    except ValueError:
                        config[key] = 8050

            # Card definitions
            elif current_section == "cards" and line.startswith("-"):
                line = line[1:].strip()  # Remove dash

                if ":" in line:
                    card_type, card_spec = line.split(":", 1)
                    card_type = card_type.strip()
                    card_spec = card_spec.strip()

                    if card_type == "metric":
                        parts = [
                            p.strip().strip('"').strip("'")
                            for p in card_spec.split(",")
                        ]
                        if len(parts) >= 3:
                            config["cards"].append(
                                {
                                    "type": "metric",
                                    "column": parts[0],
                                    "agg": parts[1],
                                    "title": parts[2],
                                    "color": parts[3] if len(parts) > 3 else "primary",
                                }
                            )

                    elif card_type == "chart":
                        parts = [
                            p.strip().strip('"').strip("'")
                            for p in card_spec.split(",")
                        ]
                        if len(parts) >= 4:
                            config["cards"].append(
                                {
                                    "type": "chart",
                                    "plot_type": parts[0],
                                    "x": parts[1],
                                    "y": parts[2],
                                    "title": parts[3],
                                }
                            )

                    elif card_type == "text":
                        content = card_spec.strip('"').strip("'")
                        # Process escape sequences (handle both \n and \\n)
                        content = (
                            content.replace("\\\\n", "\n")
                            .replace("\\n", "\n")
                            .replace("\\\\t", "\t")
                            .replace("\\t", "\t")
                        )
                        config["cards"].append({"type": "text", "content": content})

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
    print("  %dashboard df --metric col agg title [color] --chart type x y title")
    print("  %%dashboard_cell")
    print("  %dashboard_theme [theme_name]")
    print("\nExample:")
    print('  %dashboard df -m Sales sum "Total Sales" success -c bar Product Sales')
    print("\nTry: %dashboard_theme to see available themes")


def unload_ipython_extension(ipython: Any) -> None:
    """
    Unload Dashboard Lego magic functions.

    Args:
        ipython: IPython InteractiveShell instance
    """
    pass  # Magics are automatically unregistered
