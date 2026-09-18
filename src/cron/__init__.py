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

import asyncio
from typing import Any

from logger import log_cron  # pyrefly: ignore [missing-import]
from startup.env import Settings, settings  # pyrefly: ignore [missing-import]

from .heartbeat import run_heartbeat  # pyrefly: ignore [missing-import]


async def _heartbeat_worker(app_settings: Settings) -> None:
    """Run the heartbeat job in a periodic loop according to configured interval."""
    while True:
        try:
            await run_heartbeat(app_settings)
        except Exception as exc:
            log_cron("heartbeat", "failed", 0.0, str(exc), app_settings)
        await asyncio.sleep(app_settings.cron_heartbeat_interval)


def start_cron_tasks(app_settings: Settings = settings) -> list[asyncio.Task[Any]]:
    """Spawn background asyncio tasks for all enabled scheduled jobs."""
    if not app_settings.cron_enabled:
        return []

    return [
        asyncio.create_task(_heartbeat_worker(app_settings), name="cron_heartbeat"),
    ]


async def stop_cron_tasks(tasks: list[asyncio.Task[Any]]) -> None:
    """Gracefully cancel and await all running background cron tasks."""
    for task in tasks:
        task.cancel()
    if tasks:
        await asyncio.gather(*tasks, return_exceptions=True)
