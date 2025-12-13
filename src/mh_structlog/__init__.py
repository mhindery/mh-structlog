from __future__ import annotations

from logging import CRITICAL, DEBUG, ERROR, FATAL, INFO, WARN, WARNING

import structlog

from .config import filter_named_logger, setup
from .processors import FieldDropper, FieldRenamer, FieldsAdder
from .utils import determine_name_for_logger


def getLogger(name: str | None = None):  # noqa: ANN201, N802
    """Return a named logger."""
    if name is None:
        name = determine_name_for_logger()
    return structlog.get_logger(name)


def get_logger(name: str | None = None):  # noqa: ANN201
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
    "FieldDropper",
    "FieldRenamer",
    "FieldsAdder",
    "filter_named_logger",
    "getLogger",
    "getLogger",
    "get_logger",
    "get_logger",
    "setup",
]
