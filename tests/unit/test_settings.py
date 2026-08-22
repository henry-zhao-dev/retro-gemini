import json

import pytest

from retro_gemini.settings import AppSettings


def test_settings_save_and_load_round_trip(settings_path):
    AppSettings(default_model="gemini-pro-test").save()

    assert json.loads(settings_path.read_text(encoding="utf-8")) == {
        "default_model": "gemini-pro-test"
    }
    assert AppSettings.load() == AppSettings(default_model="gemini-pro-test")


@pytest.mark.parametrize("contents", [None, "not valid json", "[]", "null"])
def test_settings_load_uses_default_for_missing_or_corrupt_file(
    settings_path, contents
):
    if contents is not None:
        settings_path.write_text(contents, encoding="utf-8")

    assert AppSettings.load().default_model == "gemini-flash-lite-latest"


def test_settings_load_does_not_hide_unexpected_errors(settings_path, monkeypatch):
    settings_path.write_text("{}", encoding="utf-8")

    def raise_unexpected_error(file):
        raise RuntimeError("unexpected failure")

    monkeypatch.setattr(json, "load", raise_unexpected_error)

    with pytest.raises(RuntimeError, match="unexpected failure"):
        AppSettings.load()
