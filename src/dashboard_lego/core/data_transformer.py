"""
This module defines DataTransformer for data transformation operations.

Renamed from DataFilter in v0.15 for semantic clarity.

:hierarchy: [Core | DataSources | DataTransformer]
:relates-to:
 - motivated_by: "v0.15: Broader contract for filter/aggregate/reshape operations"
 - implements: "class: 'DataTransformer'"

:contract:
 - pre: "Receives built DataFrame and transformation params"
 - post: "Returns transformed DataFrame (any shape/structure allowed)"
 - invariant: "Input DataFrame not modified (copy-on-write)"
 - capability: "Filter, aggregate, pivot, reshape, any df→df transformation"

:complexity: 2
:decision_cache: "Renamed DataFilter→DataTransformer for semantic accuracy"
"""

import logging
from typing import Optional

import pandas as pd

from dashboard_lego.utils.logger import get_logger


class DataTransformer:
    """
    Handles data transformation operations in the data pipeline.

    Renamed from DataFilter in v0.15 for broader contract.

    This class is responsible for ANY DataFrame transformation:
    - Filtering (subsetting rows)
    - Aggregation (groupby, value_counts, pivot)
    - Reshaping (melt, pivot_table)
    - Feature engineering (add/remove columns)
    - Any df→df operation

    :hierarchy: [Core | DataSources | DataTransformer]
    :relates-to:
     - motivated_by: "v0.15: Generic transformation stage for flexible data prep"
     - implements: "class: 'DataTransformer'"

    :contract:
     - pre: "transform() receives valid DataFrame and params dict"
     - post: "transform() returns transformed DataFrame (any shape allowed)"
     - invariant: "Input DataFrame not modified (copy-on-write)"

    :complexity: 2
    :decision_cache: "Broader contract than DataFilter for aggregations/reshaping"

    Example:
        >>> # Filtering (original DataFilter use case)
        >>> class CategoryFilter(DataTransformer):
        ...     def transform(self, data, params):
        ...         df = data.copy()
        ...         if 'category' in params:
        ...             df = df[df['Category'] == params['category']]
        ...         return df

        >>> # Aggregation (new use case)
        >>> class AggregateByCategory(DataTransformer):
        ...     def transform(self, data, params):
        ...         return data.groupby('Category').size().reset_index(name='count')
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize DataTransformer.

        :hierarchy: [Core | DataSources | DataTransformer | Initialization]
        :relates-to:
         - motivated_by: "Configurable logger for debugging"
         - implements: "method: '__init__'"

        :contract:
         - pre: "logger can be None or valid Logger instance"
         - post: "DataTransformer ready to transform data"

        Args:
            logger: Optional logger instance. If None, creates default logger.
        """
        self.logger = logger or get_logger(__name__, DataTransformer)
        self.logger.debug("DataTransformer initialized")

    def transform(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Transform data based on params.

        :hierarchy: [Core | DataSources | DataTransformer | Transform]
        :relates-to:
         - motivated_by: "Generic transformation interface (filter/aggregate/reshape)"
         - implements: "method: 'transform'"

        :contract:
         - pre: "data is valid DataFrame"
         - post: "Returns transformed DataFrame (any shape/structure allowed)"
         - invariant: "Does not modify input DataFrame"

        This method provides state protection wrapper around _transform().
        Override _transform() in subclass to implement transformation logic.

        Args:
            data: Built DataFrame to transform
            **kwargs: Transformation parameters

        Returns:
            Transformed DataFrame (can be filtered, aggregated, reshaped, etc.)

        Example:
            >>> class PriceFilter(DataTransformer):
            ...     def _transform(self, data, params):
            ...         df = data.copy()
            ...         if 'min_price' in params:
            ...             df = df[df['Price'] >= params['min_price']]
            ...         return df
        """
        # State protection: Reset any mutable state before transforming
        self._reset_mutable_state()

        # Call the actual transform implementation
        return self._transform(data, **kwargs)

    def _reset_mutable_state(self) -> None:
        """
        Reset mutable state to prevent accumulation across transforms.

        Override in subclass to reset any mutable instance variables.
        Called automatically before each transform().

        :hierarchy: [Core | DataSources | DataTransformer | StateProtection]
        :contract:
         - pre: "Transformer has mutable state"
         - post: "All mutable state reset to initial state"
         - invariant: "Called before every transform()"

        Example:
            >>> class MyTransformer(DataTransformer):
            ...     def __init__(self):
            ...         super().__init__()
            ...         self._cache = {}
            ...         self._accumulator = []
            ...
            ...     def _reset_mutable_state(self):
            ...         self._cache = {}  # Reset cache
            ...         self._accumulator = []  # Reset accumulator
        """
        # Default: no-op (no mutable state to reset)
        pass

    def _transform(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Abstract transform implementation.

        Override this method in subclass to implement transformation logic.
        This method is called by transform() after state reset.

        :hierarchy: [Core | DataSources | DataTransformer | TransformImplementation]
        :contract:
         - pre: "Mutable state has been reset"
         - post: "Returns transformed DataFrame (any shape/structure allowed)"
         - invariant: "Pure function (no side effects on instance state)"

        Args:
            data: Built DataFrame to transform
            **kwargs: Transformation parameters

        Returns:
            Transformed DataFrame (can be filtered, aggregated, reshaped, etc.)
        """
        self.logger.debug(
            f"[DataTransformer|_Transform] Transforming {len(data)} rows with kwargs: {list(kwargs.keys())}"
        )

        # Default: no transformation, return data as-is
        self.logger.debug(
            "[DataTransformer|_Transform] Using default implementation (no transformation)"
        )
        return data


def _apply_column_filters(
    df: pd.DataFrame, logger: logging.Logger, **kwargs
) -> pd.DataFrame:
    """
    Apply column-based filters to DataFrame.

    Filters DataFrame by matching kwargs to column names. Builds combined
    boolean mask for all filters and applies once. Handles numeric type
    conversion and skips None/'all' values.

    :hierarchy: [Core | DataSources | DataTransformer | FilterUtility]
    :relates-to:
     - motivated_by: "Extracted filter logic for reuse in DataFilter and DfHandler to avoid code duplication [decision-filter-extract-001]"
     - implements: "function: '_apply_column_filters'"
     - uses: ["pandas.Series: boolean mask construction", "pandas.api.types: dtype checking"]
     - enables: ["DataFilter._transform: uses this for filtering", "DfHandler._build: uses this for filtering"]

    :contract:
     - pre: "df is valid DataFrame, logger is valid Logger instance, kwargs contains filter parameters"
     - post: "Returns filtered DataFrame with rows matching all filter conditions (AND logic)"
     - invariant: "Does not modify input DataFrame (works on copy), skips params not in columns, skips None/'all' values, handles numeric conversion gracefully"

    :complexity: 5
    :decision_cache: "Extracted to standalone function for reuse: avoids duplication between DataFilter and DfHandler, maintains single source of truth for filter logic [decision-filter-extract-001]"

    Args:
        df: Input DataFrame to filter
        logger: Logger instance for warnings
        **kwargs: Filter parameters (key=column_name, value=filter_value)

    Returns:
        Filtered DataFrame with rows matching all filter conditions

    Example:
        >>> df = pd.DataFrame({'A': [1, 2, 3], 'B': ['x', 'y', 'z']})
        >>> logger = logging.getLogger(__name__)
        >>> filtered = _apply_column_filters(df, logger, A=2, B='y')
        >>> len(filtered)
        1
    """
    df_copy = df.copy()

    # Build combined boolean mask for all filters
    mask = pd.Series(True, index=df_copy.index)

    for key, value in kwargs.items():
        # Skip special params or those not in columns
        if key not in df_copy.columns:
            # Log warning if it looks like a filter param (no double underscore)
            if "__" not in key:
                logger.warning(f"[DataFilter] Param '{key}' not in columns, ignoring")
            continue

        # Skip None or 'all'
        if value is None or value == "all":
            continue

        # Build filter condition for this param
        try:
            # Handle numeric type conversion if needed
            col_type = df_copy[key].dtype
            filter_value = value

            if pd.api.types.is_numeric_dtype(col_type) and isinstance(value, str):
                try:
                    if "." in value:
                        filter_value = float(value)
                    else:
                        filter_value = int(value)
                except ValueError:
                    # Keep as string if conversion fails
                    pass

            # Combine with existing mask using AND
            mask = mask & (df_copy[key] == filter_value)
        except Exception as e:
            logger.warning(f"[DataFilter] Failed to filter by {key}={value}: {e}")

    # Apply combined mask once
    return df_copy[mask]


class DataFilter(DataTransformer):
    """
    Transformer that filters DataFrame based on parameters matching column names.

    Renamed from DataFilter in v0.15 for semantic clarity.

    :hierarchy: [Core | DataSources | DataFilter]
    :relates-to:
     - motivated_by: "Provide default filtering capability based on params"
     - implements: "class: 'DataFilter'"

    :contract:
     - pre: "Receives DataFrame and params"
     - post: "Returns DataFrame filtered by params that match column names"
     - invariant: "Ignores params that don't match columns or are None/'all'"
    """

    def _transform(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Filter data by matching params to columns.

        Uses extracted _apply_column_filters() function for filtering logic.

        Args:
            data: Input DataFrame
            **kwargs: Filter parameters

        Returns:
            Filtered DataFrame
        """
        return _apply_column_filters(data, self.logger, **kwargs)


class ChainedTransformer(DataTransformer):
    """
    A transformer that applies multiple transformers in sequence.

    Enables composition of transformation logic by chaining two transformers.
    First transformer receives params, second receives empty dict.

    :hierarchy: [Core | DataSources | ChainedTransformer]
    :relates-to:
     - motivated_by: "v0.15.0: Block-specific transforms after global filters"
     - implements: "class: 'ChainedTransformer'"
     - uses: ["class: 'DataTransformer'"]

    :contract:
     - pre: "transformer_1 and transformer_2 are DataTransformer instances"
     - post: "transform() applies transformers sequentially"
     - invariant: "First gets params, second gets empty dict"

    :complexity: 3
    :decision_cache: "Sequential application preserves global filter → block transform order"

    Example:
        >>> global_filter = CategoryFilter()
        >>> block_transform = AggregateTransformer()
        >>> chained = ChainedTransformer(global_filter, block_transform)
        >>> result = chained.transform(data, {'category': 'A'})
        # First filters to category A, then aggregates
    """

    def __init__(
        self,
        transformer_1: DataTransformer,
        transformer_2: DataTransformer,
        logger: Optional[logging.Logger] = None,
    ):
        """
        Initialize ChainedTransformer with two transformers.

        :hierarchy: [Core | DataSources | ChainedTransformer | Initialization]
        :relates-to:
         - motivated_by: "Compose transformation pipeline"
         - implements: "method: '__init__'"

        :contract:
         - pre: "Both transformers are DataTransformer instances"
         - post: "ChainedTransformer ready to apply sequential transforms"

        :complexity: 1

        Args:
            transformer_1: First transformer in chain (receives params)
            transformer_2: Second transformer in chain (receives empty dict)
            logger: Optional logger instance
        """
        super().__init__(logger=logger)
        self.transformer_1 = transformer_1
        self.transformer_2 = transformer_2
        self.logger.debug(
            f"[ChainedTransformer|Init] Chain: {type(transformer_1).__name__} → "
            f"{type(transformer_2).__name__}"
        )

    def _transform(self, data: pd.DataFrame, **kwargs) -> pd.DataFrame:
        """
        Apply transformers sequentially.

        First transformer receives params (global filters), second receives
        empty dict (block-specific transform doesn't need params).

        :hierarchy: [Core | DataSources | ChainedTransformer | Transform]
        :relates-to:
         - motivated_by: "Sequential transformation preserves order"
         - implements: "method: '_transform'"

        :contract:
         - pre: "data is valid DataFrame, params is dict"
         - post: "Returns result of transformer_2(transformer_1(data, params), {})"
         - invariant: "transformer_1 gets params, transformer_2 gets empty dict"

        :complexity: 2
        :decision_cache: "Params only for first transformer (global filter)"

        Args:
            data: Input DataFrame
            params: Parameters for first transformer (global filters)

        Returns:
            DataFrame after both transformations applied

        Example:
            >>> # Step 1: Apply global filter with params
            >>> filtered = transformer_1.transform(data, {'category': 'A'})
            >>> # Step 2: Apply block-specific transform (no params)
            >>> final = transformer_2.transform(filtered, {})
        """
        self.logger.debug(
            f"[ChainedTransformer|_Transform] Starting chain | "
            f"input_rows={len(data)} | params={list(kwargs.keys())}"
        )

        # Step 1: Apply the global filter with its params
        filtered_data = self.transformer_1.transform(data, **kwargs)
        self.logger.debug(
            f"[ChainedTransformer|_Transform] After transformer_1: {len(filtered_data)} rows"
        )

        # Step 2: Apply the block-specific transform (it does not need params)
        final_data = self.transformer_2.transform(filtered_data)
        self.logger.debug(
            f"[ChainedTransformer|_Transform] After transformer_2: {len(final_data)} rows"
        )

        return final_data
