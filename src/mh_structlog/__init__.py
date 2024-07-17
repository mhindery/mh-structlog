import typing as t
from logging import CRITICAL, DEBUG, ERROR, FATAL, INFO, WARN, WARNING

import structlog

from .config import get_file_logger_config, get_named_logger_level_filter, setup
from .django import StructLogAccessLoggingMiddleware


def getLogger(name: t.Optional[str] = None):  # noqa: ANN201, N802
    """Return a named logger."""
    return structlog.get_logger(name)


def get_logger(name: t.Optional[str] = None):  # noqa: ANN201
    """Return a named logger."""
    return structlog.get_logger(name)


__all__ = [
    "setup",
    "get_logger",
    "getLogger",
    "get_named_logger_level_filter",
    "get_file_logger_config",
    "INFO",
    "DEBUG",
    "ERROR",
    "WARN",
    "WARNING",
    "CRITICAL",
    "FATAL",
    "StructLogAccessLoggingMiddleware",
    "getLogger",
    "get_logger",
]
