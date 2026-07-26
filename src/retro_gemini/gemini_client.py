"""Minimal Gemini REST API client.

Requires:
    export GEMINI_API_KEY="your-api-key"

No third-party Python packages are needed.
"""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta"


class GeminiAPIError(RuntimeError):
    """Raised when the Gemini API returns an error."""


def _get_api_key(api_key: str | None = None) -> str:
    """Return an explicitly supplied key or GEMINI_API_KEY."""

    key = api_key or os.environ.get("GEMINI_API_KEY")

    if not key:
        raise GeminiAPIError("Gemini API key not found. Set GEMINI_API_KEY first.")

    return key.strip()


def _request_json(
    url: str,
    *,
    api_key: str | None = None,
    payload: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Send a Gemini API request and return decoded JSON."""

    headers = {
        "Accept": "application/json",
        "x-goog-api-key": _get_api_key(api_key),
    }

    data = None
    method = "GET"

    if payload is not None:
        data = json.dumps(payload).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"

    request = urllib.request.Request(
        url,
        data=data,
        headers=headers,
        method=method,
    )

    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return json.load(response)

    except urllib.error.HTTPError as error:
        body = error.read().decode("utf-8", errors="replace")

        try:
            error_data = json.loads(body)
            message = error_data.get("error", {}).get("message", body)
        except json.JSONDecodeError:
            message = body

        raise GeminiAPIError(
            f"Gemini API returned HTTP {error.code}: {message}"
        ) from error

    except urllib.error.URLError as error:
        raise GeminiAPIError(
            f"Could not connect to Gemini API: {error.reason}"
        ) from error


def list_models(
    *,
    api_key: str | None = None,
    generation_only: bool = False,
) -> list[dict[str, Any]]:
    """Return all models available to this API key.

    Args:
        api_key:
            Optional API key. Otherwise GEMINI_API_KEY is used.
        generation_only:
            When True, only return models supporting generateContent.
    """

    models: list[dict[str, Any]] = []
    page_token: str | None = None

    while True:
        query = {"pageSize": 1000}

        if page_token:
            query["pageToken"] = page_token

        url = f"{API_BASE_URL}/models?{urllib.parse.urlencode(query)}"
        result = _request_json(url, api_key=api_key)

        for model in result.get("models", []):
            supported = model.get("supportedGenerationMethods", [])

            if not generation_only or "generateContent" in supported:
                models.append(model)

        page_token = result.get("nextPageToken")

        if not page_token:
            break

    return models


def list_model_names(
    *,
    api_key: str | None = None,
    generation_only: bool = True,
) -> list[str]:
    """Return model names such as 'gemini-2.5-flash'."""

    names = []

    for model in list_models(
        api_key=api_key,
        generation_only=generation_only,
    ):
        name = model.get("name", "")

        if name.startswith("models/"):
            name = name.removeprefix("models/")

        if name:
            names.append(name)

    return names


def generate(
    prompt: str,
    model: str,
    *,
    api_key: str | None = None,
) -> str:
    """Send a text prompt to a model and return its text response."""

    if not prompt.strip():
        raise ValueError("Prompt cannot be empty.")

    if model.startswith("models/"):
        model = model.removeprefix("models/")

    encoded_model = urllib.parse.quote(model, safe="-._")
    url = f"{API_BASE_URL}/models/{encoded_model}:generateContent"

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [
                    {"text": prompt},
                ],
            }
        ]
    }

    result = _request_json(
        url,
        api_key=api_key,
        payload=payload,
    )

    candidates = result.get("candidates", [])

    if not candidates:
        prompt_feedback = result.get("promptFeedback")
        raise GeminiAPIError(
            f"Gemini returned no candidates. Feedback: {prompt_feedback}"
        )

    parts = candidates[0].get("content", {}).get("parts", [])
    text_parts = [part["text"] for part in parts if isinstance(part.get("text"), str)]

    if not text_parts:
        raise GeminiAPIError(f"Gemini returned no text content: {result}")

    return "".join(text_parts)
