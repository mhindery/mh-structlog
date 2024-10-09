import logging  # noqa: I001
import logging.config
import sys
import typing as t
import structlog
from pathlib import Path
import orjson
from structlog.processors import CallsiteParameter
from structlog.dev import RichTracebackFormatter


class StructlogLoggingConfigExceptionError(Exception):
    """Exception to raise if the config is not correct."""


# Default log message so we can find out which keys on a LogRecord are 'extra'
_LOG_RECORD_KEYS = set(logging.LogRecord("name", 0, "pathname", 0, "msg", (), None).__dict__.keys())


def _add_flattened_extra(_, __, event_dict: dict) -> dict:
    """Include the content of 'extra' in the output log, flattened the attributes."""
    if event_dict.get("_from_structlog", False):
        # Coming from structlog logging call
        extra = event_dict.pop("extra", {})
        event_dict.update(extra)
    else:
        # Coming from standard logging call
        record = event_dict.get("_record")
        if record is not None:
            event_dict.update({k: v for k, v in record.__dict__.items() if k not in _LOG_RECORD_KEYS})

    return event_dict


def _merge_pathname_lineno_function_to_location(logger: structlog.BoundLogger, name: str, event_dict: dict) -> dict:  # noqa: ARG001
    """Add the source of the log as a single attribute."""
    pathname = event_dict.pop(CallsiteParameter.PATHNAME.value, None)
    lineno = event_dict.pop(CallsiteParameter.LINENO.value, None)
    func_name = event_dict.pop(CallsiteParameter.FUNC_NAME.value, None)
    event_dict["location"] = f"{pathname}:{lineno}({func_name})"
    return event_dict


def _ensure_msg_string(logger: structlog.BoundLogger, name: str, event_dict: dict) -> str:  # noqa: ARG001
    """Ensure that the message is a string, so it is json-serializable."""
    if not isinstance(event_dict['message'], str):
        event_dict['message'] = str(event_dict['message'])
    return event_dict


def _render_orjson(logger: structlog.BoundLogger, name: str, event_dict: dict) -> str:  # noqa: ARG001
    """Render the event_dict as a json string using orjson."""
    return orjson.dumps(event_dict).decode()


def setup(
    log_format: t.Optional[t.Literal["console", "json"]] = None,
    logging_configs: t.Optional[t.List[dict]] = None,
    include_source_location: bool = False,  # noqa: FBT001, FBT002
    global_filter_level: t.Optional[int] = None,
    log_file: t.Optional[t.Union[str, Path]] = None,
    log_file_format: t.Optional[t.Literal["console", "json"]] = None,
    testing_mode: bool = False,  # noqa: FBT001, FBT002
) -> None:
    """This method configures structlog and the standard library logging module."""

    # Unless we are in testing mode, don't configure logging if it was already configured.
    # During testing, we need te flexibility to configure logging multiple times.
    if structlog.is_configured() and not testing_mode:
        from logging import getLogger

        getLogger('mh_structlog').warning('logging was already configured, so I return and do nothing.')
        return

    shared_processors = [
        structlog.stdlib.add_logger_name,  # add the logger name
        structlog.stdlib.add_log_level,  # add the log level as textual representation
        structlog.processors.TimeStamper(fmt="iso", utc=True),  # add a timestamp
    ]

    # Configure stdout formatter
    if log_format is None:
        log_format = "console" if sys.stdout.isatty() else "json"
    if log_format not in ["console", "json"]:
        raise StructlogLoggingConfigExceptionError("Unknown logging format requested.")

    if log_format == "console":
        selected_formatter = "mh_structlog_colored"
    elif log_format == "json":
        shared_processors.append(
            structlog.processors.dict_tracebacks
        )  # add 'exception' field with a dict of the exception
        selected_formatter = "mh_structlog_json"

    if include_source_location:
        shared_processors.append(
            structlog.processors.CallsiteParameterAdder(
                parameters={CallsiteParameter.PATHNAME, CallsiteParameter.LINENO, CallsiteParameter.FUNC_NAME}
            )
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
        cache_logger_on_first_use=not testing_mode,  # https://www.structlog.org/en/stable/testing.html#testing
    )

    # Std lib logging configuration.
    stdlib_logging_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "mh_structlog_plain": {
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
                            width=-1, max_frames=10, show_locals=True, locals_hide_dunder=True
                        ),
                    ),
                ],
                "foreign_pre_chain": shared_processors,
            },
            "mh_structlog_colored": {
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
                            width=-1, max_frames=10, show_locals=True, locals_hide_dunder=True
                        ),
                    ),
                ],
                "foreign_pre_chain": shared_processors,
            },
            "mh_structlog_json": {
                "()": structlog.stdlib.ProcessorFormatter,
                "processors": [
                    _add_flattened_extra,  # extract the content of 'extra' and add it as entries in the event dict
                    structlog.stdlib.ProcessorFormatter.remove_processors_meta,  # remove some fields used by structlogs internal logic
                    structlog.processors.EventRenamer("message"),
                    _ensure_msg_string,
                    _render_orjson,
                ],
                "foreign_pre_chain": shared_processors,
            },
        },
        "filters": {},
        "handlers": {
            "mh_structlog_stdout": {
                "level": "DEBUG" if global_filter_level is None else logging.getLevelName(global_filter_level),
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
                "formatter": selected_formatter,
            }
        },
        "loggers": {
            "": {
                "handlers": ["mh_structlog_stdout"],
                "level": "DEBUG" if global_filter_level is None else logging.getLevelName(global_filter_level),
                "propagate": True,
            },
            "stdout": {
                "handlers": ["mh_structlog_stdout"],
                "level": "DEBUG" if global_filter_level is None else logging.getLevelName(global_filter_level),
                "propagate": False,
            },
        },
    }

    # Add a handler to output to a file
    if log_file:
        # Select formatter
        if log_file_format is None:
            log_file_format = "console" if sys.stdout.isatty() else "json"
        if log_file_format not in ["console", "json"]:
            raise StructlogLoggingConfigExceptionError("Unknown logging format requested.")

        if log_file_format == "console":
            selected_file_formatter = "mh_structlog_plain"
        elif log_file_format == "json":
            selected_file_formatter = "mh_structlog_json"

        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        # Add a handler with file output to the root logger
        stdlib_logging_config['handlers']['mh_structlog_file'] = {
            "level": "DEBUG" if global_filter_level is None else logging.getLevelName(global_filter_level),
            "class": "logging.FileHandler",
            "formatter": selected_file_formatter,
            'filename': log_file.name,
        }
        stdlib_logging_config['loggers']['']['handlers'].append('mh_structlog_file')
        # Add a named logger to log to the file only (the root logger logs to both stdout and file)
        stdlib_logging_config['loggers']['file'] = {
            "handlers": ["mh_structlog_file"],
            "level": "DEBUG" if global_filter_level is None else logging.getLevelName(global_filter_level),
            "propagate": False,
        }

    # Merge in additional logging configs that were passed in by the caller.
    if logging_configs:
        for lc in logging_configs:
            for k, v in lc.get("loggers", {}).items():
                if k in ["", "root"]:
                    raise StructlogLoggingConfigExceptionError(
                        "It is not allowed to specify a custom root logger, since structlog configures that one."
                    )
                # Add our handler if none was specified explicitly
                if "handlers" not in v:
                    v["handlers"] = ["mh_structlog_stdout"]
                    if log_file:
                        v['handlers'].append('mh_structlog_file')
                if "level" not in v:
                    v["level"] = "DEBUG" if global_filter_level is None else logging.getLevelName(global_filter_level)
                    v["propagate"] = False
                stdlib_logging_config["loggers"][k] = v
            for k, v in lc.get("handlers", {}).items():
                # Set the formatter to ours if none was specified explicitly
                if "formatter" not in v:
                    # If we are logging to a file and we do not do json format, use the non-colored formatter
                    if "file" in v["class"].lower() and selected_formatter == "mh_structlog_colored":
                        v["formatter"] = "mh_structlog_plain"
                    else:
                        v["formatter"] = selected_formatter
                stdlib_logging_config["handlers"][k] = v
            for k, v in lc.get("formatters", {}).items():
                if k in ["mh_structlog_plain", "mh_structlog_colored", "mh_structlog_json"]:
                    raise StructlogLoggingConfigExceptionError(
                        f"It is not allowed to specify a formatter with the name {k}, since structlog configures that one."
                    )
                stdlib_logging_config["formatters"][k] = v
            for k, v in lc.get("filters", {}).items():
                stdlib_logging_config["filters"][k] = v

    logging.config.dictConfig(stdlib_logging_config)


def filter_named_logger(logger_name: str, level: int) -> dict:
    """Return a dict containing a configuration for a named logger with a certain level filter.

    Use this to silence a named logger by passing this config to the setup() method.
    """
    # fmt: off
    return {
        "loggers": {
            logger_name: {
                "level": level,
                "propagate": False,
            },
        }
    }
    # fmt: on
