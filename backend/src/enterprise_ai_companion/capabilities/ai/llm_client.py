"""Thin async wrapper around the Volvo GenAI Hub (OpenAI-compatible) API.

Credentials come exclusively from environment variables:
    EAC_APIM_ENDPOINT        Base URL, e.g. https://api.volvogenaihubqa.volvogroup.net
    EAC_APIM_SUBSCRIPTION_KEY  Used as the ``api-key`` header value

The model deployment ID is also configurable:
    EAC_LLM_MODEL_ID         Default: gpt-5.4-mini_gb_2026-03-17
"""

from __future__ import annotations

import os

import httpx

_DEFAULT_MODEL = "gpt-5.4-mini_gb_2026-03-17"
_API_VERSION = "preview"


def _base_url() -> str:
    endpoint = os.environ.get("EAC_APIM_ENDPOINT", "")
    if not endpoint:
        raise EnvironmentError("EAC_APIM_ENDPOINT environment variable is not set.")
    return f"{endpoint.rstrip('/')}/azure-openai/v1"


def _api_key() -> str:
    key = os.environ.get("EAC_APIM_SUBSCRIPTION_KEY", "")
    if not key:
        raise EnvironmentError("EAC_APIM_SUBSCRIPTION_KEY environment variable is not set.")
    return key


def _model_id() -> str:
    return os.environ.get("EAC_LLM_MODEL_ID", _DEFAULT_MODEL)


async def chat_complete(
    messages: list[dict[str, str]],
    max_tokens: int = 1024,
    temperature: float = 0.0,
) -> str:
    """Send a chat completion request and return the assistant message content.

    Raises:
        EnvironmentError: If required environment variables are not set.
        httpx.HTTPStatusError: If the API returns a non-2xx status.
    """
    url = f"{_base_url()}/chat/completions?api-version={_API_VERSION}"
    headers = {
        "api-key": _api_key(),
        "Content-Type": "application/json",
    }
    payload = {
        "model": _model_id(),
        "messages": messages,
        "max_tokens": max_tokens,
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        response = await client.post(url, headers=headers, json=payload)
        response.raise_for_status()

    data = response.json()
    return str(data["choices"][0]["message"]["content"])
