from structlog.testing import capture_logs

import mh_structlog
from mh_structlog.config import filter_named_logger, setup


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
