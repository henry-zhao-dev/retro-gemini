import sys

import pytest

from retro_gemini import cli
from retro_gemini.settings import AppSettings


@pytest.fixture
def settings_path(tmp_path, monkeypatch):
    path = tmp_path / "settings.json"
    monkeypatch.setattr(AppSettings, "get_path", staticmethod(lambda: path))
    return path


@pytest.fixture
def configured_cli(monkeypatch, settings_path):
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    monkeypatch.setattr(
        cli.gemini_client,
        "list_model_names",
        lambda: ["gemini-flash-lite-latest", "gemini-pro-test"],
    )
    return settings_path


@pytest.fixture
def run_cli(monkeypatch):
    def run(*arguments):
        monkeypatch.setattr(sys, "argv", ["retro-gemini", *arguments])
        cli.main()

    return run
