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
from typing import Any, Dict, Optional

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

    def transform(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Transform data based on params.

        :hierarchy: [Core | DataSources | DataTransformer | Transform]
        :relates-to:
         - motivated_by: "Generic transformation interface (filter/aggregate/reshape)"
         - implements: "method: 'transform'"

        :contract:
         - pre: "data is valid DataFrame, params is dict"
         - post: "Returns transformed DataFrame (any shape/structure allowed)"
         - invariant: "Does not modify input DataFrame"

        :complexity: 1
        :decision_cache: "Clean contract for any df→df transformation"

        Args:
            data: Built DataFrame to transform
            params: Transformation parameters
                   (from transform_params in DataProcessingContext)

        Returns:
            Transformed DataFrame (can be filtered, aggregated, reshaped, etc.)

        Note:
            Override this method in subclasses for custom transformation logic.
            Default implementation returns data unchanged.
            Always work on a copy to avoid modifying the original.

        Examples:
            >>> # Filtering
            >>> class PriceFilter(DataTransformer):
            ...     def transform(self, data, params):
            ...         df = data.copy()
            ...         if 'min_price' in params:
            ...             df = df[df['Price'] >= params['min_price']]
            ...         return df

            >>> # Aggregation
            >>> class CategoryAggregator(DataTransformer):
            ...     def transform(self, data, params):
            ...         return data.groupby('Category')['Sales'].sum().reset_index()
        """
        self.logger.debug(
            f"[DataTransformer] Transforming {len(data)} rows with params: {list(params.keys())}"
        )

        # Default: no transformation, return data as-is
        self.logger.debug(
            "[DataTransformer] Using default implementation (no transformation)"
        )
        return data


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

    def transform(self, data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Apply transformers sequentially.

        First transformer receives params (global filters), second receives
        empty dict (block-specific transform doesn't need params).

        :hierarchy: [Core | DataSources | ChainedTransformer | Transform]
        :relates-to:
         - motivated_by: "Sequential transformation preserves order"
         - implements: "method: 'transform'"

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
            f"[ChainedTransformer|Transform] Starting chain | "
            f"input_rows={len(data)} | params={list(params.keys())}"
        )

        # Step 1: Apply the global filter with its params
        filtered_data = self.transformer_1.transform(data, params)
        self.logger.debug(
            f"[ChainedTransformer|Transform] After transformer_1: {len(filtered_data)} rows"
        )

        # Step 2: Apply the block-specific transform (it does not need params)
        final_data = self.transformer_2.transform(filtered_data, {})
        self.logger.debug(
            f"[ChainedTransformer|Transform] After transformer_2: {len(final_data)} rows"
        )

        return final_data
