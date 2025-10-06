Dashboard Lego Documentation
=============================

A modular Python library for building interactive dashboards using Dash and Plotly.

Dashboard Lego allows you to build complex dashboards from independent, reusable "blocks" like building with LEGO bricks. This simplifies development, improves code readability, and promotes component reusability.

.. image:: https://img.shields.io/pypi/v/dashboard-lego.svg
   :target: https://pypi.org/project/dashboard-lego/
   :alt: PyPI version

.. image:: https://img.shields.io/pypi/pyversions/dashboard-lego.svg
   :target: https://pypi.org/project/dashboard-lego/
   :alt: Python versions

.. image:: https://img.shields.io/badge/license-MIT-blue.svg
   :target: LICENSE
   :alt: License

.. image:: https://img.shields.io/badge/code%20style-black-000000.svg
   :target: https://github.com/psf/black
   :alt: Code style: black

Key Features
------------

* **Modular Architecture**: Build dashboards from independent blocks (KPIs, charts, text)
* **Reactive State Management**: Built-in state manager for easy interactivity between blocks
* **Flexible Grid System**: Position blocks in any configuration using Bootstrap grid system
* **Data Caching**: Built-in caching at the data source level for improved performance
* **Easy Extension**: Easily create custom blocks and data sources by inheriting from base classes
* **Presets & Layouts**: Pre-built EDA and ML visualization blocks, plus layout presets
* **Comprehensive Testing**: Full test coverage with unit, integration, and performance tests

Quick Start
-----------

Install Dashboard Lego:

.. code-block:: bash

   pip install dashboard-lego

Create a simple dashboard:

.. code-block:: python

   import dash
   import dash_bootstrap_components as dbc
   import plotly.express as px
   import pandas as pd
   from dashboard_lego import DashboardPage, KPIBlock, StaticChartBlock
   from dashboard_lego.core.datasource import BaseDataSource

   # Define your data source
   class MyDataSource(BaseDataSource):
       def _load_data(self, params: dict) -> pd.DataFrame:
           return pd.read_csv("your_data.csv")

       def get_kpis(self) -> dict:
           return {"total": len(self._data)}

   # Create blocks
   kpi_block = KPIBlock(
       block_id="my_kpis",
       datasource=MyDataSource(),
       kpi_definitions=[{"key": "total", "title": "Total Records"}]
   )

   # Create dashboard
   page = DashboardPage(
       title="My Dashboard",
       blocks=[[kpi_block]]
   )

   # Run the app
   app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])
   app.layout = page.build_layout()
   page.register_callbacks(app)
   app.run_server(debug=True)

Contents
--------

.. toctree::
   :maxdepth: 2
   :caption: Getting Started

   installation
   quickstart
   concepts

.. toctree::
   :maxdepth: 2
   :caption: API Reference

   api/modules

.. toctree::
   :maxdepth: 2
   :caption: Development

   contributing

Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
