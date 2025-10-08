"""
Concrete implementation of a DataSource for SQL databases.

"""

from typing import Any, Dict, List, Optional

import pandas as pd

from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.utils.exceptions import DataLoadError
from dashboard_lego.utils.logger import get_logger

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:
    raise ImportError(
        "SQLAlchemy is required for SqlDataSource. "
        "Please install it with `pip install dashboard-lego[sql]`."
    )


class SqlDataSource(BaseDataSource):
    """
    A data source that loads data from a SQL database using SQLAlchemy.

        :hierarchy: [Feature | DataSources | SqlDataSource]
        :relates-to:
          - motivated_by: "Architectural Conclusion: Provide ready-to-use data source classes"
          - implements: "class: 'SqlDataSource'"
          - uses: ["interface: 'BaseDataSource'", "library: 'SQLAlchemy'"]

        :rationale: "Uses SQLAlchemy to provide a consistent interface to various SQL backends."
        :contract:
          - pre: "A valid SQLAlchemy connection URI and a SQL query must be provided."
          - post: "The instance holds a pandas DataFrame with the query results."

    """

    def __init__(self, connection_uri: str, query: str, **kwargs):
        """
        Initializes the SqlDataSource.

        Args:
            connection_uri: A SQLAlchemy-compatible database URI.
                            (e.g., 'sqlite:///mydatabase.db',
                            'postgresql://user:pass@host/db')
            query: The SQL query to execute to retrieve the data.
            **kwargs: Keyword arguments for the parent BaseDataSource
                     (e.g., cache_ttl).

        """
        super().__init__(**kwargs)
        self.logger = get_logger(__name__, SqlDataSource)
        self.connection_uri = connection_uri
        self.query = query

        self.logger.info(f"SQL datasource initialized for URI: {connection_uri}")
        self.logger.debug(
            f"Query: {query[:100]}..." if len(query) > 100 else f"Query: {query}"
        )

    def _load_raw_data(self, params: Optional[Dict[str, Any]] = None) -> pd.DataFrame:
        """
        Load raw data from SQL database (NO filtering).

        :hierarchy: [Core | DataSources | SqlDataSource | Load Stage]
        :relates-to:
         - motivated_by: "Refactor: Separate data loading from filtering"
         - implements: "method: '_load_raw_data'"

        :contract:
         - pre: "connection_uri is valid, query is valid SQL"
         - post: "Returns raw DataFrame from SQL query"
         - invariant: "Does NOT apply filters"

        Args:
            params: Optional dictionary of parameters to bind to the SQL query.
                   These are SQL query parameters (e.g., :param_name in query),
                   NOT filtering parameters for the DataFrame.

        Returns:
            Raw DataFrame from SQL query results

        Raises:
            DataLoadError: If connection fails or query fails

        Note:
            Filtering logic has been removed and should be handled by DataFilter.
            SQL query parameters are still supported as they affect data loading.
        """
        self.logger.debug(f"Executing SQL query with params: {params}")

        try:
            engine = create_engine(self.connection_uri)
            self.logger.debug("Database engine created successfully")

            with engine.connect() as connection:
                self.logger.debug("Database connection established")
                df = pd.read_sql(text(self.query), connection, params=params)

                self.logger.info(
                    f"SQL query executed successfully: {len(df)} rows, "
                    f"{len(df.columns)} columns"
                )

                if df.empty:
                    self.logger.warning("SQL query returned empty result set")

                return df

        except SQLAlchemyError as e:
            self.logger.error(f"SQLAlchemy error: {e}", exc_info=True)
            raise DataLoadError(f"Database error: {e}") from e
        except Exception as e:
            self.logger.error(f"Error executing SQL query: {e}", exc_info=True)
            raise DataLoadError(f"Failed to execute SQL query: {e}") from e

    def get_kpis(self) -> Dict[str, Any]:
        """
        Returns an empty dictionary. Users should subclass to implement this.

        """
        return {}

    def get_filter_options(self, filter_name: str) -> List[Dict[str, Any]]:
        """
        Returns an empty list. Users should subclass to implement this.

        """
        return []

    def get_summary(self) -> str:
        """
        Returns a basic summary of the loaded data.

        """
        if self._data is not None and not self._data.empty:
            summary = f"SQL data loaded via query. Shape: {self._data.shape}"
            self.logger.debug(f"Generated summary: {summary}")
            return summary
        self.logger.debug("No data loaded for summary")
        return "No data loaded."
