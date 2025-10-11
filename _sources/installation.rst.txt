Installation
============

Dashboard Lego can be installed via pip or by cloning the repository.

Install from PyPI
-----------------

.. code-block:: bash

   pip install dashboard-lego


Install from source
-------------------

Clone the repository:

.. code-block:: bash

   git clone https://github.com/your-username/dashboard-lego.git
   cd dashboard-lego

Create a virtual environment (recommended):

.. code-block:: bash

   # Using uv (recommended)
   uv venv
   uv pip install -e .[dev]

   # Or using pip
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -e .[dev]

Requirements
------------

Dashboard Lego requires:

* Python 3.10 or higher
* Dash 2.14.0 or higher
* Plotly 5.17.0 or higher
* Pandas 2.0.0 or higher
* NumPy 1.24.0 or higher

Optional dependencies:

* scikit-learn (for ML presets)
* SQLAlchemy (for SQL data sources)
* Sphinx (for building documentation)

Verify Installation
-------------------

Test your installation:

.. code-block:: python

   import dashboard_lego
   print(f"Dashboard Lego version: {dashboard_lego.__version__}")

   # Test basic functionality
   from dashboard_lego.core.page import DashboardPage
   from dashboard_lego.blocks.kpi import KPIBlock
   print("Installation successful!")
