import json
import sys
from contextlib import nullcontext

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


def run_cli(monkeypatch, *arguments):
    monkeypatch.setattr(sys, "argv", ["retro-gemini", *arguments])
    cli.main()


def test_settings_save_and_load_round_trip(settings_path):
    AppSettings(default_model="gemini-pro-test").save()

    assert json.loads(settings_path.read_text(encoding="utf-8")) == {
        "default_model": "gemini-pro-test"
    }
    assert AppSettings.load() == AppSettings(default_model="gemini-pro-test")


@pytest.mark.parametrize("contents", [None, "not valid json"])
def test_settings_load_uses_default_for_missing_or_corrupt_file(
    settings_path, contents
):
    if contents is not None:
        settings_path.write_text(contents, encoding="utf-8")

    assert AppSettings.load().default_model == "gemini-flash-lite-latest"


def test_cli_uses_saved_default_model(
    configured_cli, monkeypatch, capsys
):
    AppSettings(default_model="gemini-pro-test").save()
    monkeypatch.setattr(cli, "prompt", lambda *args, **kwargs: "quit")

    run_cli(monkeypatch)

    output = capsys.readouterr().out
    assert "Model: gemini-pro-test" in output


@pytest.mark.parametrize("model_flag", ["--model", "-m"])
def test_model_argument_switches_model_shown_in_app_output(
    configured_cli, monkeypatch, capsys, model_flag
):
    AppSettings(default_model="gemini-flash-lite-latest").save()
    monkeypatch.setattr(cli, "prompt", lambda *args, **kwargs: "quit")

    run_cli(monkeypatch, model_flag, "gemini-pro-test")

    output = capsys.readouterr().out
    assert "Model: gemini-pro-test" in output
    assert "Model: gemini-flash-lite-latest" not in output


def test_default_model_argument_is_saved_for_future_runs(
    configured_cli, monkeypatch, capsys
):
    monkeypatch.setattr(
        cli,
        "start_chat",
        lambda *args, **kwargs: pytest.fail("chat should not start"),
    )

    run_cli(monkeypatch, "--default-model", "gemini-pro-test")

    assert AppSettings.load().default_model == "gemini-pro-test"
    assert f"Settings saved to: {configured_cli}" in capsys.readouterr().out


def test_list_argument_prints_models_without_starting_chat(
    configured_cli, monkeypatch, capsys
):
    monkeypatch.setattr(
        cli,
        "start_chat",
        lambda *args, **kwargs: pytest.fail("chat should not start"),
    )

    run_cli(monkeypatch, "--list")

    output = capsys.readouterr().out
    assert "gemini-flash-lite-latest\ngemini-pro-test" in output


def test_model_argument_requires_a_value(settings_path, monkeypatch):
    monkeypatch.setattr(sys, "argv", ["retro-gemini", "--model"])

    with pytest.raises(SystemExit) as error:
        cli.main()

    assert error.value.code == 2


def test_cli_exits_when_api_key_is_missing(settings_path, monkeypatch, capsys):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    monkeypatch.setattr(cli, "load_dotenv", lambda: None)
    monkeypatch.setattr(
        cli.gemini_client,
        "list_model_names",
        lambda: pytest.fail("models should not be requested"),
    )

    with pytest.raises(SystemExit) as error:
        run_cli(monkeypatch)

    captured = capsys.readouterr()
    assert error.value.code == 1
    assert "GEMINI_API_KEY environment variable is not set" in captured.err


@pytest.mark.parametrize("argument", ["--model", "--default-model"])
def test_unknown_model_is_rejected_without_starting_chat(
    configured_cli, monkeypatch, capsys, argument
):
    monkeypatch.setattr(
        cli,
        "start_chat",
        lambda *args, **kwargs: pytest.fail("chat should not start"),
    )

    run_cli(monkeypatch, argument, "gemini-does-not-exist")

    output = capsys.readouterr().out
    assert "Model not found: gemini-does-not-exist." in output
    assert "retro-gemini --list" in output


@pytest.mark.parametrize("command", ["exit", "QUIT"])
def test_exit_commands_end_chat_cleanly(monkeypatch, capsys, command):
    monkeypatch.setattr(cli, "prompt", lambda *args, **kwargs: command)

    cli.start_chat("gemini-pro-test")

    assert "Goodbye!" in capsys.readouterr().out


@pytest.mark.parametrize("interrupt", [EOFError(), KeyboardInterrupt()])
def test_terminal_interrupts_end_chat_cleanly(monkeypatch, capsys, interrupt):
    def interrupt_prompt(*args, **kwargs):
        raise interrupt

    monkeypatch.setattr(cli, "prompt", interrupt_prompt)

    cli.start_chat("gemini-pro-test")

    assert "Goodbye!" in capsys.readouterr().out


def test_successful_response_uses_selected_model(monkeypatch, capsys):
    prompts = iter(["hello", "quit"])
    call = {}

    def generate(payload, model):
        call["payload"] = payload
        call["model"] = model
        return "Hello from Gemini"

    monkeypatch.setattr(cli, "prompt", lambda *args, **kwargs: next(prompts))
    monkeypatch.setattr(cli, "loading_animation", lambda message: nullcontext())
    monkeypatch.setattr(cli.gemini_client, "generate", generate)

    cli.start_chat("gemini-pro-test")

    output = capsys.readouterr().out
    assert call["model"] == "gemini-pro-test"
    assert call["payload"]["contents"][0]["parts"][0]["text"] == "hello"
    assert "Gemini:\nHello from Gemini" in output


@pytest.mark.parametrize(
    ("error", "expected_message"),
    [
        (
            cli.gemini_client.GeminiAPIError("HTTP 503: unavailable"),
            "Gemini servers are currently overloaded",
        ),
        (
            cli.gemini_client.GeminiAPIError("HTTP 400: bad request"),
            "A Gemini API error occurred: HTTP 400: bad request",
        ),
    ],
)
def test_gemini_api_errors_are_reported(
    monkeypatch, capsys, error, expected_message
):
    monkeypatch.setattr(cli, "prompt", lambda *args, **kwargs: "hello")
    monkeypatch.setattr(cli, "loading_animation", lambda message: nullcontext())

    def raise_api_error(payload, model):
        raise error

    monkeypatch.setattr(cli.gemini_client, "generate", raise_api_error)

    cli.start_chat("gemini-pro-test")

    assert expected_message in capsys.readouterr().out


def test_unexpected_errors_are_reported(monkeypatch, capsys):
    monkeypatch.setattr(cli, "prompt", lambda *args, **kwargs: "hello")
    monkeypatch.setattr(cli, "loading_animation", lambda message: nullcontext())

    def raise_unexpected_error(payload, model):
        raise RuntimeError("something broke")

    monkeypatch.setattr(cli.gemini_client, "generate", raise_unexpected_error)

    cli.start_chat("gemini-pro-test")

    assert (
        "An unexpected error occurred: something broke"
        in capsys.readouterr().out
    )
