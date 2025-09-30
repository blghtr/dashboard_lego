# 03_presets_dashboard.py

import dash
import dash_bootstrap_components as dbc

from core.datasources.csv_source import CsvDataSource
from core.page import DashboardPage
from presets.eda_presets import (
    CorrelationHeatmapPreset, GroupedHistogramPreset, MissingValuesPreset, BoxPlotPreset
)
from presets.layouts import two_column_8_4, kpi_row_top

# 1. Use the library's CsvDataSource - no magic needed!
datasource = CsvDataSource(file_path="examples/sample_data.csv")
datasource.init_data()

# 3. Instantiate the presets
# Static presets need to subscribe to a state to trigger their first render.
# We can give them a dummy state that never changes.
dummy_state = "dummy_state_for_init"

heatmap_preset = CorrelationHeatmapPreset(
    block_id="corr_heatmap",
    datasource=datasource,
    subscribes_to=dummy_state
)

missing_values_preset = MissingValuesPreset(
    block_id="missing_values",
    datasource=datasource,
    subscribes_to=dummy_state
)

# Interactive presets manage their own state.
histogram_preset = GroupedHistogramPreset(
    block_id="grouped_hist",
    datasource=datasource
)

box_plot_preset = BoxPlotPreset(
    block_id="box_plot",
    datasource=datasource
)

# 4. Create the Dashboard Page with a more complex layout
dashboard_page = DashboardPage(
    title="EDA with Presets",
    blocks=kpi_row_top(
        kpi_blocks=[missing_values_preset, heatmap_preset],
        content_rows=two_column_8_4(histogram_preset, box_plot_preset)
    ),
    theme=dbc.themes.CYBORG
)

# 5. Set up and run the Dash app
app = dash.Dash(__name__, external_stylesheets=[dashboard_page.theme])
app.layout = dashboard_page.build_layout()

# The StateManager will automatically connect the controls within the interactive presets
# to their respective graphs.
dashboard_page.register_callbacks(app)

if __name__ == "__main__":
    app.run(debug=True, use_reloader=False)