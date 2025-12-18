from mh_structlog import get_logger, getLogger, setup


def test_get_logger_getlogger_same_name():
    setup(testing_mode=True)
    logger1 = get_logger()
    logger2 = getLogger()

    assert logger1.name == logger2.name


def test_get_logger_custom_name():
    setup(testing_mode=True)
    custom_name = "my_custom_logger"
    logger = get_logger(custom_name)

    assert logger.name == custom_name


def test_get_logger_default_name():
    setup(testing_mode=True)
    logger = get_logger()

    assert logger.name == "tests.test_init"
