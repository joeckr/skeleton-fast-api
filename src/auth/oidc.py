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

import jwt
from fastapi import HTTPException, status
from fastapi.security.utils import get_authorization_scheme_param
from starlette.requests import Request

from api.oidc import get_jwks_client
from startup.env import Settings


async def authenticate(request: Request, settings: Settings) -> dict[str, Any]:
    if not settings.oidc_issuer_url:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="OIDC issuer URL is not configured in settings",
        )

    auth_header = request.headers.get("Authorization")
    scheme, token = get_authorization_scheme_param(auth_header)

    if scheme.lower() != "bearer" or not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing or invalid Bearer authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        jwks_client = get_jwks_client(
            settings.oidc_issuer_url,
            ssl_verify=settings.oidc_ssl,
        )
        signing_key = jwks_client.get_signing_key_from_jwt(token)

        decode_kwargs: dict[str, Any] = {
            "algorithms": settings.oidc_algorithms,
            "issuer": settings.oidc_issuer_url.rstrip("/"),
            "options": {"verify_exp": True},
        }

        if settings.oidc_client_id:
            decode_kwargs["audience"] = settings.oidc_client_id
        else:
            decode_kwargs["options"]["verify_aud"] = False

        payload = jwt.decode(token, signing_key.key, **decode_kwargs)
        payload["auth_mode"] = "oidc"
        return payload

    except jwt.ExpiredSignatureError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token has expired",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )
    except jwt.PyJWTError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=f"Token validation failed: {str(exc)}",
            headers={"WWW-Authenticate": 'Bearer error="invalid_token"'},
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Unable to verify token with identity provider: {str(exc)}",
        )
