import logging

import orjson
import structlog
from structlog.processors import CallsiteParameter
from structlog.typing import EventDict
from structlog_sentry import SentryProcessor as _SentryProcessor


# Inspect a default logging library record so we can find out which keys on a LogRecord are 'extra' and not default ones.
_LOG_RECORD_KEYS = set(logging.LogRecord("name", 0, "pathname", 0, "msg", (), None).__dict__.keys())


def add_flattened_extra(_, __, event_dict: dict) -> dict:  # noqa: ANN001
    """Include the content of 'extra' in the output log, flattened the attributes."""
    if event_dict.get("_from_structlog"):
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


def render_orjson(logger: structlog.BoundLogger, name: str, event_dict: dict) -> str:  # noqa: ARG001
    """Render the event_dict as a json string using orjson."""
    return orjson.dumps(event_dict, default=repr).decode()


class FieldRenamer:
    """Rename fields in the event dict."""

    def __init__(self, enable: bool, name_from: str, name_to: str):  # noqa: D107
        self.enable = enable
        self.name_from = name_from
        self.name_to = name_to

    def __call__(self, logger: logging.Logger, name: str, event_dict: EventDict) -> EventDict:  # noqa: D102,ARG001,ARG002
        if self.enable and self.name_from in event_dict:
            event_dict[self.name_to] = event_dict.pop(self.name_from)

        return event_dict


class CapExceptionFrames:
    """Limit the number of frames in the exception traceback.

    With the builtin ConsoleRenderer, this can be given as argument (max_frames), but not when dict_tracebacks is used.
    """

    def __init__(self, max_frames: int):
        """Set the max number of frames to keep in exception tracebacks."""
        self.max_frames = max_frames

    def __call__(self, logger: structlog.BoundLogger, name: str, event_dict: EventDict) -> EventDict:  # noqa: ARG002, D102
        if self.max_frames is not None and 'exception' in event_dict and 'frames' in event_dict["exception"]:
            event_dict['exception']['frames'] = event_dict['exception']['frames'][-self.max_frames :]
        return event_dict


class SentryProcessor(_SentryProcessor):
    """The SentryProcessor but with some of our own defaults and slight customization applied."""

    def __init__(self, **kwargs):  # noqa: D107
        # Unless otherwise specified, add all extra attributes from the log to Sentry as tags.
        # Explicitly pass tag_keys=None to avoid this behaviour.
        if 'tag_keys' not in kwargs:
            kwargs['tag_keys'] = '__all__'
        super().__init__(**kwargs)

    def _get_event_and_hint(self, event_dict: EventDict) -> tuple[dict, dict]:
        """Filter out tag_keys which are not primitive types, because Sentry gives an error otherwise."""

        event, hint = super()._get_event_and_hint(event_dict)

        if 'tags' in event:
            for k in list(event['tags'].keys()):
                if not isinstance(event['tags'][k], (bool, str, int, float, type(None))):  # noqa: UP038
                    del event['tags'][k]

        return event, hint
