"""
Concrete implementation of a DataSource for SQL databases.

"""
from typing import Any, Dict, List, Optional
import pandas as pd

from core.datasource import BaseDataSource

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
    def __init__(self, connection_uri: str, query: str):
        """
        Initializes the SqlDataSource.

        Args:
            connection_uri: A SQLAlchemy-compatible database URI.
                            (e.g., 'sqlite:///mydatabase.db', 'postgresql://user:pass@host/db')
            query: The SQL query to execute to retrieve the data.

        """
        self.connection_uri = connection_uri
        self.query = query
        self._data: Optional[pd.DataFrame] = None

    def init_data(self, params: Optional[Dict[str, Any]] = None) -> bool:
        """
        Loads data from the database by executing the query.

        Args:
            params: Optional dictionary of parameters to bind to the SQL query.

        Returns:
            True if data was loaded successfully, False otherwise.

        """
        try:
            engine = create_engine(self.connection_uri)
            with engine.connect() as connection:
                self._data = pd.read_sql(text(self.query), connection, params=params)
            return True
        except SQLAlchemyError as e:
            print(f"An error occurred while connecting to the database or executing the query: {e}")
            self._data = pd.DataFrame()
            return False
        except Exception as e:
            print(f"An unexpected error occurred: {e}")
            self._data = pd.DataFrame()
            return False

    def get_processed_data(self) -> pd.DataFrame:
        """
        Returns the loaded DataFrame.

        """
        if self._data is None:
            if not self.init_data():
                return pd.DataFrame()
        return self._data

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
            return f"SQL data loaded via query. Shape: {self._data.shape}"
        return "No data loaded."
