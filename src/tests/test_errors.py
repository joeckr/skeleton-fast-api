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

from fastapi import HTTPException
from fastapi.testclient import TestClient
from pydantic import BaseModel

from main import create_app
from startup.env import Settings


def test_404_error_envelope(client: TestClient) -> None:
    """Non-existent endpoints should return standardized 404 envelope with request_id."""
    resp = client.get("/does-not-exist")
    assert resp.status_code == 404
    data = resp.json()
    assert data["error"] == "HTTPException"
    assert data["status_code"] == 404
    assert "Not Found" in data["message"]
    assert "request_id" in data
    assert resp.headers.get("X-Request-ID") == data["request_id"]


def test_422_validation_error_envelope() -> None:
    """Request validation failures should return standardized 422 envelope with details."""
    settings = Settings(auth_mode="none", cron_enabled=False)
    app = create_app(settings)

    class Payload(BaseModel):
        count: int

    @app.post("/test-validation")
    def sample_endpoint(payload: Payload) -> dict[str, int]:
        return {"count": payload.count}

    with TestClient(app) as test_client:
        resp = test_client.post("/test-validation", json={"count": "not-an-integer"})
        assert resp.status_code == 422
        data = resp.json()
        assert data["error"] == "RequestValidationError"
        assert data["status_code"] == 422
        assert "details" in data
        assert isinstance(data["details"], list)
        assert "request_id" in data


def test_500_internal_error_envelope() -> None:
    """Unhandled exceptions in production return sanitized 500 error envelope."""
    settings = Settings(auth_mode="none", cron_enabled=False, debug=False)
    app = create_app(settings)

    @app.get("/test-500")
    def broken_endpoint() -> None:
        raise RuntimeError("Database connection suddenly dropped")

    with TestClient(app, raise_server_exceptions=False) as test_client:
        resp = test_client.get("/test-500")
        assert resp.status_code == 500
        data = resp.json()
        assert data["error"] == "InternalServerError"
        assert data["status_code"] == 500
        assert "unexpected error" in data["message"].lower()
        assert "request_id" in data


def test_custom_http_exception_envelope() -> None:
    """Explicit Starlette/FastAPI HTTPExceptions return formatted envelope."""
    settings = Settings(auth_mode="none", cron_enabled=False)
    app = create_app(settings)

    @app.get("/test-custom-http")
    def custom_http_endpoint() -> None:
        raise HTTPException(status_code=403, detail="Custom access restriction")

    with TestClient(app) as test_client:
        resp = test_client.get("/test-custom-http")
        assert resp.status_code == 403
        data = resp.json()
        assert data["error"] == "HTTPException"
        assert data["status_code"] == 403
        assert data["message"] == "Custom access restriction"
        assert "request_id" in data
