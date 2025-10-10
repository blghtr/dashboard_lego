.. _guide-datasources:

DataSources Module API
======================

Pre-built data source implementations for common data formats.

.. contents::
   :local:

CsvDataSource
-------------

**Location:** ``dashboard_lego.core.datasources.csv_source``

Load data from CSV files with automatic caching.

**Constructor:**

.. code-block:: python

   def __init__(
       self,
       file_path: str,
       read_csv_options: Optional[Dict[str, Any]] = None,
       cache_dir: Optional[str] = None,
       cache_ttl: int = 300,
       **kwargs
   )

**Example:**

.. code-block:: python

   from dashboard_lego.core.datasources.csv_source import CsvDataSource

   datasource = CsvDataSource(
       file_path="data/sales.csv",
       read_csv_options={"parse_dates": ["Date"]},
       cache_ttl=600  # 10 minutes
   )
   datasource.init_data()

ParquetDataSource
-----------------

**Location:** ``dashboard_lego.core.datasources.parquet_source``

High-performance columnar data loading.

**Constructor:**

.. code-block:: python

   def __init__(
       self,
       file_path: str,
       read_parquet_options: Optional[Dict[str, Any]] = None,
       cache_dir: Optional[str] = None,
       cache_ttl: int = 300,
       **kwargs
   )

**Example:**

.. code-block:: python

   from dashboard_lego.core.datasources.parquet_source import ParquetDataSource

   datasource = ParquetDataSource(
       file_path="data/large_dataset.parquet",
       read_parquet_options={"columns": ["Date", "Sales", "Region"]}
   )
   datasource.init_data()

SqlDataSource
-------------

**Location:** ``dashboard_lego.core.datasources.sql_source``

Database connectivity via SQLAlchemy.

**Constructor:**

.. code-block:: python

   def __init__(
       self,
       connection_string: str,
       query: str,
       cache_dir: Optional[str] = None,
       cache_ttl: int = 300,
       **kwargs
   )

**Connection String Examples:**

.. code-block:: python

   # PostgreSQL
   "postgresql://user:password@localhost:5432/dbname"

   # MySQL
   "mysql+pymysql://user:password@localhost:3306/dbname"

   # SQLite
   "sqlite:///path/to/database.db"

**Example:**

.. code-block:: python

   from dashboard_lego.core.datasources.sql_source import SqlDataSource

   datasource = SqlDataSource(
       connection_string="postgresql://user:pass@localhost/sales_db",
       query="SELECT * FROM sales WHERE year = 2024",
       cache_ttl=1800  # 30 minutes
   )
   datasource.init_data()
