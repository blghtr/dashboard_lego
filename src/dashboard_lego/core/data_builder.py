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
