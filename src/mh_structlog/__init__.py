import typing as t
from logging import CRITICAL, DEBUG, ERROR, FATAL, INFO, WARN, WARNING

import structlog

from .config import filter_named_logger, setup
from .utils import determine_name_for_logger


def getLogger(name: t.Optional[str] = None):  # noqa: ANN201, N802
    """Return a named logger."""
    if name is None:
        name = determine_name_for_logger()
    return structlog.get_logger(name)


def get_logger(name: t.Optional[str] = None):  # noqa: ANN201
    """Return a named logger."""
    return getLogger(name)


__all__ = [
    "CRITICAL",
    "DEBUG",
    "ERROR",
    "FATAL",
    "INFO",
    "WARN",
    "WARNING",
    "filter_named_logger",
    "getLogger",
    "getLogger",
    "get_logger",
    "get_logger",
    "setup",
]
