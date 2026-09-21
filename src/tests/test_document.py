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


def test_document_upload_success(client: TestClient) -> None:
    """Test successful document upload with description."""
    file_payload = ("test_doc.txt", b"Hello, document ingestion!", "text/plain")
    data_payload = {"description": "Sample report"}

    resp = client.post("/documents/upload", files={"file": file_payload}, data=data_payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    doc = body["document"]
    assert doc["filename"] == "test_doc.txt"
    assert doc["content_type"] == "text/plain"
    assert doc["size_bytes"] == len(b"Hello, document ingestion!")
    assert doc["description"] == "Sample report"
    assert doc["status"] == "received"


def test_document_upload_missing_file(client: TestClient) -> None:
    """Missing required file field should trigger 422 RequestValidationError."""
    resp = client.post("/documents/upload", data={"description": "Missing file payload"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"] == "RequestValidationError"
    assert body["status_code"] == 422


def test_form_submission_success(client: TestClient) -> None:
    """Test successful form data submission."""
    form_data = {
        "title": "Quarterly Update",
        "content": "All systems operational.",
        "category": "engineering",
    }
    resp = client.post("/documents/form", data=form_data)
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    data = body["data"]
    assert data["title"] == "Quarterly Update"
    assert data["content"] == "All systems operational."
    assert data["category"] == "engineering"
    assert data["status"] == "processed"


def test_form_submission_missing_required_fields(client: TestClient) -> None:
    """Submitting form data missing required fields triggers 422."""
    resp = client.post("/documents/form", data={"category": "only-category"})
    assert resp.status_code == 422
    body = resp.json()
    assert body["error"] == "RequestValidationError"


def test_documents_protected_by_auth(basic_client: TestClient) -> None:
    """When auth is active, /documents endpoints require credentials."""
    unauthed_resp = basic_client.post(
        "/documents/upload",
        files={"file": ("test.txt", b"content", "text/plain")},
    )
    assert unauthed_resp.status_code == 401

    authed_resp = basic_client.post(
        "/documents/upload",
        files={"file": ("test.txt", b"content", "text/plain")},
        auth=("testadmin", "testpass"),
    )
    assert authed_resp.status_code == 200
