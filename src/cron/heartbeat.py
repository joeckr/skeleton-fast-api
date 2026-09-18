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

import time

from logger import log_cron  # pyrefly: ignore [missing-import]
from startup.env import Settings  # pyrefly: ignore [missing-import]

# Record process start time to compute uptime
PROCESS_START_TIME = time.time()


async def run_heartbeat(app_settings: Settings) -> None:
    """Execute the heartbeat diagnostic cron job."""
    start = time.perf_counter()
    try:
        uptime_seconds = int(time.time() - PROCESS_START_TIME)
        duration_ms = (time.perf_counter() - start) * 1000
        log_cron(
            job_name="heartbeat",
            status="success",
            duration_ms=duration_ms,
            details=f"Uptime: {uptime_seconds}s | Environment: {app_settings.app_env}",
            app_settings=app_settings,
        )
    except Exception as exc:
        duration_ms = (time.perf_counter() - start) * 1000
        log_cron(
            job_name="heartbeat",
            status="failed",
            duration_ms=duration_ms,
            details=str(exc),
            app_settings=app_settings,
        )
