"""
SQL data source with built-in DataBuilder.

:hierarchy: [Core | DataSources | SqlDataSource]
:contract:
 - pre: "connection_uri and query provided"
 - post: "SQL data loaded and cached"

:complexity: 3
"""

import pandas as pd

from dashboard_lego.core.data_builder import DataBuilder
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.utils.exceptions import DataLoadError

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:
    raise ImportError(
        "SQLAlchemy is required for SqlDataSource. "
        "Please install it with `pip install dashboard-lego[sql]`."
    )


class SqlDataBuilder(DataBuilder):
    """
    DataBuilder for SQL databases.

    :hierarchy: [Core | DataSources | SqlDataBuilder]
    :contract:
     - pre: "connection_uri and query valid"
     - post: "Returns loaded DataFrame"
    """

    def __init__(self, connection_uri: str, query: str, **kwargs):
        super().__init__(**kwargs)
        self.connection_uri = connection_uri
        self.query = query

    def build(self, **params) -> pd.DataFrame:
        """Execute SQL query."""
        self.logger.info("[SqlDataBuilder] Executing query")
        try:
            engine = create_engine(self.connection_uri)

            with engine.connect() as connection:
                df = pd.read_sql(text(self.query), connection, params=params)
                self.logger.info(f"[SqlDataBuilder] Loaded {len(df)} rows")
                return df

        except SQLAlchemyError as e:
            self.logger.error(f"SQLAlchemy error: {e}")
            raise DataLoadError(f"Database error: {e}") from e
        except Exception as e:
            self.logger.error(f"Error executing SQL query: {e}")
            raise DataLoadError(f"Failed to execute SQL query: {e}") from e


class SqlDataSource(DataSource):
    """
    SQL data source.

    :hierarchy: [Core | DataSources | SqlDataSource]
    :complexity: 3
    """

    def __init__(self, connection_uri: str, query: str, **kwargs):
        """
        Initialize SQL datasource.

        Args:
            connection_uri: SQLAlchemy connection URI
            query: SQL query to execute
        """
        # Create builder
        builder = SqlDataBuilder(connection_uri, query)

        # Pass to parent
        super().__init__(data_builder=builder, **kwargs)
