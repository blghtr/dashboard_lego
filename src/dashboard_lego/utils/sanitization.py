"""
Input sanitization utilities.

:hierarchy: [Utils | Security | Sanitization]
:relates-to:
 - motivated_by: "Security: Prevent XSS attacks in user-provided content"
 - implements: "functions: 'sanitize_html', 'sanitize_dict'"
 - uses: ["library: 'html.escape'"]

:rationale: "HTML escaping prevents script injection and event handler attacks."
:contract:
 - pre: "value is any type that can be converted to string"
 - post: "Returns HTML-escaped string safe for rendering in HTML context"
 - invariant: "All HTML special characters are escaped"

:complexity: 2
"""

from html import escape
from typing import Any


def sanitize_html(value: Any) -> str:
    """
    Sanitize user input to prevent XSS attacks.

    Escapes HTML special characters to prevent:
    - Script tag injection: <script>alert('XSS')</script>
    - Event handler injection: <img onerror="alert('XSS')">
    - Attribute injection: <div onclick="alert('XSS')">
    - Data URI injection: <a href="javascript:alert('XSS')">
    - HTML entity confusion attacks

    Args:
        value: User input (will be converted to string)

    Returns:
        HTML-escaped string safe for rendering

    Example:
        >>> sanitize_html("<script>alert('XSS')</script>")
        "&lt;script&gt;alert(&#x27;XSS&#x27;)&lt;/script&gt;"
        >>> sanitize_html('"><img onerror="alert(1)">')
        "&quot;&gt;&lt;img onerror=&quot;alert(1)&quot;&gt;"
    """
    if value is None:
        return ""
    # Convert to string and escape HTML special characters
    # quote=True escapes both single and double quotes
    return escape(str(value), quote=True)


def sanitize_dict(data: dict) -> dict:
    """
    Recursively sanitize all string values in dictionary.

    Traverses nested dictionaries and lists to sanitize all string values,
    preventing XSS attacks in complex data structures.

    Args:
        data: Dictionary with potentially unsafe strings

    Returns:
        Dictionary with sanitized string values (non-string values unchanged)

    Example:
        >>> data = {
        ...     'safe': 'hello',
        ...     'unsafe': '<script>alert(1)</script>',
        ...     'nested': {'attack': '<img onerror=alert(1)>'}
        ... }
        >>> sanitize_dict(data)
        {'safe': 'hello', 'unsafe': '&lt;script&gt;...', 'nested': {'attack': '&lt;img...'}}
    """
    if not isinstance(data, dict):
        return data

    result = {}
    for key, value in data.items():
        if isinstance(value, str):
            result[key] = sanitize_html(value)
        elif isinstance(value, dict):
            result[key] = sanitize_dict(value)
        elif isinstance(value, list):
            result[key] = [
                (
                    sanitize_html(v)
                    if isinstance(v, str)
                    else sanitize_dict(v) if isinstance(v, dict) else v
                )
                for v in value
            ]
        else:
            result[key] = value
    return result
