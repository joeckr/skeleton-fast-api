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

from typing import Any

from fastapi import APIRouter, File, Form, UploadFile

from controllers.document import (  # pyrefly: ignore [missing-import]
    process_document_upload,
    process_form_data,
)

router = APIRouter(prefix="/documents", tags=["Documents"])


@router.post("/upload")
async def upload_document(
    file: UploadFile = File(..., description="Document or media file to upload"),
    description: str | None = Form(None, description="Optional document description"),
) -> dict[str, Any]:
    """Ingest documents and file attachments via multipart/form-data."""
    result = await process_document_upload(file=file, description=description)
    return {
        "status": "ok",
        "document": result,
    }


@router.post("/form")
def submit_form(
    title: str = Form(..., description="Form entry title"),
    content: str = Form(..., description="Form body content"),
    category: str | None = Form(None, description="Optional classification category"),
) -> dict[str, Any]:
    """Ingest structured form data via application/x-www-form-urlencoded or multipart/form-data."""
    result = process_form_data(title=title, content=content, category=category)
    return {
        "status": "ok",
        "data": result,
    }
