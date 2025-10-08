"""
This module provides utility functions for formatting values.

"""

import json
from typing import Any

import numpy as np


class NumpyEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for NumPy types.
    This encoder handles the serialization of common NumPy data types that are
    not natively supported by the standard `json` library. It converts NumPy
    integers, floats, booleans, and arrays into their standard Python equivalents.

        :hierarchy: [Utils | Formatting | NumpyEncoder]
        :relates-to:
          - motivated_by: "Bug: `TypeError` during cache key generation for NumPy types."
          - implements: "utility: 'NumpyEncoder'"

        :contract:
          - pre: "Input object `obj` can be a standard type or a NumPy type."
          - post: "Returns a JSON-serializable representation of the object."

    """

    def default(self, obj: Any) -> Any:
        """
        Overrides the default JSON encoding behavior to handle NumPy types.

        Args:
            obj: The object to encode.

        Returns:
            A serializable representation of the object.
        """
        if isinstance(obj, (np.integer, np.floating, np.bool_)):
            return obj.item()
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        return super(NumpyEncoder, self).default(obj)


def format_number(value: Any) -> str:
    """
    Formats a number into a string with appropriate separators.

    - Floats are formatted to two decimal places.
    - Integers are formatted with thousand separators.
    - Other types are converted to strings.

        :hierarchy: [Utils | Formatting | format_number]
        :relates-to:
          - motivated_by: "Architectural Conclusion: Consistent number formatting
            improves user experience across all dashboard components"
          - implements: "utility: 'format_number'"

        :rationale: "A simple function was chosen for direct extraction of formatting logic from KPIBlock, avoiding over-engineering."
        :contract:
          - pre: "Input `value` can be of any type."
          - post: "Returns a formatted string representation of the value."

    Args:
        value: The number or value to format.

    Returns:
        A formatted string.

    """
    if isinstance(value, float):
        return f"{value:.2f}"
    if isinstance(value, int):
        return f"{value:,}"
    return str(value)
