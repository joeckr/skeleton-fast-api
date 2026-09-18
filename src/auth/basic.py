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
import binascii
import secrets

from fastapi import HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.requests import Request

from startup.env import Settings


async def authenticate(request: Request, settings: Settings) -> dict:
    auth_header = request.headers.get("Authorization")
    scheme, param = get_authorization_scheme_param(auth_header)

    if scheme.lower() != "basic" or not param:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid authentication credentials",
            headers={"WWW-Authenticate": 'Basic realm="restricted"'},
        )

    try:
        decoded = base64.b64decode(param).decode("utf-8")
        username, sep, password = decoded.partition(":")
        if not sep:
            raise ValueError("Invalid basic auth format")
    except binascii.Error, UnicodeDecodeError, ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid basic authentication credentials format",
            headers={"WWW-Authenticate": 'Basic realm="restricted"'},
        )

    is_username_valid = secrets.compare_digest(username, settings.basic_auth_username)
    is_password_valid = secrets.compare_digest(password, settings.basic_auth_password.get_secret_value())

    if not (is_username_valid and is_password_valid):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid username or password",
            headers={"WWW-Authenticate": 'Basic realm="restricted"'},
        )

    return {
        "sub": username,
        "username": username,
        "auth_mode": "basic",
    }
