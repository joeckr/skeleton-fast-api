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
from collections.abc import Generator
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from main import create_app
from startup.env import Settings


@pytest.fixture
def temp_custom_config(tmp_path: Path) -> Generator[Path]:
    """Provide a temporary config.json containing custom_config as well as ignored env-like keys."""
    config_file = tmp_path / "config.json"
    data = {
        # These keys should be ignored and NOT override BaseSettings / env vars
        "app_name": "should-not-override-env-app",
        "port": 9999,
        "max_json_size": 12345,
        # Only this should apply
        "custom_config": {
            "feature_flags": {
                "enable_new_dashboard": True,
            },
            "rate_limits": {
                "burst": 100,
                "rate_per_second": 10,
            },
        },
    }
    config_file.write_text(json.dumps(data), encoding="utf-8")
    yield config_file


def test_config_json_only_applies_to_custom_config(temp_custom_config: Path) -> None:
    """config.json must ONLY populate custom_config and NOT serve as source of truth for env vars."""
    settings = Settings(config_path=str(temp_custom_config))

    # Environment settings must retain their env/.env/default values, NOT values from config.json
    assert settings.app_name != "should-not-override-env-app"
    assert settings.port != 9999
    assert settings.max_json_size != 12345

    # custom_config must be populated from config.json
    assert settings.custom_config["feature_flags"]["enable_new_dashboard"] is True
    assert settings.custom_config["rate_limits"]["burst"] == 100
    assert settings.config_file_loaded == str(temp_custom_config.resolve())


def test_no_config_json_works_and_custom_config_is_empty(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    """When no config.json exists, the app must work normally and custom_config must be empty."""
    # Ensure no CONFIG_PATH env var is set
    monkeypatch.delenv("CONFIG_PATH", raising=False)

    # Point search away from any repo config.json files by using empty tmp_path
    monkeypatch.chdir(tmp_path)

    settings = Settings(config_path=None)
    assert settings.custom_config == {}
    assert settings.config_file_loaded is None

    # App boots cleanly and endpoints work
    app = create_app(settings)
    with TestClient(app) as client:
        resp = client.get("/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "app_name" in data
        assert "custom_config" not in data
        assert "config_file_loaded" not in data


def test_invalid_json_syntax_raises_descriptive_value_error(tmp_path: Path) -> None:
    """Malformed JSON syntax must raise a descriptive ValueError with line and column info."""
    corrupt_file = tmp_path / "corrupt.json"
    corrupt_file.write_text("{ unquoted_key: 123 ", encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        Settings(config_path=str(corrupt_file))

    assert "Invalid JSON in configuration file" in str(exc_info.value)
    assert "line 1" in str(exc_info.value)


def test_non_dict_json_raises_value_error(tmp_path: Path) -> None:
    """A JSON file whose root is not an object (e.g. an array) must raise a ValueError."""
    array_file = tmp_path / "array.json"
    array_file.write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(ValueError) as exc_info:
        Settings(config_path=str(array_file))

    assert "must contain a JSON object" in str(exc_info.value)


def test_missing_explicit_config_path_raises_file_not_found() -> None:
    """Specifying an explicit config_path that does not exist must raise FileNotFoundError."""
    with pytest.raises(FileNotFoundError) as exc_info:
        Settings(config_path="/non/existent/path/to/config.json")

    assert "does not exist" in str(exc_info.value)


def test_app_retains_custom_config_without_exposing_in_endpoint(temp_custom_config: Path) -> None:
    """Custom config should be loaded into app settings while /config remains sanitized."""
    settings = Settings(config_path=str(temp_custom_config), auth_mode="none", cron_enabled=False)
    app = create_app(settings)

    assert app.state.settings.config_file_loaded == str(temp_custom_config.resolve())
    assert app.state.settings.custom_config["feature_flags"]["enable_new_dashboard"] is True
    assert app.state.settings.custom_config["rate_limits"]["burst"] == 100

    with TestClient(app) as client:
        resp = client.get("/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "config_file_loaded" not in data
        assert "custom_config" not in data
