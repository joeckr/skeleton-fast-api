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

logger = logging.getLogger("skeleton.console")


def log_endpoint(
    method: str,
    path: str,
    status_code: int,
    duration_ms: float,
    client_ip: str | None = None,
    request_id: str | None = None,
) -> None:
    """Log incoming HTTP request execution details to the console."""
    extra = f"[{request_id}] " if request_id else ""
    ip = f"{client_ip} - " if client_ip else ""
    logger.info(f"{extra}{ip}{method} {path} -> {status_code} ({duration_ms:.2f}ms)")


def log_auth(
    auth_mode: str,
    status: str,
    user_sub: str | None = None,
    reason: str | None = None,
    request_id: str | None = None,
) -> None:
    """Log authentication attempts and outcomes to the console."""
    extra = f"[{request_id}] " if request_id else ""
    user = f"user='{user_sub}'" if user_sub else "anonymous"
    detail = f" - reason: {reason}" if reason else ""
    level = logging.INFO if status.lower() == "success" else logging.WARNING
    logger.log(
        level,
        f"{extra}AUTH [{auth_mode}] -> {status.upper()} ({user}){detail}",
    )


def log_api(
    method: str,
    url: str,
    status_code: int,
    duration_ms: float,
    request_id: str | None = None,
) -> None:
    """Log outbound third-party API requests to the console."""
    extra = f"[{request_id}] " if request_id else ""
    logger.info(f"{extra}OUTBOUND API {method} {url} -> {status_code} ({duration_ms:.2f}ms)")


def log_cron(
    job_name: str,
    status: str,
    duration_ms: float,
    details: str | None = None,
) -> None:
    """Log scheduled cron job execution details to the console."""
    level = logging.INFO if status.lower() == "success" else logging.ERROR
    extra = f" - {details}" if details else ""
    logger.log(
        level,
        f"CRON [{job_name}] -> {status.upper()} in {duration_ms:.2f}ms{extra}",
    )


def log_error(
    error_type: str,
    message: str,
    status_code: int,
    request_id: str | None = None,
    details: str | None = None,
) -> None:
    """Log an application exception or error event to the console."""
    extra = f"[{request_id}] " if request_id else ""
    detail_str = f" | Details: {details}" if details else ""
    logger.error(f"{extra}ERROR [{error_type}] -> HTTP {status_code}: {message}{detail_str}")
