from collections.abc import Mapping
from dataclasses import dataclass

from pydantic import BaseModel

from mh_structlog.processors import (
    FieldDropper,
    FieldRenamer,
    FieldsAdder,
    FieldTransformer,
    ObjectToDictTransformer,
    add_flattened_extra,
    cap_timestamp_to_ms_precision,
)


def test_add_flattened_extra_from_structlog_event_dict():
    event_dict = {"_from_structlog": True, "event": "test event", "extra": {"user_id": 123, "session_id": "abc"}}

    result = add_flattened_extra(None, None, event_dict)

    assert result == {"_from_structlog": True, "event": "test event", "user_id": 123, "session_id": "abc"}


def test_cap_timestamp_to_ms_precision():
    event_dict = {"event": "test event", "timestamp": "2024-06-01T12:34:56.789123Z"}

    result = cap_timestamp_to_ms_precision(None, None, event_dict)

    assert result == {"event": "test event", "timestamp": "2024-06-01T12:34:56.789Z"}


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


def test_field_transformer_enabled():
    transformer = FieldTransformer(enable=True, field_name="level", transform_function=lambda v: v.upper())
    event_dict = {"event": "system alert", "level": "warning"}
    result = transformer(None, None, event_dict)
    assert result == {"event": "system alert", "level": "WARNING"}


def test_object_to_dict_transformer_basemodel():
    class MyModel(BaseModel):
        id: int
        name: str

    obj = MyModel(id=123, name="alice")

    transformer = ObjectToDictTransformer()
    event_dict = {"event": "user data", "obj": obj}
    result = transformer(None, None, event_dict)
    assert result == {"event": "user data", "obj": {"id": 123, "name": "alice"}}


def test_object_to_dict_transformer_mapping():
    class MyModel(dict, Mapping):
        id: int
        name: str

    obj = MyModel(id=123, name="alice")

    transformer = ObjectToDictTransformer()
    event_dict = {"event": "user data", "obj": obj}
    result = transformer(None, None, event_dict)
    assert result == {"event": "user data", "obj": {"id": 123, "name": "alice"}}


def test_object_to_dict_transformer_dataclass():
    @dataclass
    class MyModel:
        id: int
        name: str

    obj = MyModel(id=123, name="alice")

    transformer = ObjectToDictTransformer()
    event_dict = {"event": "user data", "obj": obj}
    result = transformer(None, None, event_dict)
    assert result == {"event": "user data", "obj": {"id": 123, "name": "alice"}}
