from structlog.typing import EventDict
from structlog_sentry import SentryProcessor as _SentryProcessor


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
