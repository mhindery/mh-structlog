import logging  # noqa: I001
import logging.config
import sys
from typing import Literal
import structlog
import orjson
from structlog.processors import CallsiteParameter
from structlog.dev import RichTracebackFormatter

# Import the constants here so people don't need to import logging separately
# from logging import INFO, DEBUG, ERROR, WARN, WARNING, CRITICAL, FATAL


class StructlogLoggingConfigExceptionError(Exception):
    """Exception to raise if the config is not correct."""


# Default log message so we can find out which keys on a LogRecord are 'extra'
_LOG_RECORD_KEYS = set(logging.LogRecord("name", 0, "pathname", 0, "msg", (), None).__dict__.keys())


def _add_flattened_extra(_, __, event_dict):
    """Include the content of 'extra' in the output log, flattened the attributes."""
    if event_dict.get("_from_structlog", False):
        # Coming from structlog logging call
        extra = event_dict.pop("extra", {})
        for k, v in extra.items():
            event_dict[k] = v
    else:
        # Coming from standard logging call
        record = event_dict.get("_record")
        if record is not None:
            for k, v in record.__dict__.items():
                if k not in _LOG_RECORD_KEYS:
                    event_dict[k] = v

    return event_dict


def _merge_pathname_lineno_function_to_location(logger: structlog.BoundLogger, name: str, event_dict: dict) -> dict:  # noqa: ARG001
    """Add the source of the log as a single attribute."""
    pathname = event_dict.pop(CallsiteParameter.PATHNAME.value, None)
    lineno = event_dict.pop(CallsiteParameter.LINENO.value, None)
    func_name = event_dict.pop(CallsiteParameter.FUNC_NAME.value, None)
    event_dict["location"] = f"{pathname}:{lineno}({func_name})"
    return event_dict


def _render_orjson(logger: structlog.BoundLogger, name: str, event_dict: dict) -> str:  # noqa: ARG001
    return orjson.dumps(event_dict).decode()


def setup(
    log_format: Literal["console", "aws_json"] | None = None,
    logging_configs: list[dict] | None = None,
    include_source_location: bool = False,  # noqa: FBT001, FBT002
    global_filter_level: int | None = None,
) -> None:
    """Configure logging."""
    if structlog.is_configured():
        return

    shared_processors = [
        structlog.stdlib.add_logger_name,  # add the logger name
        structlog.stdlib.add_log_level,  # add the log level as textual representation
        structlog.processors.TimeStamper(fmt="iso", utc=True),  # add a timestamp
    ]

    if log_format is None:
        log_format = "console" if sys.stdout.isatty() else "aws_json"
    if log_format not in ["console", "aws_json"]:
        raise StructlogLoggingConfigExceptionError("Unknown logging format requested.")

    if log_format == "console":
        selected_formatter = "structlog_colored_formatter"
    elif log_format == "aws_json":
        shared_processors.append(
            structlog.processors.dict_tracebacks,
        )  # add 'exception' field with a dict of the exception
        selected_formatter = "structlog_json_formatter"

    if include_source_location:
        shared_processors.append(
            structlog.processors.CallsiteParameterAdder(
                parameters={CallsiteParameter.PATHNAME, CallsiteParameter.LINENO, CallsiteParameter.FUNC_NAME},
            ),
        )

    wrapper_class = structlog.stdlib.BoundLogger
    if global_filter_level is not None:
        wrapper_class = structlog.make_filtering_bound_logger(global_filter_level)

    # Structlog configuration
    structlog.configure(
        processors=[
            *shared_processors,
            structlog.stdlib.filter_by_level,  # filter based on the stdlib logging config
            structlog.contextvars.merge_contextvars,  # add variables and bound data from global context
            structlog.stdlib.PositionalArgumentsFormatter(),  # Allow string formatting with positional arguments in log calls
            structlog.processors.StackInfoRenderer(),  # when you create a log and specify stack_info=True, add a stacktrace to the log
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=wrapper_class,
        cache_logger_on_first_use=True,
    )

    # Std lib logging configuration.
    stdlib_logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "structlog_plain_formatter": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    _add_flattened_extra,  # extract the content of 'extra' and add it as entries in the event dict
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,  # remove some fields used by structlogs internal logic
                    structlog.processors.EventRenamer("message"),
                    structlog.dev.ConsoleRenderer(
                        colors=False,
                        pad_event=80,
                        sort_keys=True,
                        event_key="message",
                        exception_formatter=RichTracebackFormatter(
                            width=-1, max_frames=10, show_locals=True, locals_hide_dunder=True,
                        ),
                    ),
                ],
                "foreign_pre_chain": shared_processors,
            },
            "structlog_colored_formatter": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    _add_flattened_extra,  # extract the content of 'extra' and add it as entries in the event dict
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,  # remove some fields used by structlogs internal logic
                    structlog.processors.EventRenamer("message"),
                    structlog.dev.ConsoleRenderer(
                        pad_event=80,
                        sort_keys=True,
                        event_key="message",
                        exception_formatter=RichTracebackFormatter(
                            width=-1, max_frames=10, show_locals=True, locals_hide_dunder=True,
                        ),
                    ),
                ],
                "foreign_pre_chain": shared_processors,
            },
            "structlog_json_formatter": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    _add_flattened_extra,  # extract the content of 'extra' and add it as entries in the event dict
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,  # remove some fields used by structlogs internal logic
                    structlog.processors.EventRenamer("message"),
                    _render_orjson,
                ],
                "foreign_pre_chain": shared_processors,
            },
        },
        "filters": {},
        "handlers": {
            "structlog_handler": {
                "level": "DEBUG" if global_filter_level is None else logging.getLevelName(global_filter_level),
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": selected_formatter,
            },
        },
        "loggers": {
            "": {
                "handlers": ["structlog_handler"],
                "level": "DEBUG" if global_filter_level is None else logging.getLevelName(global_filter_level),
                "propagate": True,
            },
        },
    }

    # Merge in additional logging configs that were passed in by the caller.
    if logging_configs:
        for lc in logging_configs:
            for k, v in lc.get("loggers", {}).items():
                if k in ["", "root"]:
                    raise StructlogLoggingConfigExceptionError(
                        "It is not allowed to specify a custom root logger, since structlog configures that one.",
                    )
                # Add our handler if none was specified explicitly
                if "handlers" not in v:
                    v["handlers"] = ["structlog_handler"]
                if "level" not in v:
                    v["level"] = "DEBUG" if global_filter_level is None else logging.getLevelName(global_filter_level)
                    v["propagate"] = False
                stdlib_logging_config["loggers"][k] = v
            for k, v in lc.get("handlers", {}).items():
                # Set the formatter to ours if none was specified explicitly
                if "formatter" not in v:
                    # If we are logging to a file and we do not do json format, use the non-colored formatter
                    if "file" in v["class"].lower() and selected_formatter == "structlog_colored_formatter":
                        v["formatter"] = "structlog_plain_formatter"
                    else:
                        v["formatter"] = selected_formatter
                stdlib_logging_config["handlers"][k] = v
            for k, v in lc.get("formatters", {}).items():
                if k in ["structlog_plain_formatter", "structlog_colored_formatter", "structlog_json_formatter"]:
                    raise StructlogLoggingConfigExceptionError(
                        f"It is not allowed to specify a formatter with the name {k}, since structlog configures that one.",
                    )
                stdlib_logging_config["formatters"][k] = v
            for k, v in lc.get("filters", {}).items():
                stdlib_logging_config["filters"][k] = v

    logging.config.dictConfig(stdlib_logging_config)


def get_named_logger_level_filter(logger_name: str, level: int) -> dict:
    """Return a dict containing a configuration for a named logger with a certain level filter."""
    return {"loggers": {logger_name: {"level": level, "propagate": False}}}


def get_file_logger_config(logger_name: str = "", file_name: str = "out.log") -> dict:
    """Return a dict containing a configuration for logging to a file, additionally to the stdout output."""
    return {
        "handlers": {f"file_handler_{logger_name}": {"class": "logging.FileHandler", "filename": file_name}},
        "loggers": {logger_name: {"handlers": [f"file_handler_{logger_name}"]}},
    }


if __name__ == "__main__":
    setup(
        # log_format="aws_json",
        logging_configs=[
            get_named_logger_level_filter(logger_name="named", level=logging.DEBUG),
            get_file_logger_config(logger_name="file_logger", file_name="file.log"),
            get_file_logger_config(logger_name="file_logger_2", file_name="out.log"),
        ],
        global_filter_level=logging.NOTSET,
    )

    log = structlog.get_logger("named")
    log.debug("DEBUG MESSAGE")
    log.info("An info message", key="value", mylist=[1, 2, 3])
    log.warning("Another %s, this time %s", "one", "warning", hey="ho", extra={"lala": "lolo"})
    log.error("Testing", extra={"lala": "lolo"}, stack_info=True)
    std_log = logging.getLogger("named")
    std_log.debug("DEBUG MESSAGE")
    std_log.info("An info message", extra={"key": "value", "mylist": [1, 2, 3]})
    std_log.warning("Another %s, this time %s", "one", "warning", extra={"hey": "ho", "lala": "lolo"})
    std_log.error("Testing", extra={"lala": "lolo"}, stack_info=True)
    # try:
    #     raise Exception('An exception')
    # except Exception as e:
    #     log.exception('Something went wrong')
    # raise Exception('Another one')

    # Logging to a file
    file_log = structlog.get_logger("file_logger")
    file_log.debug("DEBUG MESSAGE")
    file_log.info("An info message", key="value", mylist=[1, 2, 3])
    file_log.warning("Another %s, this time %s", "one", "warning", hey="ho", extra={"lala": "lolo"})
    file_log.error("Testing", extra={"lala": "lolo"}, stack_info=True)
