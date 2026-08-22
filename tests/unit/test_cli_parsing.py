import sys

import pytest

from retro_gemini import cli

DEFAULT_MODEL = "gemini-flash-lite-latest"


def test_model_argument_requires_a_value(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["retro-gemini", "--model"])

    with pytest.raises(SystemExit) as error:
        cli.parse_args(DEFAULT_MODEL)

    assert error.value.code == 2


@pytest.mark.parametrize("argument", ["-n", "--no-context"])
def test_no_context_argument(monkeypatch, argument):
    monkeypatch.setattr(sys, "argv", ["retro-gemini", argument])

    args = cli.parse_args(DEFAULT_MODEL)

    assert args.no_context is True


def test_default_arguments(monkeypatch):
    monkeypatch.setattr(sys, "argv", ["retro-gemini"])

    args = cli.parse_args(DEFAULT_MODEL)

    assert args.model == DEFAULT_MODEL
    assert args.default_model is None
    assert args.list is False
    assert args.no_context is False
