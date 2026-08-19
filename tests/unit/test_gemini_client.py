import pytest

from retro_gemini import gemini_client


def test_client_rejects_an_explicit_blank_api_key(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "valid-environment-key")

    with pytest.raises(gemini_client.GeminiAPIError):
        gemini_client._get_api_key("   ")
