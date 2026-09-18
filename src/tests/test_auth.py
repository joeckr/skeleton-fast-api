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

import base64

from fastapi.testclient import TestClient


def test_auth_none_mode_permits_access(client: TestClient) -> None:
    """When auth_mode is none, all endpoints should permit access without credentials."""
    resp = client.get("/me")
    assert resp.status_code == 200
    data = resp.json()
    assert "user" in data
    assert data["user"]["auth_mode"] == "none"
    assert data["user"]["username"] == "anonymous"


def test_basic_auth_unauthenticated_rejected(basic_client: TestClient) -> None:
    """When auth_mode is basic, unauthenticated requests to protected endpoints receive 401."""
    resp = basic_client.get("/me")
    assert resp.status_code == 401
    assert "WWW-Authenticate" in resp.headers


def test_basic_auth_invalid_credentials_rejected(basic_client: TestClient) -> None:
    """When auth_mode is basic, invalid credentials receive 401."""
    invalid_creds = base64.b64encode(b"wronguser:wrongpass").decode("utf-8")
    headers = {"Authorization": f"Basic {invalid_creds}"}
    resp = basic_client.get("/me", headers=headers)
    assert resp.status_code == 401


def test_basic_auth_valid_credentials_accepted(basic_client: TestClient) -> None:
    """When auth_mode is basic, valid credentials return 200 and user payload."""
    valid_creds = base64.b64encode(b"testadmin:testpass").decode("utf-8")
    headers = {"Authorization": f"Basic {valid_creds}"}
    resp = basic_client.get("/me", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "user" in data
    assert data["user"]["username"] == "testadmin"
    assert data["user"]["id"] == "testadmin"
    assert data["user"]["auth_mode"] == "basic"


def test_cors_preflight_bypasses_auth(basic_client: TestClient) -> None:
    """OPTIONS preflight requests should not require authentication even in basic auth mode."""
    headers = {
        "Origin": "http://localhost:3000",
        "Access-Control-Request-Method": "GET",
    }
    resp = basic_client.options("/me", headers=headers)
    assert resp.status_code == 200
