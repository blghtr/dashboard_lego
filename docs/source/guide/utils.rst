.. _guide-utils:

Utils Module API
================

Utility functions and classes for logging, exceptions, and formatting.

.. contents::
   :local:

Exception Hierarchy
-------------------

**Location:** ``dashboard_lego.utils.exceptions``

Custom exception hierarchy for error handling.

.. code-block:: text

   DashboardLegoError (base)
   ├── DataSourceError
   │   ├── DataLoadError
   │   └── CacheError
   ├── BlockError
   ├── StateError
   └── ConfigurationError

**Usage:**

.. code-block:: python

   from dashboard_lego.utils.exceptions import (
       DashboardLegoError,
       DataLoadError,
       ConfigurationError
   )

   try:
       datasource.init_data()
   except DataLoadError as e:
       logger.error(f"Failed to load data: {e}")
   except DashboardLegoError as e:
       logger.error(f"Dashboard error: {e}")

Logger
------

**Location:** ``dashboard_lego.utils.logger``

Logging configuration and utilities.

.. code-block:: python

   from dashboard_lego.utils.logger import get_logger

   # Get logger for module
   logger = get_logger(__name__, MyClass)

   # Logging levels
   logger.debug("Detailed information")
   logger.info("General information")
   logger.warning("Warning message")
   logger.error("Error message", exc_info=True)

Formatting
----------

**Location:** ``dashboard_lego.utils.formatting``

Data formatting utilities.

.. code-block:: python

   from dashboard_lego.utils.formatting import format_number

   # Automatic formatting with K/M/B suffixes
   format_number(1234)        # "1.23K"
   format_number(1234567)     # "1.23M"
   format_number(1234567890)  # "1.23B"
   format_number(123.45)      # "123"
   format_number(0.1234)      # "0.12"

For detailed documentation, see :ref:`api-utils`.
