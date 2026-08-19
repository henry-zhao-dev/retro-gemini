import pytest

from retro_gemini import chat, cli
from retro_gemini.settings import AppSettings


def test_cli_uses_saved_default_model(configured_cli, run_cli, monkeypatch, capsys):
    AppSettings(default_model="gemini-pro-test").save()
    monkeypatch.setattr(chat, "prompt", lambda *args, **kwargs: "quit")

    run_cli()

    assert "Model: gemini-pro-test" in capsys.readouterr().out


@pytest.mark.parametrize("model_flag", ["--model", "-m"])
def test_model_argument_switches_model_shown_in_app_output(
    configured_cli, run_cli, monkeypatch, capsys, model_flag
):
    AppSettings(default_model="gemini-flash-lite-latest").save()
    monkeypatch.setattr(chat, "prompt", lambda *args, **kwargs: "quit")

    run_cli(model_flag, "gemini-pro-test")

    output = capsys.readouterr().out
    assert "Model: gemini-pro-test" in output
    assert "Model: gemini-flash-lite-latest" not in output


def test_default_model_argument_is_saved_for_future_runs(
    configured_cli, run_cli, monkeypatch, capsys
):
    monkeypatch.setattr(
        cli.chat,
        "start_chat",
        lambda *args, **kwargs: pytest.fail("chat should not start"),
    )

    run_cli("--default-model", "gemini-pro-test")

    assert AppSettings.load().default_model == "gemini-pro-test"
    assert f"Settings saved to: {configured_cli}" in capsys.readouterr().out


def test_list_argument_prints_models_without_starting_chat(
    configured_cli, run_cli, monkeypatch, capsys
):
    monkeypatch.setattr(
        cli.chat,
        "start_chat",
        lambda *args, **kwargs: pytest.fail("chat should not start"),
    )

    run_cli("--list")

    output = capsys.readouterr().out
    assert "gemini-flash-lite-latest\ngemini-pro-test" in output


@pytest.mark.parametrize("api_key", [None, "", " \t "])
def test_cli_exits_when_api_key_is_missing_or_blank(
    settings_path, run_cli, monkeypatch, capsys, api_key
):
    if api_key is None:
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    else:
        monkeypatch.setenv("GEMINI_API_KEY", api_key)
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    monkeypatch.setattr(
        cli.gemini_client,
        "list_model_names",
        lambda: pytest.fail("models should not be requested"),
    )

    with pytest.raises(SystemExit) as error:
        run_cli()

    captured = capsys.readouterr()
    assert error.value.code == 1
    assert "GEMINI_API_KEY environment variable is not set" in captured.err


def test_cli_exits_cleanly_when_model_request_fails(
    settings_path, run_cli, monkeypatch, capsys
):
    monkeypatch.setenv("GEMINI_API_KEY", "test-api-key")
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)

    def fail_to_list_models():
        raise cli.gemini_client.GeminiAPIError("HTTP 503: unavailable")

    monkeypatch.setattr(cli.gemini_client, "list_model_names", fail_to_list_models)

    with pytest.raises(SystemExit) as error:
        run_cli()

    captured = capsys.readouterr()
    assert error.value.code == 1
    assert "Failed to retrieve Gemini models: HTTP 503: unavailable" in captured.err
    assert "Settings saved" not in captured.out
    assert not settings_path.exists()


@pytest.mark.parametrize("argument", ["--model", "--default-model"])
def test_unknown_model_is_rejected_without_starting_chat(
    configured_cli, run_cli, monkeypatch, capsys, argument
):
    monkeypatch.setattr(
        cli.chat,
        "start_chat",
        lambda *args, **kwargs: pytest.fail("chat should not start"),
    )

    with pytest.raises(SystemExit) as error:
        run_cli(argument, "gemini-does-not-exist")

    output = capsys.readouterr().out
    assert error.value.code == 1
    assert "Model not found: gemini-does-not-exist." in output
    assert "retro-gemini --list" in output
    assert "Settings saved" not in output
