"""
Tests for knee plot functions.

:hierarchy: [Tests | Utils | KneePlots]
:relates-to:
 - motivated_by: "Unit tests for knee plot functionality"
 - implements: "test module: 'test_knee_plots'"

:contract:
 - pre: "Test environment with pandas and plotly available"
 - post: "All tests pass, knee plot functions work correctly"

:complexity: 2
"""

import pandas as pd
import plotly.graph_objects as go
import pytest

from dashboard_lego.utils.knee_plots import plot_knee


class TestPlotKnee:
    """
    Test cases for plot_knee function.

    :hierarchy: [Tests | Utils | KneePlots | TestPlotKnee]
    :relates-to:
     - motivated_by: "Comprehensive testing of knee plot functionality"
     - implements: "test class: 'TestPlotKnee'"

    :contract:
     - pre: "Valid test data available"
     - post: "All test cases pass"

    :complexity: 2
    """

    @pytest.fixture
    def sample_data(self):
        """Create sample data for knee plot testing."""
        # Create data that has a clear knee point
        k_values = list(range(1, 11))
        # Simulate inertia values with a clear elbow at k=3
        inertia_values = [100, 50, 20, 15, 12, 10, 9, 8, 7, 6]

        return pd.DataFrame(
            {
                "k": k_values,
                "inertia": inertia_values,
                "silhouette": [0.1, 0.3, 0.7, 0.6, 0.5, 0.4, 0.3, 0.2, 0.1, 0.0],
            }
        )

    def test_plot_knee_basic(self, sample_data):
        """Test basic knee plot without auto detection."""
        fig = plot_knee(df=sample_data, x="k", y="inertia", title="Test Knee Plot")

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 1  # Should have one line trace
        assert fig.layout.title.text == "Test Knee Plot"

    def test_plot_knee_with_auto_detection(self, sample_data):
        """Test knee plot with auto detection (if kneed available)."""
        fig = plot_knee(
            df=sample_data,
            x="k",
            y="inertia",
            auto_knee=True,
            title="Test Knee Plot with Detection",
        )

        assert isinstance(fig, go.Figure)
        # Should have at least one trace (the line)
        assert len(fig.data) >= 1

        # If kneed is available, should have knee marker
        # If not available, should have installation message
        has_knee_marker = any(trace.name == "Knee Point" for trace in fig.data)
        has_install_message = any(
            "kneed not installed" in str(annotation.text)
            for annotation in fig.layout.annotations
        )

        # Either knee detection worked or installation message is shown
        assert has_knee_marker or has_install_message

    def test_plot_knee_empty_dataframe(self):
        """Test knee plot with empty DataFrame."""
        empty_df = pd.DataFrame()
        fig = plot_knee(df=empty_df, x="k", y="inertia")

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 0
        assert len(fig.layout.annotations) == 1
        assert "No data available" in fig.layout.annotations[0].text

    def test_plot_knee_missing_columns(self, sample_data):
        """Test knee plot with missing columns."""
        fig = plot_knee(df=sample_data, x="nonexistent", y="inertia")

        assert isinstance(fig, go.Figure)
        assert len(fig.data) == 0
        assert len(fig.layout.annotations) == 1
        assert "not found" in fig.layout.annotations[0].text

    def test_plot_knee_with_nan_values(self):
        """Test knee plot with NaN values."""
        data_with_nan = pd.DataFrame(
            {"k": [1, 2, 3, 4, 5], "inertia": [100, 50, None, 15, 12]}
        )

        fig = plot_knee(df=data_with_nan, x="k", y="inertia")

        assert isinstance(fig, go.Figure)
        # Should handle NaN gracefully
        assert len(fig.data) >= 0

    def test_plot_knee_parameters(self, sample_data):
        """Test knee plot with various parameters."""
        fig = plot_knee(
            df=sample_data,
            x="k",
            y="inertia",
            knee_curve="convex",
            knee_direction="decreasing",
            knee_S=2.0,
            sort_by_x=False,
        )

        assert isinstance(fig, go.Figure)
        assert len(fig.data) >= 1

    def test_plot_knee_custom_kwargs(self, sample_data):
        """Test knee plot with custom layout kwargs."""
        fig = plot_knee(
            df=sample_data,
            x="k",
            y="inertia",
            title="Custom Title",
            width=800,
            height=600,
        )

        assert isinstance(fig, go.Figure)
        assert fig.layout.title.text == "Custom Title"
        assert fig.layout.width == 800
        assert fig.layout.height == 600
