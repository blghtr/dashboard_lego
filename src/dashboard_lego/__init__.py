"""
Dashboard Lego - A modular library for creating interactive dashboards.

This package provides a framework for building data visualization dashboards
using Dash and Plotly with a modular block-based architecture.
"""

# Import core modules to make them available at package level
from . import blocks, core, presets, utils

__all__ = ["blocks", "core", "presets", "utils"]
