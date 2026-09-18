# Copyright (c) 2026 Joseph Christopher King
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

import logging
import sys
import time
import uuid
from collections.abc import Callable

from fastapi import FastAPI, Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from logger import log_endpoint  # pyrefly: ignore [missing-import]
from startup.env import Settings, settings


def configure_logger(app_settings: Settings = settings) -> None:
    """Configure base console logging format and log levels based on environment settings."""
    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(
        level=getattr(logging, app_settings.log_level.upper(), logging.INFO),
        format=log_format,
        handlers=[logging.StreamHandler(sys.stdout)],
        force=True,
    )
    logging.getLogger("skeleton").setLevel(getattr(logging, app_settings.log_level.upper(), logging.INFO))


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for tracking request latency, request IDs, and logging endpoint metrics."""

    def __init__(self, app: FastAPI, app_settings: Settings = settings):
        super().__init__(app)
        self.settings = app_settings

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Extract incoming X-Request-ID or generate a new correlation ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        request.state.request_id = request_id

        start_time = time.perf_counter()

        try:
            response = await call_next(request)
        except Exception as exc:
            duration_ms = (time.perf_counter() - start_time) * 1000
            log_endpoint(
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration_ms=duration_ms,
                client_ip=request.client.host if request.client else None,
                request_id=request_id,
                app_settings=self.settings,
            )
            raise exc

        duration_ms = (time.perf_counter() - start_time) * 1000

        # Inject X-Request-ID into outgoing response headers
        response.headers["X-Request-ID"] = request_id

        # Log endpoint outcome
        log_endpoint(
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=duration_ms,
            client_ip=request.client.host if request.client else None,
            request_id=request_id,
            app_settings=self.settings,
        )

        return response


def setup_logging(app: FastAPI, app_settings: Settings = settings) -> None:
    """Initialize logging configuration and register the LoggingMiddleware."""
    configure_logger(app_settings)
    app.add_middleware(LoggingMiddleware, app_settings=app_settings)
