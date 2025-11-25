"""
Async-compatible logging configuration for dashboard_lego using Loguru.

This module provides a modern, async-compatible logging system with automatic
hierarchy extraction from docstrings and dual output (console + rotating file).

:hierarchy: [Core | Logging | Async Logger]
"""

import inspect
import os
import re
import sys
from pathlib import Path
from typing import Any, Optional

from loguru import logger

# Windows file locking workaround: Patch Loguru's file sink to handle PermissionError
# during rotation gracefully
if sys.platform == "win32":
    try:
        from loguru._file_sink import FileSink

        # Store original _terminate_file method
        _original_terminate_file = FileSink._terminate_file

        def _patched_terminate_file(self, is_rotating=False):
            """
            Patched version that catches Windows file locking errors during rotation.

            On Windows, file rotation may fail if the file is locked by another process.
            This patch catches PermissionError and logs a warning instead of crashing.
            """
            try:
                return _original_terminate_file(self, is_rotating=is_rotating)
            except (PermissionError, OSError) as e:
                # Windows file locking error - log warning and continue
                if "WinError 32" in str(e) or "being used by another process" in str(e):
                    # File is locked - rotation will be retried on next write
                    # Don't crash, just skip this rotation attempt
                    try:
                        import sys

                        sys.stderr.write(
                            f"WARNING: Log rotation skipped (file locked): {e}\n"
                        )
                    except Exception:
                        pass  # Silently ignore if we can't write to stderr
                    return
                # Re-raise other errors
                raise

        # Apply patch
        FileSink._terminate_file = _patched_terminate_file
    except (ImportError, AttributeError):
        # If patching fails (e.g., Loguru version mismatch), continue without patch
        # The catch=True parameter will help with some errors
        pass


class HierarchyLoggerAdapter:
    """
    Logger adapter that prepends hierarchy to DEBUG logs.

    Wraps loguru logger with hierarchy support from docstrings.

    :hierarchy: [Core | Logging | HierarchyLoggerAdapter]
    """

    def __init__(self, name: str, hierarchy: Optional[str] = None):
        """
        Initialize logger adapter with hierarchy context.

        Args:
            name: Logger name (typically __name__)
            hierarchy: Hierarchy string extracted from docstrings
        """
        self.name = name
        self.hierarchy = hierarchy or "Unknown"
        self._logger = logger.bind(name=name, hierarchy=self.hierarchy)

    def debug(self, message: str, **kwargs):
        """Log debug message with hierarchy prefix."""
        if self.hierarchy != "Unknown" and not message.startswith("["):
            message = f"[{self.hierarchy}] {message}"
        self._logger.debug(message, **kwargs)

    def info(self, message: str, **kwargs):
        """Log info message."""
        self._logger.info(message, **kwargs)

    def warning(self, message: str, **kwargs):
        """Log warning message."""
        self._logger.warning(message, **kwargs)

    def error(self, message: str, **kwargs):
        """Log error message."""
        self._logger.error(message, **kwargs)

    def critical(self, message: str, **kwargs):
        """Log critical message."""
        self._logger.critical(message, **kwargs)

    def exception(self, message: str, exc_info=True, **kwargs):
        """Log exception with traceback."""
        self._logger.exception(message, **kwargs)

    def isEnabledFor(self, level: int) -> bool:
        """Check if logger is enabled for given level."""
        # Map standard logging levels to loguru
        level_map = {
            10: "DEBUG",
            20: "INFO",
            30: "WARNING",
            40: "ERROR",
            50: "CRITICAL",
        }
        loguru_level = level_map.get(level, "INFO")
        return self._logger.is_enabled(loguru_level)


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

    # Extract hierarchy if obj is provided
    hierarchy = None
    if obj is not None:
        hierarchy = _extract_hierarchy_from_docstring(obj)

    return HierarchyLoggerAdapter(logger_name, hierarchy)


def _get_log_level() -> str:
    """Get log level from environment variable."""
    return os.getenv("DASHBOARD_LEGO_LOG_LEVEL", "INFO").upper()


def _get_log_dir() -> str:
    """Get log directory from environment variable."""
    return os.getenv("DASHBOARD_LEGO_LOG_DIR", "./logs")


LOG_FILE = "dashboard_lego.log"
MAX_LOG_SIZE = 10 * 1024 * 1024  # 10 MB
BACKUP_COUNT = 5

# Ensure log directory exists
Path(_get_log_dir()).mkdir(parents=True, exist_ok=True)

# Global flag to track if logging is configured
_logging_configured = False


def setup_logging(level: Optional[str] = None, log_dir: Optional[str] = None) -> None:
    """
    Configure async-compatible logging with Loguru.

    :hierarchy: [Core | Logging | Setup]

    Args:
        level: Log level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               Defaults to environment variable or INFO.
        log_dir: Directory for log files. Defaults to ./logs.
    """
    global _logging_configured

    level = level or _get_log_level()
    log_dir = log_dir or _get_log_dir()

    # Ensure directory exists
    Path(log_dir).mkdir(parents=True, exist_ok=True)

    # Remove default handler if already configured
    if _logging_configured:
        logger.remove()

    # Console handler with colors
    console_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan> | "
        "<level>{message}</level>"
    )
    logger.add(
        sys.stderr,
        format=console_format,
        level=level,
        colorize=True,
        enqueue=True,  # Async support - thread-safe logging
    )

    # File handler with rotation
    # Windows-compatible configuration to handle file locking during rotation
    log_file_path = os.path.join(log_dir, LOG_FILE)
    file_format = (
        "{time:YYYY-MM-DD HH:mm:ss} | "
        "{level: <8} | "
        "{name}:{function}:{line} | "
        "{message}"
    )

    # Configure file sink with Windows-compatible settings
    # Use larger rotation size to reduce rotation frequency (fewer lock conflicts)
    # catch=True will catch exceptions during logging operations
    # enqueue=True provides thread safety but doesn't prevent Windows file locking
    try:
        logger.add(
            log_file_path,
            format=file_format,
            level="DEBUG",  # File captures everything
            rotation=f"{MAX_LOG_SIZE // (1024 * 1024)} MB",  # Rotate at MAX_LOG_SIZE
            retention=f"{BACKUP_COUNT * 7} days",  # Keep logs for approximately BACKUP_COUNT weeks
            compression="zip",  # Compress old logs
            enqueue=True,  # Async support - thread-safe logging
            catch=True,  # Catch exceptions during logging (helps with some errors)
            backtrace=True,  # Show full traceback
            diagnose=True,  # Show variable values in traceback
            encoding="utf-8",
            errors="ignore",  # Ignore encoding errors gracefully
        )
    except Exception as e:
        # If file sink setup fails (e.g., permission issues), log to stderr only
        # This prevents the application from crashing due to logging configuration
        logger.warning(
            f"Failed to configure file logging to {log_file_path}: {e}. "
            "Logging to console only."
        )

    # Mark as configured
    _logging_configured = True

    # Log initialization only when not in reloader subprocess
    if os.environ.get("WERKZEUG_RUN_MAIN") != "true":
        logger.debug(f"Logging initialized: level={level}, log_dir={log_dir}")


def update_log_level(level: Optional[str] = None) -> None:
    """
    Update log level for existing loggers.

    Useful when environment variable is changed after module import.

    Args:
        level: Log level as string (DEBUG, INFO, WARNING, ERROR, CRITICAL).
               If None, reads from DASHBOARD_LEGO_LOG_LEVEL environment variable.
    """
    level = level or _get_log_level()

    # Remove existing handlers and reconfigure
    logger.remove()
    setup_logging(level)

    logger.info(f"Log level updated to {level}")


def _auto_setup_logging():
    """Auto-setup logging if not already configured."""
    global _logging_configured
    if not _logging_configured and not os.getenv("DASHBOARD_LEGO_NO_AUTO_LOG_SETUP"):
        setup_logging()
        _logging_configured = True


# Auto-setup on import only if not explicitly disabled
if not os.getenv("DASHBOARD_LEGO_NO_AUTO_LOG_SETUP"):
    _auto_setup_logging()
