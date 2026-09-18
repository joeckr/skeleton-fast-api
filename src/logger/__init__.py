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

"""Logging module providing a unified interface across different logger backends."""

from startup.env import Settings, settings  # pyrefly: ignore [missing-import]

from . import none  # pyrefly: ignore [missing-import]

LOGGER_HANDLERS = {
    "none": none,
}


def _get_active_handler(app_settings: Settings = settings):
    return LOGGER_HANDLERS.get(app_settings.log_mode, none)


def log_endpoint(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    client_ip: str | None = None,
    request_id: str | None = None,
    app_settings: Settings = settings,
) -> None:
    """Log an incoming HTTP endpoint call using the active logging handler."""
    handler = _get_active_handler(app_settings)
    handler.log_endpoint(
        method=method,
        path=path,
        status_code=status_code,
        duration_ms=duration_ms,
        client_ip=client_ip,
        request_id=request_id,
    )


def log_auth(
    auth_mode: str,
    status: str,
    user_sub: str | None = None,
    reason: str | None = None,
    request_id: str | None = None,
    app_settings: Settings = settings,
) -> None:
    """Log an authentication event using the active logging handler."""
    handler = _get_active_handler(app_settings)
    handler.log_auth(
        auth_mode=auth_mode,
        status=status,
        user_sub=user_sub,
        reason=reason,
        request_id=request_id,
    )


def log_api(
    method: str,
    url: str,
    status_code: int,
    duration_ms: float,
    request_id: str | None = None,
    app_settings: Settings = settings,
) -> None:
    """Log an outbound third-party API call using the active logging handler."""
    handler = _get_active_handler(app_settings)
    handler.log_api(
        method=method,
        url=url,
        status_code=status_code,
        duration_ms=duration_ms,
        request_id=request_id,
    )


def log_cron(
    job_name: str,
    status: str,
    duration_ms: float,
    details: str | None = None,
    app_settings: Settings = settings,
) -> None:
    """Log a scheduled cron job execution using the active logging handler."""
    handler = _get_active_handler(app_settings)
    handler.log_cron(
        job_name=job_name,
        status=status,
        duration_ms=duration_ms,
        details=details,
    )


def log_error(
    error_type: str,
    message: str,
    status_code: int,
    request_id: str | None = None,
    details: str | None = None,
    app_settings: Settings = settings,
) -> None:
    """Log an application exception or error event using the active logging handler."""
    handler = _get_active_handler(app_settings)
    handler.log_error(
        error_type=error_type,
        message=message,
        status_code=status_code,
        request_id=request_id,
        details=details,
    )
