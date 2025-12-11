from collections.abc import Generator
from contextlib import contextmanager, redirect_stderr, redirect_stdout
from io import StringIO
from typing import TextIO

import orjson
import pytest
from freezegun import freeze_time
from structlog import reset_defaults

from mh_structlog import ERROR, filter_named_logger, get_logger, setup


@contextmanager
def capture_output() -> Generator[tuple[TextIO, TextIO]]:
    """
    Capture both stdout and stderr into StringIO buffers.

    Source: https://adamj.eu/tech/2025/08/29/python-unittest-capture-stdout-stderr/
    """
    with redirect_stdout(StringIO()) as out, redirect_stderr(StringIO()) as err:
        yield out, err


@freeze_time("2025-12-11 12:01:02")
def test_setup_twice():
    reset_defaults()

    with capture_output() as (out, _err):
        setup(log_format="json", testing_mode=False, logging_configs=[filter_named_logger("asyncio", ERROR)])
        setup(log_format="json", testing_mode=False, logging_configs=[filter_named_logger("asyncio", ERROR)])

    data = orjson.loads(out.getvalue())

    assert data == {
        'level': 'warning',
        'logger': 'mh_structlog',
        'message': 'logging was already configured, so I return and do nothing.',
        'timestamp': '2025-12-11T12:01:02Z',
    }


def test_setup_invalid_params():
    reset_defaults()
    with pytest.raises(Exception, match="max_frames should be a positive integer."):  # noqa: RUF043
        setup(max_frames=-1)

    reset_defaults()
    with pytest.raises(Exception, match="Unknown logging format requested."):  # noqa: RUF043
        setup(log_format='invalid_format')


@freeze_time("2025-12-11 12:01:02")
def test_logging_json():
    reset_defaults()

    with capture_output() as (out, _err):
        setup(log_format="json", testing_mode=True, logging_configs=[filter_named_logger("asyncio", ERROR)])
        logger = get_logger("test_logger_json")
        logger.info("JSON log message", keyA="valueA", keyB=100)

    data = orjson.loads(out.getvalue())

    assert isinstance(data, dict)

    assert data == {
        'keyA': 'valueA',
        'keyB': 100,
        'logger': 'test_logger_json',
        'level': 'info',
        'message': 'JSON log message',
        'timestamp': '2025-12-11T12:01:02Z',
    }
