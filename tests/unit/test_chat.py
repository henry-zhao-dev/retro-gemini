from contextlib import nullcontext
from datetime import datetime, timezone

import pytest

from retro_gemini import chat


def test_message_timestamp_is_utc_and_excluded_from_api_payload():
    message = chat.ChatMessage.create(chat.MessageRole.USER, "hello")

    timestamp = datetime.fromisoformat(message.timestamp)
    assert timestamp.utcoffset() == timezone.utc.utcoffset(timestamp)
    assert message.to_api_payload() == {
        "role": "user",
        "parts": [{"text": "hello"}],
    }


@pytest.mark.parametrize("command", ["exit", "QUIT"])
def test_exit_commands_end_chat_cleanly(monkeypatch, capsys, command):
    monkeypatch.setattr(chat, "prompt", lambda *args, **kwargs: command)

    chat.start_chat("gemini-pro-test")

    assert "Goodbye!" in capsys.readouterr().out


@pytest.mark.parametrize("interrupt", [EOFError(), KeyboardInterrupt()])
def test_terminal_interrupts_end_chat_cleanly(monkeypatch, capsys, interrupt):
    def interrupt_prompt(*args, **kwargs):
        raise interrupt

    monkeypatch.setattr(chat, "prompt", interrupt_prompt)

    chat.start_chat("gemini-pro-test")

    assert "Goodbye!" in capsys.readouterr().out


def test_successful_response_uses_selected_model(monkeypatch, capsys):
    prompts = iter(["hello", "quit"])
    call = {}

    def generate(payload, model):
        call["payload"] = payload
        call["model"] = model
        return "Hello from Gemini"

    monkeypatch.setattr(chat, "prompt", lambda *args, **kwargs: next(prompts))
    monkeypatch.setattr(
        chat.spinner, "loading_animation", lambda message: nullcontext()
    )
    monkeypatch.setattr(chat.gemini_client, "generate", generate)

    chat.start_chat("gemini-pro-test")

    output = capsys.readouterr().out
    assert call["model"] == "gemini-pro-test"
    assert call["payload"]["contents"][0]["parts"][0]["text"] == "hello"
    assert "Gemini:\nHello from Gemini" in output


def test_no_context_sends_only_current_prompt(monkeypatch):
    prompts = iter(["first", "second", "quit"])
    payloads = []

    def generate(payload, model):
        payloads.append(payload)
        return "Hello from Gemini"

    monkeypatch.setattr(chat, "prompt", lambda *args, **kwargs: next(prompts))
    monkeypatch.setattr(
        chat.spinner, "loading_animation", lambda message: nullcontext()
    )
    monkeypatch.setattr(chat.gemini_client, "generate", generate)

    chat.start_chat("gemini-pro-test", no_context=True)

    assert payloads == [
        {"contents": [{"role": "user", "parts": [{"text": "first"}]}]},
        {"contents": [{"role": "user", "parts": [{"text": "second"}]}]},
    ]


def test_no_context_still_records_the_conversation(monkeypatch):
    conversation = []
    monkeypatch.setattr(
        chat.spinner, "loading_animation", lambda message: nullcontext()
    )
    monkeypatch.setattr(
        chat.gemini_client,
        "generate",
        lambda payload, model: "Hello from Gemini",
    )

    chat._generate_response(
        "hello", "gemini-pro-test", conversation, no_context=True
    )

    assert [(message.role, message.content) for message in conversation] == [
        ("user", "hello"),
        ("model", "Hello from Gemini"),
    ]


@pytest.mark.parametrize(
    ("error", "expected_message"),
    [
        (
            chat.gemini_client.GeminiAPIError("HTTP 503: unavailable", status_code=503),
            "Gemini servers are currently overloaded",
        ),
        (
            chat.gemini_client.GeminiAPIError("HTTP 400: bad request"),
            "A Gemini API error occurred: HTTP 400: bad request",
        ),
        (
            chat.gemini_client.GeminiAPIError(
                "HTTP 400: value 503 is invalid", status_code=400
            ),
            "A Gemini API error occurred: HTTP 400: value 503 is invalid",
        ),
    ],
)
def test_gemini_api_errors_are_reported(monkeypatch, capsys, error, expected_message):
    monkeypatch.setattr(chat, "prompt", lambda *args, **kwargs: "hello")
    monkeypatch.setattr(
        chat.spinner, "loading_animation", lambda message: nullcontext()
    )

    def raise_api_error(payload, model):
        raise error

    monkeypatch.setattr(chat.gemini_client, "generate", raise_api_error)

    chat.start_chat("gemini-pro-test")

    assert expected_message in capsys.readouterr().out


def test_unexpected_errors_are_reported(monkeypatch, capsys):
    monkeypatch.setattr(chat, "prompt", lambda *args, **kwargs: "hello")
    monkeypatch.setattr(
        chat.spinner, "loading_animation", lambda message: nullcontext()
    )

    def raise_unexpected_error(payload, model):
        raise RuntimeError("something broke")

    monkeypatch.setattr(chat.gemini_client, "generate", raise_unexpected_error)

    chat.start_chat("gemini-pro-test")

    assert "An unexpected error occurred: something broke" in capsys.readouterr().out
