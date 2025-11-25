"""
SQL data source with built-in DataBuilder.

:hierarchy: [Core | DataSources | SqlDataSource]
:contract:
 - pre: "connection_uri and query provided"
 - post: "SQL data loaded and cached"

:complexity: 3
"""

import pandas as pd
import sqlparse

from dashboard_lego.core.data_builder import DataBuilder
from dashboard_lego.core.datasource import DataSource
from dashboard_lego.core.exceptions import DataLoadError
from dashboard_lego.utils.logger import get_logger

try:
    from sqlalchemy import create_engine, text
    from sqlalchemy.exc import SQLAlchemyError
except ImportError:
    raise ImportError(
        "SQLAlchemy is required for SqlDataSource. "
        "Please install it with `pip install dashboard-lego[sql]`."
    )


def validate_sql_query(query: str, allowed_statements: list[str] | None = None) -> None:
    """
    Validate SQL query to prevent dangerous operations.

    :hierarchy: [Core | DataSources | Security | ValidateSQL]
    :relates-to:
     - motivated_by: "Security: Prevent SQL injection and dangerous operations"
     - implements: "function: 'validate_sql_query'"
     - uses: ["library: 'sqlparse'"]

    :rationale: "Only allow SELECT statements by default to prevent data modification."
    :contract:
     - pre: "query is a non-empty string"
     - post: "Raises DataLoadError if query contains dangerous operations"
     - invariant: "Only SELECT statements are allowed by default"

    Args:
        query: SQL query string to validate
        allowed_statements: List of allowed statement types (default: ['SELECT'])

    Raises:
        DataLoadError: If query contains dangerous operations or invalid SQL
    """
    logger = get_logger(__name__)
    logger.debug(f"[Security|SQL] Validating SQL query: {query[:100]}...")

    if allowed_statements is None:
        allowed_statements = ["SELECT"]

    # Dangerous operations that should never be allowed
    dangerous_operations = {
        "DROP",
        "DELETE",
        "UPDATE",
        "ALTER",
        "CREATE",
        "TRUNCATE",
        "INSERT",
        "GRANT",
        "REVOKE",
        "EXEC",
        "EXECUTE",
    }

    try:
        # Parse SQL query
        parsed_statements = sqlparse.parse(query)
        if not parsed_statements:
            raise DataLoadError("Empty SQL query provided")

        # Validate each statement
        for stmt in parsed_statements:
            statement_type = stmt.get_type()

            # Check if statement type is dangerous
            if statement_type in dangerous_operations:
                logger.warning(
                    f"[Security|SQL] Blocked dangerous operation: {statement_type}"
                )
                raise DataLoadError(
                    f"Dangerous SQL operation '{statement_type}' is not allowed. "
                    f"Only SELECT queries are permitted."
                )

            # Check if statement type is in allowed list
            if statement_type not in allowed_statements:
                if statement_type == "UNKNOWN":
                    logger.warning(
                        "[Security|SQL] Unknown statement type - blocking for safety"
                    )
                    raise DataLoadError(
                        "Unknown SQL statement type detected. "
                        "Only SELECT queries are permitted."
                    )
                else:
                    logger.warning(
                        f"[Security|SQL] Blocked non-allowed statement: {statement_type}"
                    )
                    raise DataLoadError(
                        f"SQL statement type '{statement_type}' is not allowed. "
                        f"Allowed types: {', '.join(allowed_statements)}"
                    )

        logger.debug("[Security|SQL] SQL query validation passed")

    except DataLoadError:
        # Re-raise DataLoadError as-is
        raise
    except Exception as e:
        logger.error(f"[Security|SQL] SQL validation error: {e}")
        raise DataLoadError(f"Invalid SQL query provided: {e}") from e


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

    def _build(self, **kwargs) -> pd.DataFrame:
        """Execute SQL query."""
        self.logger.info("[SqlDataBuilder] Executing query")
        try:
            engine = create_engine(self.connection_uri)

            with engine.connect() as connection:
                df = pd.read_sql(text(self.query), connection, params=kwargs)
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

    def __init__(
        self,
        connection_uri: str,
        query: str,
        allowed_statements: list[str] | None = None,
        **kwargs,
    ):
        """
        Initialize SQL datasource.

        Args:
            connection_uri: SQLAlchemy connection URI
            query: SQL query to execute
            allowed_statements: List of allowed statement types (default: ['SELECT'])
            **kwargs: Additional arguments passed to DataSource

        Raises:
            DataLoadError: If query contains dangerous operations or invalid SQL
        """
        # Validate query for security
        validate_sql_query(query, allowed_statements=allowed_statements)

        # Create builder
        builder = SqlDataBuilder(connection_uri, query)

        # Pass to parent
        super().__init__(data_builder=builder, **kwargs)
