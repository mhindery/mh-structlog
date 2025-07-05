import time

import structlog
from asgiref.sync import iscoroutinefunction
from django.http import HttpRequest, HttpResponse
from django.utils.decorators import sync_and_async_middleware

from mh_structlog.config import SELECTED_LOG_FORMAT  # noqa: PLC0415


logger = structlog.getLogger("mh_structlog.django.access")


def get_fields_to_log(request: HttpRequest, response: HttpResponse, latency_ms: int) -> dict:
    """Extracts fields to log from the request object."""

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

    return fields_to_log


@sync_and_async_middleware
def StructLogAccessLoggingMiddleware(get_response):  # noqa: N802
    """Middleware that logs access requests with some extra fields as structured logs."""

    if iscoroutinefunction(get_response):

        async def middleware(request):
            start = time.time()
            response = await get_response(request)
            end = time.time()

            latency_ms = int(1000 * (end - start))
            fields_to_log = get_fields_to_log(request, response, latency_ms)

            # in case Sentry is enabled, prevent logging to it.
            # The actual exception will be logged if necessary somewhere else, but the response access log to the client should not be on there.

            if response.status_code >= 500:  # noqa: PLR2004
                await logger.aerror(request.get_full_path(), sentry_skip=True, **fields_to_log)
            elif response.status_code >= 400:  # noqa: PLR2004
                await logger.awarning(request.get_full_path(), sentry_skip=True, **fields_to_log)
            else:
                await logger.ainfo(request.get_full_path(), **fields_to_log)

            return response

    else:

        def middleware(request):
            start = time.time()
            response = get_response(request)
            end = time.time()

            latency_ms = int(1000 * (end - start))
            fields_to_log = get_fields_to_log(request, response, latency_ms)

            # in case Sentry is enabled, prevent logging to it.
            # The actual exception will be logged if necessary somewhere else, but the response access log to the client should not be on there.

            if response.status_code >= 500:  # noqa: PLR2004
                logger.error(request.get_full_path(), sentry_skip=True, **fields_to_log)
            elif response.status_code >= 400:  # noqa: PLR2004
                logger.warning(request.get_full_path(), sentry_skip=True, **fields_to_log)
            else:
                logger.info(request.get_full_path(), **fields_to_log)

            return response

    return middleware
