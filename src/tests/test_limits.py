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

from main import create_app
from startup.env import Settings


def test_json_payload_within_limit() -> None:
    """JSON requests within max_json_size should proceed normally."""
    settings = Settings(
        auth_mode="none",
        cron_enabled=False,
        max_json_size=1024,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        resp = client.get("/test")
        assert resp.status_code == 200


def test_json_payload_exceeding_limit() -> None:
    """JSON requests exceeding max_json_size should return 413 PayloadTooLarge envelope."""
    settings = Settings(
        auth_mode="none",
        cron_enabled=False,
        max_json_size=100,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        oversized_data = {"key": "x" * 200}
        resp = client.post("/test", json=oversized_data)
        assert resp.status_code == 413
        data = resp.json()
        assert data["error"] == "PayloadTooLarge"
        assert data["status_code"] == 413
        assert "exceeds limit" in data["message"]
        assert "request_id" in data
        assert resp.headers.get("X-Request-ID") == data["request_id"]


def test_upload_within_limit() -> None:
    """File uploads within max_upload_size should be accepted."""
    settings = Settings(
        auth_mode="none",
        cron_enabled=False,
        max_upload_size=5000,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        small_file = ("test.txt", b"Small content within limit", "text/plain")
        resp = client.post("/documents/upload", files={"file": small_file})
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"
        assert data["document"]["filename"] == "test.txt"


def test_upload_exceeding_limit() -> None:
    """File uploads exceeding max_upload_size should return 413 PayloadTooLarge."""
    settings = Settings(
        auth_mode="none",
        cron_enabled=False,
        max_upload_size=200,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        large_file = ("huge.bin", b"A" * 1000, "application/octet-stream")
        resp = client.post("/documents/upload", files={"file": large_file})
        assert resp.status_code == 413
        data = resp.json()
        assert data["error"] == "PayloadTooLarge"
        assert data["status_code"] == 413
        assert "exceeds limit" in data["message"]
        assert "request_id" in data


def test_generic_request_size_limit() -> None:
    """Non-JSON, non-multipart requests should be bounded by max_request_size."""
    settings = Settings(
        auth_mode="none",
        cron_enabled=False,
        max_request_size=150,
    )
    app = create_app(settings)
    with TestClient(app) as client:
        resp = client.post(
            "/test",
            content=b"raw-bytes-" * 50,
            headers={"Content-Type": "application/octet-stream"},
        )
        assert resp.status_code == 413
        data = resp.json()
        assert data["error"] == "PayloadTooLarge"
        assert data["status_code"] == 413
