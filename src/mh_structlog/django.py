import time

import structlog
from asgiref.sync import iscoroutinefunction
from django.http import HttpRequest, HttpResponse
from django.http.response import HttpResponseRedirectBase
from django.utils.decorators import sync_and_async_middleware

from mh_structlog import config  # ruff: ignore[noqa-comments]


logger = structlog.getLogger("mh_structlog.django.access")


async def a_get_fields_to_log(request: HttpRequest, response: HttpResponse, latency_ms: int) -> dict:
    """Extracts fields to log from the request object."""

    request_user_id = None
    if (user := await request.auser()).is_authenticated:  # ty: ignore[unresolved-attribute]
        request_user_id = user.id

    fields_to_log = {
        'latency_ms': latency_ms,
        'method': request.method,
        'status': response.status_code,
        'referrer': request.headers.get('Referer', ''),
        'request_user_id': request_user_id,
    }

    if isinstance(response, HttpResponseRedirectBase):
        fields_to_log['redirect_url'] = response['Location']

    if config.SELECTED_LOG_FORMAT == 'gcp_json':
        fields_to_log['httpRequest'] = {
            'requestMethod': request.method,
            'requestUrl': request.build_absolute_uri(),
            'status': response.status_code,
            'latency': f"{latency_ms / 1000}s",
            "userAgent": request.headers.get('User-Agent', ''),
            "responseSize": str(response.headers.get('Content-Length', 0)),
        }

    return fields_to_log


def get_fields_to_log(request: HttpRequest, response: HttpResponse, latency_ms: int) -> dict:
    """Extracts fields to log from the request object."""

    request_user_id = None
    if request.user.is_authenticated:  # ty: ignore[unresolved-attribute]
        request_user_id = request.user.id  # ty: ignore[unresolved-attribute]

    fields_to_log = {
        'latency_ms': latency_ms,
        'method': request.method,
        'status': response.status_code,
        'referrer': request.headers.get('Referer', ''),
        'request_user_id': request_user_id,
    }

    if isinstance(response, HttpResponseRedirectBase):
        fields_to_log['redirect_url'] = response['Location']

    if config.SELECTED_LOG_FORMAT == 'gcp_json':
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
def StructLogAccessLoggingMiddleware(get_response):  # ruff: ignore[invalid-function-name]
    """Middleware that logs access requests with some extra fields as structured logs."""

    if iscoroutinefunction(get_response):

        async def middleware(request):
            start = time.time()
            response = await get_response(request)
            end = time.time()

            latency_ms = int(1000 * (end - start))
            fields_to_log = await a_get_fields_to_log(request, response, latency_ms)

            # in case Sentry is enabled, prevent logging to it.
            # The actual exception will be logged if necessary somewhere else, but the response access log to the client should not be on there.

            if response.status_code >= 500:  # ruff: ignore[magic-value-comparison]
                await logger.aerror(request.get_full_path(), sentry_skip=True, **fields_to_log)
            elif response.status_code >= 400:  # ruff: ignore[magic-value-comparison]
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

            if response.status_code >= 500:  # ruff: ignore[magic-value-comparison]
                logger.error(request.get_full_path(), sentry_skip=True, **fields_to_log)
            elif response.status_code >= 400:  # ruff: ignore[magic-value-comparison]
                logger.warning(request.get_full_path(), sentry_skip=True, **fields_to_log)
            else:
                logger.info(request.get_full_path(), **fields_to_log)

            return response

    return middleware
