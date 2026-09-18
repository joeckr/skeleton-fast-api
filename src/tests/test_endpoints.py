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

from fastapi.testclient import TestClient


def test_test_endpoint(client: TestClient) -> None:
    """Test the /test diagnostic endpoint."""
    resp = client.get("/test")
    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "ok"
    assert data["message"] == "Backend is reachable"
    assert "X-Request-ID" in resp.headers


def test_config_endpoint(client: TestClient) -> None:
    """Test the /config endpoint returns sanitized configuration."""
    resp = client.get("/config")
    assert resp.status_code == 200
    data = resp.json()
    assert data["app_name"] == "test-skeleton-fast-api"
    assert data["app_env"] == "test"
    assert data["auth_mode"] == "none"
    assert "basic_auth_password" not in data
    assert "password" not in str(data).lower()


def test_user_me_endpoint(client: TestClient) -> None:
    """Test the /me user profile endpoint."""
    resp = client.get("/me")
    assert resp.status_code == 200
    data = resp.json()
    assert "user" in data
    assert data["user"]["username"] == "anonymous"
    assert data["user"]["id"] == "anonymous"
