import time

import structlog
from django.http import HttpRequest


class StructLogAccessLoggingMiddleware:
    """Perform access logging using the structlog logger."""

    def __init__(self, get_response):  # noqa: D107
        self.get_response = get_response
        self.logger = structlog.getLogger("mh_structlog.django.access")

    def __call__(self, request: HttpRequest):
        """Create an access log of the request/response."""
        from mh_structlog.config import SELECTED_LOG_FORMAT  # noqa: PLC0415

        start = time.time()
        response = self.get_response(request)
        end = time.time()

        latency_ms = int(1000 * (end - start))

        request_path = request.get_full_path()

        fields_to_log = {'latency_ms': latency_ms, 'method': request.method, 'status': response.status_code}

        if SELECTED_LOG_FORMAT == 'gcp_json':
            fields_to_log['httpRequest'] = {
                'requestMethod': request.method,
                'requestUrl': request.build_absolute_uri(),
                'status': response.status_code,
                'latency': f"{latency_ms / 1000}s",
                "userAgent": request.headers.get('User-Agent', ''),
                "responseSize": str(response.headers.get('Content-Length', 0)),
            }

        if response.status_code >= 500:  # noqa: PLR2004
            self.logger.error(request_path, **fields_to_log)
        elif response.status_code >= 400:  # noqa: PLR2004
            self.logger.warning(request_path, **fields_to_log)
        else:
            self.logger.info(request_path, **fields_to_log)

        return response
