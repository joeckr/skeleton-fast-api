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


from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from controllers.config import get_public_config  # pyrefly: ignore [missing-import]
from startup.env import Settings, get_settings

router = APIRouter(tags=["Configuration"])


class FrontendConfigResponse(BaseModel):
    app_name: str = Field(description="Name of the application")
    app_env: str = Field(description="Current deployment environment (dev, staging, prod, test)")
    auth_mode: str = Field(description="Active authentication mode (none, basic, oidc)")


@router.get(
    "/config",
    response_model=FrontendConfigResponse,
    summary="Get public application configuration for frontend bootstrapping",
)
def get_frontend_config(settings: Settings = Depends(get_settings)) -> FrontendConfigResponse:
    config_data = get_public_config(settings)
    return FrontendConfigResponse(**config_data)
