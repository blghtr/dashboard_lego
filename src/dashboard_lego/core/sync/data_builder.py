"""
DataBuilder - Complete data construction before filtering.

Handles ALL data preparation BEFORE filtering stage:
- Data loading from source
- Data transformation
- Feature engineering
- Aggregations
- Joins

:hierarchy: [Core | Pipeline | DataBuilder]
:relates-to:
 - motivated_by: "v0.15.0: Semantic clarity - builder constructs complete dataset"
 - implements: "class: 'DataBuilder'"

:contract:
 - pre: "build(params) receives construction parameters"
 - post: "Returns complete DataFrame ready for filtering"
 - responsibility: "Load + Process (everything BEFORE filters)"

:complexity: 3
:decision_cache: "DataBuilder name semantically correct - builds complete dataset"
"""

import logging
from typing import Optional

import pandas as pd

from dashboard_lego.core.data_transformer import _apply_column_filters
from dashboard_lego.utils.logger import get_logger


class DataBuilder:
    """
    Base class for data construction.

    Combines loading and processing into single stage.

    :hierarchy: [Core | Pipeline | DataBuilder]
    :contract:
     - pre: "build(params) receives params"
     - post: "Returns complete built DataFrame"
     - invariant: "Deterministic (same params → same output)"

    :complexity: 2
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize DataBuilder.

        :hierarchy: [Core | Pipeline | DataBuilder | Init]
        :contract:
         - pre: "logger optional"
         - post: "Builder ready"

        Args:
            logger: Optional logger instance
        """
        self.logger = logger or get_logger(__name__, DataBuilder)
        self.logger.info("[DataBuilder|Init] Initialized")

    def build(self, **kwargs) -> pd.DataFrame:
        """
        Build complete dataset (load + process).

        :hierarchy: [Core | Pipeline | DataBuilder | Build]
        :contract:
         - pre: -
         - post: "Returns complete DataFrame ready for filtering"
         - invariant: "Same params → same output"

        This method provides state protection wrapper around _build().
        Override _build() in subclass to implement building logic.

        Args:
            params: Construction parameters
                   Examples: file paths, SQL queries, transformations

        Returns:
            Complete built DataFrame

        Example:
            >>> class SalesDataBuilder(DataBuilder):
            ...     def __init__(self, file_path, **kwargs):
            ...         super().__init__(**kwargs)
            ...         self.file_path = file_path
            ...
            ...     def _build(self, params):
            ...         # Load
            ...         df = pd.read_csv(self.file_path)
            ...         # Process
            ...         df['Revenue'] = df['Price'] * df['Quantity']
            ...         return df
        """
        # State protection: Reset any mutable state before building
        self._reset_mutable_state()

        # Call the actual build implementation
        return self._build(**kwargs)

    def _reset_mutable_state(self) -> None:
        """
        Reset mutable state to prevent accumulation across builds.

        Override in subclass to reset any mutable instance variables.
        Called automatically before each build().

        :hierarchy: [Core | Pipeline | DataBuilder | StateProtection]
        :contract:
         - pre: "Builder has mutable state"
         - post: "All mutable state reset to initial state"
         - invariant: "Called before every build()"

        Example:
            >>> class MyBuilder(DataBuilder):
            ...     def __init__(self):
            ...         super().__init__()
            ...         self._rows = []
            ...         self._cache = {}
            ...
            ...     def _reset_mutable_state(self):
            ...         self._rows = []  # Reset accumulation
            ...         self._cache = {}  # Reset cache
        """
        # Default: no-op (no mutable state to reset)
        pass

    def _build(self, **kwargs) -> pd.DataFrame:
        """
        Abstract build implementation.

        Override this method in subclass to implement building logic.
        This method is called by build() after state reset.

        :hierarchy: [Core | Pipeline | DataBuilder | BuildImplementation]
        :contract:
         - pre: "Mutable state has been reset"
         - post: "Returns complete DataFrame ready for filtering"
         - invariant: "Pure function (no side effects on instance state)"

        Args:
            params: Construction parameters

        Returns:
            Complete built DataFrame
        """
        self.logger.debug("[DataBuilder|_Build] No-op builder (empty DataFrame)")
        return pd.DataFrame()


# LLM:METADATA
# :hierarchy: [Core | Pipeline | DataBuilder | DfHandler]
# :relates-to:
#  - motivated_by: "Default DataBuilder that wraps existing DataFrame and applies column-based filtering similar to DataFilter, enabling direct DataFrame usage in pipeline without custom builder implementation [decision-dfhandler-001]"
#  - implements: "class: 'DfHandler'"
#  - uses: [
#      "_apply_column_filters: column-based filtering logic extracted from DataFilter for reuse",
#      "pandas.DataFrame: stores DataFrame copy in instance"
#  ]
#  - enables: [
#      "DataSource: can use DfHandler for quick DataFrame wrapping with filtering capability",
#      "QuickDashboard: simplified builder for in-memory DataFrames with filter support"
#  ]
# :contract:
#  - pre: "df parameter in __init__ is valid pandas DataFrame, kwargs in _build() contain filter parameters matching column names"
#  - post: "build() returns filtered DataFrame based on kwargs matching column names, or original DataFrame if no filters applied"
#  - invariant: "Does not modify stored DataFrame (works on copy), same filtering behavior as DataFilter, deterministic (same kwargs → same output)"
#  - spec_compliance: "Follows DataBuilder contract: builds complete DataFrame ready for filtering (in this case, applies filters during build)"
# :complexity: 3
# :decision_cache: "DfHandler reuses _apply_column_filters for consistency with DataFilter behavior, avoids code duplication, provides default builder for DataFrame wrapping [decision-dfhandler-001]"
# LLM:END
class DfHandler(DataBuilder):
    """
    Default DataBuilder that wraps DataFrame and applies column-based filtering.

    Similar to InMemoryDataBuilder but with filtering capability. Accepts
    DataFrame in constructor and applies filters during build() based on
    kwargs matching column names.

    :hierarchy: [Core | Pipeline | DataBuilder | DfHandler]
    :relates-to:
     - motivated_by: "Default builder for DataFrame wrapping with filter support"
     - implements: "class: 'DfHandler'"

    :contract:
     - pre: "df is valid DataFrame"
     - post: "build() returns filtered DataFrame"
     - invariant: "Does not modify stored DataFrame"

    Example:
        >>> df = pd.DataFrame({'Category': ['A', 'B', 'A'], 'Value': [1, 2, 3]})
        >>> builder = DfHandler(df)
        >>> filtered = builder.build(Category='A')
        >>> len(filtered)
        2
    """

    def __init__(self, df: pd.DataFrame, logger: Optional[logging.Logger] = None):
        """
        Initialize DfHandler with DataFrame.

        :hierarchy: [Core | Pipeline | DataBuilder | DfHandler | Initialization]
        :relates-to:
         - motivated_by: "Store DataFrame for filtering during build"
         - implements: "method: '__init__'"

        :contract:
         - pre: "df is valid pandas DataFrame"
         - post: "DfHandler ready with stored DataFrame copy"

        Args:
            df: DataFrame to wrap and filter
            logger: Optional logger instance
        """
        super().__init__(logger=logger)
        if df is None or not isinstance(df, pd.DataFrame):
            raise ValueError("df must be a valid pandas DataFrame")
        if df.empty:
            self.logger.warning("[DfHandler] Empty DataFrame provided")

        self._df = df.copy()  # Copy to avoid external mutations
        self.logger.debug(
            f"[DfHandler|Init] Initialized | rows={len(df)} | cols={len(df.columns)}"
        )

    def _build(self, **kwargs) -> pd.DataFrame:
        """
        Return filtered DataFrame based on kwargs matching column names.

        Applies column-based filtering using _apply_column_filters() function,
        same logic as DataFilter._transform().

        :hierarchy: [Core | Pipeline | DataBuilder | DfHandler | Build]
        :relates-to:
         - motivated_by: "Apply filters during build stage using extracted filter logic"
         - implements: "method: '_build'"
         - uses: ["_apply_column_filters: column-based filtering function"]

        :contract:
         - pre: "kwargs contains filter parameters (key=column_name, value=filter_value)"
         - post: "Returns filtered DataFrame with rows matching all filter conditions"
         - invariant: "Does not modify stored DataFrame, uses copy for filtering"

        Args:
            **kwargs: Filter parameters matching column names

        Returns:
            Filtered DataFrame based on kwargs

        Example:
            >>> df = pd.DataFrame({'A': [1, 2, 3], 'B': ['x', 'y', 'z']})
            >>> builder = DfHandler(df)
            >>> filtered = builder.build(A=2, B='y')
            >>> len(filtered)
            1
        """
        self.logger.debug(
            f"[DfHandler|_Build] Filtering DataFrame | "
            f"rows={len(self._df)} | filters={list(kwargs.keys())}"
        )
        return _apply_column_filters(self._df, self.logger, **kwargs)
