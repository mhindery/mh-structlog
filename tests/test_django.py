from django.http import HttpRequest

from mh_structlog.django import get_fields_to_log


def test_get_fields_to_log_standard_format(django_settings, serial):
    request = HttpRequest()
    request.method = "GET"
    request.build_absolute_uri = lambda: "http://testserver/test-path"  # ty:ignore[invalid-assignment]
    request.META = {"HTTP_USER_AGENT": "TestAgent"}

    class Response:
        status_code = 200
        headers = {"Content-Length": "1234"}

    response = Response()
    latency_ms = 150

    fields = get_fields_to_log(request, response, latency_ms)  # ty:ignore[invalid-argument-type]

    assert fields == {"latency_ms": 150, "method": "GET", "status": 200, "referrer": '', 'request_user_id': None}


def test_get_fields_to_log_standard_format_with_user(django_settings, serial):
    class User:
        def __init__(self, id):  # noqa: A002
            self.id = id

    request = HttpRequest()
    request.method = "GET"
    request.build_absolute_uri = lambda: "http://testserver/test-path"  # ty:ignore[invalid-assignment]
    request.META = {"HTTP_USER_AGENT": "TestAgent"}
    request.user = User(id=42)  # ty:ignore[unresolved-attribute]

    class Response:
        status_code = 200
        headers = {"Content-Length": "1234"}

    response = Response()
    latency_ms = 150

    fields = get_fields_to_log(request, response, latency_ms)  # ty:ignore[invalid-argument-type]

    assert fields == {"latency_ms": 150, "method": "GET", "status": 200, "referrer": '', 'request_user_id': 42}
