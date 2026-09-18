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

import traceback

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from logger import log_error  # pyrefly: ignore [missing-import]
from startup.env import Settings, settings  # pyrefly: ignore [missing-import]


def setup_errors(app: FastAPI, app_settings: Settings = settings) -> None:
    """Register centralized application exception handlers on the FastAPI app."""

    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        log_error(
            error_type="HTTPException",
            message=str(exc.detail),
            status_code=exc.status_code,
            request_id=request_id,
            app_settings=app_settings,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "error": "HTTPException",
                "status_code": exc.status_code,
                "message": exc.detail,
                "request_id": request_id,
            },
            headers=exc.headers,
        )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        errors = exc.errors()
        log_error(
            error_type="RequestValidationError",
            message="Request validation failed",
            status_code=422,
            request_id=request_id,
            details=str(errors),
            app_settings=app_settings,
        )
        return JSONResponse(
            status_code=422,
            content={
                "error": "RequestValidationError",
                "status_code": 422,
                "message": "Validation failed for request parameters or body",
                "details": errors,
                "request_id": request_id,
            },
        )

    @app.exception_handler(Exception)
    async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        request_id = getattr(request.state, "request_id", None)
        trace_details = traceback.format_exc() if app_settings.debug else None
        log_error(
            error_type="InternalServerError",
            message=str(exc),
            status_code=500,
            request_id=request_id,
            details=trace_details,
            app_settings=app_settings,
        )

        message = (
            f"Internal server error: {str(exc)}"
            if app_settings.debug
            else "An unexpected error occurred. Please contact support."
        )

        return JSONResponse(
            status_code=500,
            content={
                "error": "InternalServerError",
                "status_code": 500,
                "message": message,
                "request_id": request_id,
            },
        )
