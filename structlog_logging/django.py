import time

import structlog


class StructLogAccessLoggingMiddleware:
    """Perform access logging using the structlog logger."""

    def __init__(self, get_response):  # noqa: D107
        self.get_response = get_response
        self.logger = structlog.getLogger("mh_structlog.django.access")

    def __call__(self, request):
        """Create an access log of the request/response."""
        start = time.time()
        response = self.get_response(request)
        end = time.time()

        latency_ms = 1000 * (end - start)

        if response.status_code >= 500:
            self.logger.error(
                request.get_full_path(),
                latency=f"{int(latency_ms)}ms",
                method=request.method,
                status=response.status_code,
            )
        elif response.status_code >= 400:
            self.logger.warning(
                request.get_full_path(),
                latency=f"{int(latency_ms)}ms",
                method=request.method,
                status=response.status_code,
            )
        else:
            self.logger.info(
                request.get_full_path(),
                latency=f"{int(latency_ms)}ms",
                method=request.method,
                status=response.status_code,
            )

        # Code to be executed for each request/response after
        # the view is called.

        return response
