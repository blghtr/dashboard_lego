"""
This module defines the DataFilter for data filtering operations.

:hierarchy: [Core | DataSources | DataFilter]
:relates-to:
 - motivated_by: "Refactor: Separate filtering logic from preprocessing for independent control"
 - implements: "class: 'DataFilter'"
 - uses: []

:contract:
 - pre: "Receives preprocessed DataFrame and filtering params"
 - post: "Returns filtered subset of DataFrame"
 - invariant: "Filtering never adds rows, only removes them"

:complexity: 2
:decision_cache: "Chose base class pattern for extensibility via inheritance"
"""

import logging
from typing import Any, Dict, Optional

import pandas as pd

from dashboard_lego.utils.logger import get_logger


class DataFilter:
    """
    Handles data filtering operations in the data pipeline.

    This class is responsible for subsetting data based on user-defined criteria,
    such as:
    - Column value filters (category == 'X')
    - Range filters (price between min and max)
    - Date range filters
    - Search/text filters
    - Boolean conditions

    :hierarchy: [Core | DataSources | DataFilter]
    :relates-to:
     - motivated_by: "Need to separate filtering from preprocessing for independent caching"
     - implements: "class: 'DataFilter'"

    :contract:
     - pre: "filter() receives valid DataFrame and params dict"
     - post: "filter() returns filtered DataFrame (subset of input)"
     - invariant: "Filtering never adds rows; output rows ≤ input rows"

    :complexity: 2
    :decision_cache: "Chose inheritance-based extensibility over composition"

    Example:
        >>> class CategoryFilter(DataFilter):
        ...     def filter(self, data, params):
        ...         df = data.copy()
        ...         if 'category' in params and params['category']:
        ...             df = df[df['Category'] == params['category']]
        ...         return df
        >>>
        >>> data_filter = CategoryFilter()
        >>> filtered_df = data_filter.filter(preprocessed_df, {'category': 'Electronics'})
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize DataFilter.

        :hierarchy: [Core | DataSources | DataFilter | Initialization]
        :relates-to:
         - motivated_by: "Need configurable logger for debugging"
         - implements: "method: '__init__'"

        :contract:
         - pre: "logger can be None or valid Logger instance"
         - post: "DataFilter is ready to filter data"

        Args:
            logger: Optional logger instance. If None, creates default logger.
        """
        self.logger = logger or get_logger(__name__, DataFilter)
        self.logger.debug("DataFilter initialized")

    def filter(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Filter data based on params.

        :hierarchy: [Core | DataSources | DataFilter | Filter]
        :relates-to:
         - motivated_by: "Core filtering interface for pipeline"
         - implements: "method: 'filter'"

        :contract:
         - pre: "data is valid DataFrame, params is dict"
         - post: "Returns filtered DataFrame where len(output) <= len(input)"
         - invariant: "Does not modify input DataFrame"

        :complexity: 1
        :decision_cache: "Default implementation returns unchanged data for backward compatibility"

        Args:
            data: Preprocessed DataFrame to filter
            params: Filtering parameters that define subset criteria
                   (these come from filtering_params in DataProcessingContext)

        Returns:
            Filtered DataFrame (subset of input)

        Note:
            Override this method in subclasses for custom filtering logic.
            The default implementation returns data unchanged.
            Always work on a copy of the data to avoid modifying the original.

        Example:
            >>> class PriceRangeFilter(DataFilter):
            ...     def filter(self, data, params):
            ...         df = data.copy()
            ...         if 'min_price' in params and params['min_price']:
            ...             df = df[df['Price'] >= params['min_price']]
            ...         if 'max_price' in params and params['max_price']:
            ...             df = df[df['Price'] <= params['max_price']]
            ...         return df
        """
        self.logger.debug(
            f"[DataFilter] Filtering {len(data)} rows with params: {list(params.keys())}"
        )

        # Default: no filtering, return data as-is
        self.logger.debug("[DataFilter] Using default implementation (no filtering)")
        return data
