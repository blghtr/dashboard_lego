"""
Centralized logging configuration for dashboard_lego.

This module provides a smart logging system with automatic hierarchy extraction
from docstrings and dual output (console + rotating file).

"""

import inspect
import logging
import os
import re
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional


# Global logging configuration
def _get_log_level():
    """Get log level from environment variable."""
    return os.getenv("DASHBOARD_LEGO_LOG_LEVEL", "INFO").upper()


def _get_log_dir():
    """Get log directory from environment variable."""
    return os.getenv("DASHBOARD_LEGO_LOG_DIR", "./logs")


LOG_FILE = "dashboard_lego.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

# Ensure log directory exists
Path(_get_log_dir()).mkdir(parents=True, exist_ok=True)


class HierarchyLoggerAdapter(logging.LoggerAdapter):
    """
    A custom LoggerAdapter that prepends hierarchy to DEBUG logs.

        :hierarchy: [Core | Logging | HierarchyLoggerAdapter]
        :relates-to:
         - motivated_by: "User requirement: Debug logs must display
           hierarchy from docstrings"
         - implements: "class: 'HierarchyLoggerAdapter'"
         - uses: ["library: 'logging'"]

        :rationale: "Chose LoggerAdapter to transparently inject
         hierarchy context without modifying call sites."
        :contract:
         - pre: "A standard logger and optional hierarchy string are
           provided."
         - post: "All DEBUG messages are automatically prefixed with
           [Hierarchy] if available."

    """

    def __init__(self, logger: logging.Logger, hierarchy: Optional[str] = None):
        """
        Initialize the adapter with hierarchy context.

        Args:
            logger: The base logger instance.
            hierarchy: The hierarchy string extracted from docstrings.

        """
        super().__init__(logger, {"hierarchy": hierarchy or "Unknown"})

    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """
        Process the log message to inject hierarchy for DEBUG level.

        Args:
            msg: The original log message.
            kwargs: Additional keyword arguments.

        Returns:
            A tuple of (modified_message, kwargs).

        """
        # Check if this is a DEBUG level log
        # Note: kwargs.get('level') doesn't work,
        # we check logger's effective level
        if self.isEnabledFor(logging.DEBUG):
            hierarchy = self.extra.get("hierarchy", "Unknown")
            # Prepend hierarchy only if not already in message
            if hierarchy != "Unknown" and not msg.startswith("["):
                msg = f"[{hierarchy}] {msg}"
        return msg, kwargs


def _extract_hierarchy_from_docstring(obj: Any) -> Optional[str]:
    """
    Extract the :hierarchy: field from an object's docstring.

    Args:
        obj: A class, function, or module object.

    Returns:
        The hierarchy string if found, None otherwise.

    """
    docstring = inspect.getdoc(obj)
    if not docstring:
        return None

    # Look for :hierarchy: [Some | Hierarchy | Path]
    match = re.search(r":hierarchy:\s*\[(.*?)\]", docstring, re.IGNORECASE)
    if match:
        return match.group(1).strip()

    return None


def get_logger(name: str, obj: Optional[Any] = None) -> HierarchyLoggerAdapter:
    """
    Factory function to create a logger with automatic hierarchy extraction.

        :hierarchy: [Core | Logging | Logger Factory]
        :relates-to:
         - motivated_by: "User requirement: Centralized logger
           creation with hierarchy support"
         - implements: "function: 'get_logger'"
         - uses: ["class: 'HierarchyLoggerAdapter'",
           "function: '_extract_hierarchy_from_docstring'"]

        :rationale: "Factory pattern allows centralized configuration
         and automatic docstring parsing."
        :contract:
         - pre: "A logger name is provided; optionally, an object for
           hierarchy extraction."
         - post: "Returns a configured HierarchyLoggerAdapter ready
           for use."

    Args:
        name: The name for the logger (typically __name__).
        obj: Optional object (class, function) to extract hierarchy from.

    Returns:
        A configured HierarchyLoggerAdapter instance.

    Example:
        >>> logger = get_logger(__name__, MyClass)
        >>> logger.debug("This will include hierarchy")
        >>> logger.info("This is for users")

    """
    # Ensure logger name starts with dashboard_lego for proper inheritance
    if not name.startswith("dashboard_lego"):
        logger_name = f"dashboard_lego.{name}"
    else:
        logger_name = name

    base_logger = logging.getLogger(logger_name)

    # Extract hierarchy if obj is provided
    hierarchy = None
    if obj is not None:
        hierarchy = _extract_hierarchy_from_docstring(obj)

    return HierarchyLoggerAdapter(base_logger, hierarchy)


def setup_logging(level: Optional[str] = None, log_dir: Optional[str] = None) -> None:
    """
    Configure global logging with dual output (console + rotating file).

        :hierarchy: [Core | Logging | Setup]
        :relates-to:
         - motivated_by: "User requirement: Dual logging to console
           and file with rotation"
         - implements: "function: 'setup_logging'"
         - uses: ["library: 'logging'", "class: 'RotatingFileHandler'"]

        :rationale: "Centralized setup ensures consistent formatting
         and handlers across the application."
        :contract:
         - pre: "Function is called once at application startup."
         - post: "All loggers use configured handlers with appropriate
           formatters."

    Args:
        level: Log level as string (DEBUG, INFO, WARNING, ERROR,
               CRITICAL). Defaults to environment variable or INFO.
        log_dir: Directory for log files. Defaults to ./logs.

    """
    level = level or _get_log_level()
    log_dir = log_dir or _get_log_dir()

    # Ensure directory exists
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Get root logger for dashboard_lego
    root_logger = logging.getLogger("dashboard_lego")
    root_logger.setLevel(getattr(logging, level, logging.INFO))

    # Also set the root logger to ensure proper propagation
    logging.getLogger().setLevel(getattr(logging, level, logging.INFO))

    # Check if logging is already configured to prevent double initialization
    if root_logger.handlers:
        root_logger.debug("Logging already configured, skipping re-initialization")
        return

    # Mark as configured
    global _logging_configured
    _logging_configured = True

    # Console Handler
    console_handler = logging.StreamHandler()
    # Console shows the same level as configured
    console_handler.setLevel(getattr(logging, level, logging.INFO))
    console_formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    console_handler.setFormatter(console_formatter)

    # File Handler (with rotation)
    log_file_path = os.path.join(log_dir, LOG_FILE)
    file_handler = RotatingFileHandler(
        log_file_path, maxBytes=MAX_LOG_SIZE, backupCount=BACKUP_COUNT, encoding="utf-8"
    )
    # File captures everything
    file_handler.setLevel(logging.DEBUG)
    file_formatter = logging.Formatter(
        fmt=(
            "%(asctime)s - %(name)s - %(levelname)s - "
            "%(funcName)s:%(lineno)d - %(message)s"
        ),
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)

    # Add handlers to root logger
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Ensure propagation to child loggers
    root_logger.propagate = True

    # Force immediate output
    import sys

    sys.stdout.flush()
    sys.stderr.flush()

    # Configure exception hook to log unhandled exceptions
    def exception_hook(exc_type, exc_value, exc_traceback):
        """Log unhandled exceptions to file before program terminates."""
        if issubclass(exc_type, KeyboardInterrupt):
            # Don't log keyboard interrupts
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return

        root_logger.critical(
            "Unhandled exception occurred",
            exc_info=(exc_type, exc_value, exc_traceback),
        )

        # Force log flush to ensure it's written to file
        for handler in root_logger.handlers:
            handler.flush()

        # Also call the default handler to print to stderr
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = exception_hook

    # Log the initialization only when not in reloader subprocess
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        root_logger.info(f"Logging initialized: level={level}, log_dir={log_dir}")


# Auto-setup on import (can be disabled by setting env var)
# Only auto-setup if not already configured
_logging_configured = False


def _auto_setup_logging():
    """Auto-setup logging if not already configured."""
    global _logging_configured
    if not _logging_configured and not os.getenv("DASHBOARD_LEGO_NO_AUTO_LOG_SETUP"):
        setup_logging()
        _logging_configured = True


# Auto-setup on import only if not explicitly disabled
if not os.getenv("DASHBOARD_LEGO_NO_AUTO_LOG_SETUP"):
    _auto_setup_logging()
