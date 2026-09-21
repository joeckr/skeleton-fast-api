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

from fastapi import UploadFile


async def process_document_upload(file: UploadFile, description: str | None = None) -> dict[str, Any]:
    """Process an uploaded document or file, capturing metadata and validating intake."""
    contents = await file.read()
    size_bytes = len(contents)
    await file.seek(0)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size_bytes": size_bytes,
        "description": description,
        "status": "received",
    }


def process_form_data(title: str, content: str, category: str | None = None) -> dict[str, Any]:
    """Process standard form submissions."""
    return {
        "title": title,
        "content": content,
        "category": category or "general",
        "status": "processed",
    }
