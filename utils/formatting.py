"""
This module provides utility functions for formatting values.

"""

from typing import Any


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
