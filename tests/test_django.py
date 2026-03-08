import orjson
from django.http import HttpRequest
from freezegun import freeze_time

import mh_structlog
from mh_structlog import filter_named_logger, setup
from mh_structlog.django import get_fields_to_log

from .utils import capture_output


def test_get_fields_to_log_json_format(django_settings, serial):
    setup(log_format='json', testing_mode=True)

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


def test_get_fields_to_log_gcp_json_format(django_settings, serial):
    setup(log_format='gcp_json', testing_mode=True)

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

    assert fields == {
        "latency_ms": 150,
        "method": "GET",
        "status": 200,
        "referrer": '',
        'request_user_id': None,
        'httpRequest': {
            'latency': '0.15s',
            'requestMethod': 'GET',
            'requestUrl': 'http://testserver/test-path',
            'responseSize': '1234',
            'status': 200,
            'userAgent': 'TestAgent',
        },
    }


def test_get_fields_to_log_standard_format_with_user(django_settings, serial):
    setup(log_format='json', testing_mode=True)

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


@freeze_time("2025-12-11 12:01:02")
def test_middleware_on_request(django_settings, settings, serial, client):
    settings.MIDDLEWARE = ["mh_structlog.django.StructLogAccessLoggingMiddleware"]

    with capture_output() as (out, _err):
        setup(testing_mode=True, log_format='json', global_filter_level=mh_structlog.INFO)
        response = client.get("/")
        assert response.status_code == 200

    data = orjson.loads(out.getvalue())

    assert data == {
        'latency_ms': 0,
        'level': 'info',
        'logger': 'mh_structlog.django.access',
        'message': '/',
        'method': 'GET',
        'referrer': '',
        'request_user_id': None,
        'status': 200,
        'timestamp': '2025-12-11T12:01Z',
    }


@freeze_time("2025-12-11 12:01:02")
def test_middleware_on_notfound(django_settings, settings, serial, client):
    settings.MIDDLEWARE = ["mh_structlog.django.StructLogAccessLoggingMiddleware"]

    with capture_output() as (out, _err):
        setup(
            testing_mode=True,
            log_format='json',
            global_filter_level=mh_structlog.INFO,
            logging_configs=[filter_named_logger('django', level=mh_structlog.ERROR)],
        )
        response = client.get("notfound")
        assert response.status_code == 404

    data = orjson.loads(out.getvalue())

    assert data == {
        'latency_ms': 0,
        'level': 'warning',
        'logger': 'mh_structlog.django.access',
        'message': '/notfound',
        'method': 'GET',
        'referrer': '',
        'request_user_id': None,
        'status': 404,
        'timestamp': '2025-12-11T12:01Z',
    }
