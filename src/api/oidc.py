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

import ssl
import time
from functools import lru_cache

import httpx
from jwt import PyJWKClient

from logger import log_api  # pyrefly: ignore [missing-import]


@lru_cache(maxsize=4)
def get_jwks_client(issuer_url: str, ssl_verify: bool = True) -> PyJWKClient:
    issuer = issuer_url.rstrip("/")
    discovery_url = f"{issuer}/.well-known/openid-configuration"

    start_time = time.perf_counter()
    status_code = 0
    try:
        with httpx.Client(verify=ssl_verify, timeout=10.0) as client:
            response = client.get(discovery_url)
            status_code = response.status_code
            response.raise_for_status()
            jwks_uri = response.json().get("jwks_uri")
    except Exception as exc:
        if hasattr(exc, "response") and exc.response:
            status_code = exc.response.status_code
        jwks_uri = f"{issuer}/.well-known/jwks.json"
    finally:
        duration_ms = (time.perf_counter() - start_time) * 1000
        log_api(
            method="GET",
            url=discovery_url,
            status_code=status_code,
            duration_ms=duration_ms,
        )

    ssl_context = None
    if not ssl_verify:
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE

    return PyJWKClient(
        jwks_uri,
        cache_keys=True,
        ssl_context=ssl_context,
    )
