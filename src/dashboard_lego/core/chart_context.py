"""
Chart context data structure for unified chart generation.

This module defines the ChartContext dataclass that provides a standardized
interface for chart generators, containing all necessary context information
including datasource, controls, and logger.

"""

from dataclasses import dataclass
from typing import Any, Dict

from dashboard_lego.core.datasource import BaseDataSource
from dashboard_lego.utils.logger import get_logger


@dataclass(frozen=True)
class ChartContext:
    """
    Context object containing all necessary information for chart generation.

    This dataclass provides a unified interface for chart generators,
    encapsulating the datasource, control values, and logger in a single
    immutable object.

        :hierarchy: [Architecture | ChartContext | ChartContext]
        :relates-to:
         - motivated_by: "Architectural Conclusion: Unified chart generator signatures
           enable consistent chart creation across different block types"
         - implements: "datatype: 'ChartContext'"
         - uses: ["interface: 'BaseDataSource'", "module: 'utils.logger'"]

        :rationale: "Chose immutable dataclass for thread safety and clear interface contract."
        :contract:
         - pre: "Valid datasource and controls dictionary must be provided."
         - post: "Context object contains all necessary data for chart generation."

    """

    datasource: BaseDataSource
    controls: Dict[str, Any]
    logger: Any = None

    def __post_init__(self):
        """
        Initialize logger if not provided.

        """
        if self.logger is None:
            object.__setattr__(self, "logger", get_logger(__name__))
