from django.conf import settings
from django.http import HttpRequest
from django.test.utils import setup_test_environment

from mh_structlog.django import get_fields_to_log


def test_get_fields_to_log_standard_format():
    settings.configure()
    setup_test_environment(debug=True)

    request = HttpRequest()
    request.method = "GET"
    request.build_absolute_uri = lambda: "http://testserver/test-path"
    request.headers = {"User-Agent": "TestAgent"}

    class Response:
        status_code = 200
        headers = {"Content-Length": "1234"}

    response = Response()
    latency_ms = 150

    fields = get_fields_to_log(request, response, latency_ms)

    assert fields == {"latency_ms": 150, "method": "GET", "status": 200, "referrer": ''}
