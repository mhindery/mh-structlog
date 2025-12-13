from mh_structlog.processors import FieldDropper, FieldRenamer, FieldsAdder, add_flattened_extra


def test_add_flattened_extra_from_structlog_event_dict():
    event_dict = {"_from_structlog": True, "event": "test event", "extra": {"user_id": 123, "session_id": "abc"}}

    result = add_flattened_extra(None, None, event_dict)

    assert result == {"_from_structlog": True, "event": "test event", "user_id": 123, "session_id": "abc"}


def test_add_flattened_extra_from_logging_record():
    class MockRecord:
        def __init__(self):
            # default LogRecord attributes
            self.msg = "test log"
            self.levelname = "INFO"
            # extra attributes
            self.user_id = 456
            self.session_id = "def"

    event_dict = {"_record": MockRecord()}

    result = add_flattened_extra(None, None, event_dict)

    assert result == event_dict | {"user_id": 456, "session_id": "def"}


def test_field_dropper():
    dropper = FieldDropper(fields=["password", "secret"])
    event_dict = {"event": "user login", "user": "alice", "password": "mypassword", "secret": "topsecret"}
    result = dropper(None, None, event_dict)
    assert result == {"event": "user login", "user": "alice"}


def test_field_renamer_enabled():
    renamer = FieldRenamer(enable=True, name_from="old_name", name_to="new_name")
    event_dict = {"event": "data update", "old_name": "value1"}
    result = renamer(None, None, event_dict)
    assert result == {"event": "data update", "new_name": "value1"}


def test_field_adder():
    adder = FieldsAdder(data={"service": "my-service", "env": "production"})
    event_dict = {"event": "startup"}
    result = adder(None, None, event_dict)
    assert result == {"event": "startup", "service": "my-service", "env": "production"}
