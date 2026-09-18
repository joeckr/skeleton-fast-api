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
from typing import Any

from fastapi import FastAPI, HTTPException, Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from auth import basic, none, oidc
from logger import log_auth  # pyrefly: ignore [missing-import]
from startup.env import Settings, settings

AUTH_STRATEGIES = {
    "none": none.authenticate,
    "basic": basic.authenticate,
    "oidc": oidc.authenticate,
}

# Endpoints that bypass authentication (strictly Kubernetes health probes)
EXCLUDED_PATHS = {
    "/health/live",
    "/health/ready",
}


class AuthenticationMiddleware(BaseHTTPMiddleware):
    def __init__(self, app: FastAPI, app_settings: Settings = settings):
        super().__init__(app)
        self.settings = app_settings

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 1. Skip auth for CORS preflight (OPTIONS) requests
        if request.method == "OPTIONS":
            return await call_next(request)

        # 2. Skip auth for listed endpoints
        path = request.url.path
        if path in EXCLUDED_PATHS:
            return await call_next(request)

        # 3. Resolve authentication strategy
        authenticator = AUTH_STRATEGIES.get(self.settings.auth_mode)
        if not authenticator:
            return JSONResponse(
                status_code=500,
                content={"detail": f"Unsupported auth_mode '{self.settings.auth_mode}' configured"},
            )

        # 4. Authenticate request
        request_id = getattr(request.state, "request_id", None)
        try:
            user = await authenticator(request, self.settings)
            request.state.user = user
            log_auth(
                auth_mode=self.settings.auth_mode,
                status="success",
                user_sub=user.get("sub"),
                request_id=request_id,
                app_settings=self.settings,
            )
        except HTTPException as exc:
            log_auth(
                auth_mode=self.settings.auth_mode,
                status="failure",
                reason=exc.detail,
                request_id=request_id,
                app_settings=self.settings,
            )
            return JSONResponse(
                status_code=exc.status_code,
                content={"detail": exc.detail},
                headers=exc.headers,
            )
        except Exception as exc:
            log_auth(
                auth_mode=self.settings.auth_mode,
                status="error",
                reason=str(exc),
                request_id=request_id,
                app_settings=self.settings,
            )
            return JSONResponse(
                status_code=500,
                content={"detail": f"Internal authentication error: {str(exc)}"},
            )

        return await call_next(request)


def setup_auth(app: FastAPI, app_settings: Settings = settings) -> None:
    """Register the centralized authentication middleware on the application."""
    app.add_middleware(AuthenticationMiddleware, app_settings=app_settings)


def get_current_user(request: Request) -> dict[str, Any]:
    """FastAPI Dependency for endpoints to retrieve the authenticated user payload.

    Example:
        @app.get("/me")
        def me(user: dict = Depends(get_current_user)):
            return user
    """
    return getattr(request.state, "user", None) or {
        "sub": "anonymous",
        "username": "anonymous",
        "auth_mode": "none",
    }
