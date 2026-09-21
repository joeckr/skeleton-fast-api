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

from collections.abc import Callable

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from logger import log_error  # pyrefly: ignore [missing-import]
from startup.env import Settings, settings


class PayloadLimitMiddleware(BaseHTTPMiddleware):
    """Middleware for enforcing maximum payload size limits on incoming HTTP requests."""

    def __init__(self, app: FastAPI, app_settings: Settings = settings):
        super().__init__(app)
        self.settings = app_settings

    def _resolve_limit(self, content_type: str) -> int:
        """Resolve maximum permitted byte size based on Content-Type."""
        ct = content_type.lower()
        if ct.startswith("multipart/form-data"):
            return self.settings.max_upload_size
        if ct.startswith("application/json"):
            return self.settings.max_json_size
        return self.settings.max_request_size

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        content_type = request.headers.get("content-type", "")
        limit = self._resolve_limit(content_type)

        # 1. Early rejection based on Content-Length header
        content_length_header = request.headers.get("content-length")
        if content_length_header is not None:
            try:
                content_length = int(content_length_header)
            except ValueError:
                content_length = 0

            if content_length > limit:
                request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")
                log_error(
                    error_type="PayloadTooLarge",
                    message=f"Request payload of {content_length} bytes exceeds limit of {limit} bytes",
                    status_code=413,
                    request_id=request_id,
                    app_settings=self.settings,
                )
                headers = {"X-Request-ID": request_id} if request_id else None
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "PayloadTooLarge",
                        "status_code": 413,
                        "message": f"Request payload of {content_length} bytes exceeds limit of {limit} bytes",
                        "request_id": request_id,
                    },
                    headers=headers,
                )

        # 2. Guard chunked and streaming requests by monitoring bytes received
        original_receive = request._receive
        bytes_received = 0

        async def limited_receive():
            nonlocal bytes_received
            message = await original_receive()
            if message["type"] == "http.request":
                bytes_received += len(message.get("body", b""))
                if bytes_received > limit:
                    raise HTTPException(
                        status_code=413,
                        detail=f"Request payload exceeds limit of {limit} bytes",
                    )
            return message

        request._receive = limited_receive

        try:
            return await call_next(request)
        except HTTPException as exc:
            if exc.status_code == 413:
                request_id = getattr(request.state, "request_id", None) or request.headers.get("X-Request-ID")
                log_error(
                    error_type="PayloadTooLarge",
                    message=str(exc.detail),
                    status_code=413,
                    request_id=request_id,
                    app_settings=self.settings,
                )
                headers = {"X-Request-ID": request_id} if request_id else None
                return JSONResponse(
                    status_code=413,
                    content={
                        "error": "PayloadTooLarge",
                        "status_code": 413,
                        "message": str(exc.detail),
                        "request_id": request_id,
                    },
                    headers=headers,
                )
            raise exc


def setup_limits(app: FastAPI, app_settings: Settings = settings) -> None:
    """Register PayloadLimitMiddleware on the FastAPI application."""
    app.add_middleware(PayloadLimitMiddleware, app_settings=app_settings)
