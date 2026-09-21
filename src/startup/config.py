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

import json
import os
from pathlib import Path
from typing import Any

# Base directory for resolving relative config paths
BASE_DIR = Path(__file__).resolve().parent.parent


def load_custom_config(config_path: str | Path | None = None) -> tuple[dict[str, Any], str | None]:
    """Search for, validate, and load custom configuration from config.json.

    Returns:
        tuple[dict[str, Any], str | None]: The custom configuration mapping and the resolved file path,
        or ({}, None) if no config file is found.
    """
    explicit = str(config_path).strip() if config_path else os.getenv("CONFIG_PATH", "").strip()
    if explicit:
        target = Path(explicit).expanduser()
        if not target.is_file():
            raise FileNotFoundError(f"Configuration file specified by CONFIG_PATH does not exist: '{explicit}'")
        candidates = [target]
    else:
        candidates = [
            Path("config.json"),
            BASE_DIR / "config.json",
            BASE_DIR.parent / "config.json",
        ]

    for candidate in candidates:
        if candidate.is_file():
            try:
                content = candidate.read_text(encoding="utf-8")
            except Exception as exc:
                raise ValueError(f"Could not read configuration file '{candidate}': {exc}") from exc

            try:
                parsed = json.loads(content)
            except json.JSONDecodeError as exc:
                raise ValueError(
                    f"Invalid JSON in configuration file '{candidate}' at line {exc.lineno}, "
                    f"column {exc.colno}: {exc.msg}"
                ) from exc

            if not isinstance(parsed, dict):
                raise ValueError(
                    f"Configuration file '{candidate}' must contain a JSON object, got {type(parsed).__name__}"
                )

            # If user scoped configuration under 'custom_config', extract that section
            if "custom_config" in parsed and isinstance(parsed["custom_config"], dict):
                custom_data = parsed["custom_config"]
            else:
                custom_data = parsed

            return custom_data, str(candidate.resolve())

    return {}, None
