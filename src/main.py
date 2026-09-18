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

from fastapi import FastAPI

from startup.auth import setup_auth
from startup.cors import setup_cors
from startup.cron import lifespan
from startup.endpoints import setup_endpoints
from startup.env import Settings, get_settings
from startup.errors import setup_errors
from startup.logging import setup_logging


def create_app(app_settings: Settings | None = None) -> FastAPI:
    """Application factory for configuring FastAPI instances."""
    cfg = app_settings or get_settings()
    app = FastAPI(
        title=cfg.app_name,
        debug=cfg.debug,
        lifespan=lifespan,
    )
    app.state.settings = cfg
    if app_settings:
        app.dependency_overrides[get_settings] = lambda: app_settings

    setup_errors(app, app_settings=cfg)
    setup_auth(app, app_settings=cfg)
    setup_logging(app, app_settings=cfg)
    setup_cors(app, app_settings=cfg)
    setup_endpoints(app)
    return app


app = create_app()
