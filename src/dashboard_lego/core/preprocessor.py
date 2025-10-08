"""
This module defines the PreProcessor for data preprocessing operations.

:hierarchy: [Core | DataSources | PreProcessor]
:relates-to:
 - motivated_by: "Refactor: Separate preprocessing logic from filtering for better caching"
 - implements: "class: 'PreProcessor'"
 - uses: []

:contract:
 - pre: "Receives raw DataFrame and preprocessing params"
 - post: "Returns preprocessed DataFrame"
 - invariant: "Preprocessing is deterministic for same params"

:complexity: 2
:decision_cache: "Chose base class pattern for extensibility via inheritance"
"""

import logging
from typing import Any, Dict, Optional

import pandas as pd

from dashboard_lego.utils.logger import get_logger


class PreProcessor:
    """
    Handles data preprocessing operations in the data pipeline.

    This class is responsible for data transformations that should happen
    before filtering, such as:
    - Feature engineering (adding calculated columns)
    - Data type conversions
    - Aggregations
    - Joins with other data sources
    - Date parsing and extraction

    :hierarchy: [Core | DataSources | PreProcessor]
    :relates-to:
     - motivated_by: "Need to separate preprocessing from filtering for staged caching"
     - implements: "class: 'PreProcessor'"

    :contract:
     - pre: "process() receives valid DataFrame and params dict"
     - post: "process() returns preprocessed DataFrame"
     - invariant: "Same input data + params always produces same output"

    :complexity: 2
    :decision_cache: "Chose inheritance-based extensibility over composition"

    Example:
        >>> class SalesPreProcessor(PreProcessor):
        ...     def process(self, raw_data, params):
        ...         df = raw_data.copy()
        ...         df['Revenue'] = df['Price'] * df['Quantity']
        ...         return df
        >>>
        >>> preprocessor = SalesPreProcessor()
        >>> processed_df = preprocessor.process(raw_df, {})
    """

    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize PreProcessor.

        :hierarchy: [Core | DataSources | PreProcessor | Initialization]
        :relates-to:
         - motivated_by: "Need configurable logger for debugging"
         - implements: "method: '__init__'"

        :contract:
         - pre: "logger can be None or valid Logger instance"
         - post: "PreProcessor is ready to process data"

        Args:
            logger: Optional logger instance. If None, creates default logger.
        """
        self.logger = logger or get_logger(__name__, PreProcessor)
        self.logger.debug("PreProcessor initialized")

    def process(self, raw_data: pd.DataFrame, params: Dict[str, Any]) -> pd.DataFrame:
        """
        Preprocess raw data based on params.

        :hierarchy: [Core | DataSources | PreProcessor | Process]
        :relates-to:
         - motivated_by: "Core preprocessing interface for pipeline"
         - implements: "method: 'process'"

        :contract:
         - pre: "raw_data is valid DataFrame, params is dict"
         - post: "Returns preprocessed DataFrame"
         - invariant: "Does not modify input DataFrame"

        :complexity: 1
        :decision_cache: "Default implementation returns unchanged data for backward compatibility"

        Args:
            raw_data: Raw DataFrame from data source
            params: Preprocessing parameters that affect transformation logic
                   (these come from preprocessing_params in DataProcessingContext)

        Returns:
            Preprocessed DataFrame

        Note:
            Override this method in subclasses for custom preprocessing logic.
            The default implementation returns raw_data unchanged.
            Always work on a copy of the data to avoid modifying the original.

        Example:
            >>> class MyPreProcessor(PreProcessor):
            ...     def process(self, raw_data, params):
            ...         df = raw_data.copy()
            ...         # Add calculated column
            ...         if 'add_revenue' in params and params['add_revenue']:
            ...             df['Revenue'] = df['Price'] * df['Quantity']
            ...         return df
        """
        self.logger.debug(
            f"[PreProcessor] Processing {len(raw_data)} rows with params: {list(params.keys())}"
        )

        # Default: no preprocessing, return data as-is
        self.logger.debug(
            "[PreProcessor] Using default implementation (no transformation)"
        )
        return raw_data
