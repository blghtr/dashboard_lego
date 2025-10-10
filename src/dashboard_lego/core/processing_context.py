"""
This module defines the DataProcessingContext for the data pipeline.

:hierarchy: [Core | DataSources | DataProcessingContext]
:relates-to:
 - motivated_by: "Refactor: Separate preprocessing and filtering parameters through pipeline"
 - implements: "dataclass: 'DataProcessingContext'"
 - uses: []

:contract:
 - pre: "params dict can be empty or None"
 - post: "Context provides typed access to preprocessing and filtering params"
 - invariant: "raw_params always contains original input"

:complexity: 3
:decision_cache: "Chose dataclass for immutability and clear structure over dict"
"""

from dataclasses import dataclass, field
from typing import Any, Callable, Dict, Optional

from dashboard_lego.utils.logger import get_logger


@dataclass
class DataProcessingContext:
    """
    Context object for data processing pipeline stages.

    This context separates preprocessing parameters (which affect data transformation)
    from filtering parameters (which affect data subsetting) to enable staged caching
    and clearer separation of concerns.

    :hierarchy: [Core | DataSources | DataProcessingContext]
    :relates-to:
     - motivated_by: "Need to pass preprocessing and filtering params separately through pipeline"
     - implements: "dataclass: 'DataProcessingContext'"

    :contract:
     - pre: "All params are optional and default to empty dicts"
     - post: "Context provides structured access to categorized params"

    Attributes:
        preprocessing_params: Parameters that affect data loading/transformation
                            (e.g., aggregation level, date parsing options)
        filtering_params: Parameters that affect data filtering/subsetting
                         (e.g., category filters, range filters)
        raw_params: Original params dict from controls (for backward compatibility)

    Example:
        >>> context = DataProcessingContext.from_params(
        ...     {'category': 'Electronics', 'min_price': 100},
        ...     lambda k: 'filter' if k in ['category', 'min_price'] else 'preprocess'
        ... )
        >>> context.filtering_params
        {'category': 'Electronics', 'min_price': 100}
    """

    preprocessing_params: Dict[str, Any] = field(default_factory=dict)
    filtering_params: Dict[str, Any] = field(default_factory=dict)
    raw_params: Dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_params(
        cls,
        params: Optional[Dict[str, Any]] = None,
        param_classifier: Optional[Callable[[str], str]] = None,
    ) -> "DataProcessingContext":
        """
        Create context by classifying params into preprocessing vs filtering.

        :hierarchy: [Core | DataSources | DataProcessingContext | Factory]
        :relates-to:
         - motivated_by: "Need flexible param classification for different use cases"
         - implements: "classmethod: 'from_params'"

        :contract:
         - pre: "params can be None or dict, param_classifier can be None or callable"
         - post: "Returns DataProcessingContext with classified params"
         - invariant: "raw_params always equals input params"

        Args:
            params: Raw params dict from controls. If None, treated as empty dict.
            param_classifier: Optional function that returns 'preprocess' or 'filter'
                            for each param key. If None, all params are treated as
                            preprocessing params (backward compatible default).

                            Signature: (param_key: str) -> str
                            Return value must be either 'preprocess' or 'filter'

        Returns:
            DataProcessingContext with classified params

        Example:
            >>> def classifier(key):
            ...     return 'filter' if key.startswith('filter_') else 'preprocess'
            >>> ctx = DataProcessingContext.from_params(
            ...     {'preproc_agg': 'sum', 'filter_cat': 'A'},
            ...     classifier
            ... )
            >>> ctx.preprocessing_params
            {'preproc_agg': 'sum'}
            >>> ctx.filtering_params
            {'filter_cat': 'A'}
        """
        logger = get_logger(__name__, DataProcessingContext)

        params = params or {}
        preprocessing = {}
        filtering = {}

        logger.debug(f"Classifying {len(params)} params into categories")

        for key, value in params.items():
            if param_classifier:
                try:
                    category = param_classifier(key)
                    if category in (
                        "filter",
                        "transform",
                    ):  # Accept both old and new names
                        filtering[key] = value
                        logger.debug(f"  {key} -> filtering/transform")
                    else:
                        # Default to preprocessing for any other return value
                        preprocessing[key] = value
                        logger.debug(f"  {key} -> preprocessing/build")
                except Exception as e:
                    logger.warning(
                        f"Error classifying param '{key}', defaulting to preprocessing: {e}"
                    )
                    preprocessing[key] = value
            else:
                # Default: all params are preprocessing (backward compatible)
                preprocessing[key] = value
                logger.debug(f"  {key} -> preprocessing (no classifier)")

        logger.info(
            f"Context created: {len(preprocessing)} preprocessing params, "
            f"{len(filtering)} filtering params"
        )

        return cls(
            preprocessing_params=preprocessing,
            filtering_params=filtering,
            raw_params=params.copy(),  # Make a copy to prevent external mutations
        )
