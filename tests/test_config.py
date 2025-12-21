import orjson
from freezegun import freeze_time
from structlog import reset_defaults
from structlog.contextvars import clear_contextvars
from structlog.testing import capture_logs

import mh_structlog
from mh_structlog.config import filter_named_logger, setup
from mh_structlog.processors import FieldsAdder

from .utils import capture_output


def test_setup_configures_structlog():
    """Test that setup configures structlog properly."""
    setup(testing_mode=True)

    with capture_logs() as logs:
        mh_structlog.get_logger().info("Test log message", key1="value1", key2=42)

    assert len(logs) == 1
    assert logs[0] == {'key1': 'value1', 'key2': 42, 'event': 'Test log message', 'log_level': 'info'}


def test_filter_named_logger():
    ret = filter_named_logger("filtered.logger", mh_structlog.INFO)
    assert ret == {'loggers': {'filtered.logger': {'level': 20, 'propagate': False}}}


@freeze_time("2025-12-11 12:01:02")
def test_setup_with_additional_processors():
    reset_defaults()
    clear_contextvars()

    with capture_output() as (out, _err):
        setup(
            testing_mode=True,
            log_format='json',
            additional_processors=[FieldsAdder(data={"custom_field": "custom_value"})],
            timestamp_ms_precision=False,
        )
        mh_structlog.get_logger().info("Test log message", key1="value1", key2=42)

    data = orjson.loads(out.getvalue())

    data.pop('logger')

    assert data == {
        'key1': 'value1',
        'key2': 42,
        'message': 'Test log message',
        'level': 'info',
        "custom_field": "custom_value",
        'timestamp': '2025-12-11T12:01:02Z',
    }


@freeze_time("2025-12-11 12:01:02")
def test_setup_with_global_filter_level():
    reset_defaults()
    clear_contextvars()

    with capture_output() as (out, _err):
        setup(testing_mode=True, log_format='json', global_filter_level=mh_structlog.WARNING)
        mh_structlog.get_logger().info("Test log message", key1="value1", key2=42)

    assert not out.getvalue()

    with capture_output() as (out, _err):
        setup(testing_mode=True, log_format='json', global_filter_level=mh_structlog.WARNING)
        mh_structlog.get_logger().warning("Test log message", key1="value1", key2=42)

    assert out.getvalue()


@freeze_time("2025-12-11 12:01:02")
def test_setup_with_source_location():
    reset_defaults()
    clear_contextvars()

    with capture_output() as (out, _err):
        setup(testing_mode=True, log_format='json', include_source_location=True, timestamp_ms_precision=False)
        mh_structlog.get_logger().info("Test log message", key1="value1", key2=42)

    data = orjson.loads(out.getvalue())

    data.pop('logger')

    assert 'lineno' in data
    data.pop('lineno')

    assert 'pathname' in data
    data.pop('pathname')

    assert data == {
        'key1': 'value1',
        'key2': 42,
        'message': 'Test log message',
        'level': 'info',
        'timestamp': '2025-12-11T12:01:02Z',
        'func_name': 'test_setup_with_source_location',
    }
