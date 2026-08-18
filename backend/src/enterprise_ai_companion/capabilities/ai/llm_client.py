"""Thin async wrapper around the Volvo GenAI Hub (OpenAI-compatible) API.

Credentials come exclusively from environment variables:
    EAC_APIM_ENDPOINT        Base URL, e.g. https://api.volvogenaihubqa.volvogroup.net
    EAC_APIM_SUBSCRIPTION_KEY  Used as the ``api-key`` header value

The model deployment ID is also configurable:
    EAC_LLM_MODEL_ID         Default: gpt-5.4-mini_gb_2026-03-17
"""

from __future__ import annotations

import asyncio
import logging

import httpx

from enterprise_ai_companion.infrastructure.config import get_config

logger = logging.getLogger(__name__)

_MAX_RETRIES = 3
_RETRY_BACKOFF = [1.0, 2.0, 4.0]  # seconds between attempts

_API_VERSION = "preview"


def _base_url() -> str:
    endpoint = get_config().apim_endpoint
    return f"{endpoint.rstrip('/')}/azure-openai/v1"


def _api_key() -> str:
    return get_config().apim_subscription_key.get_secret_value()


def _model_id() -> str:
    return get_config().llm_model_id


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
        "max_completion_tokens": max_tokens,
        "temperature": temperature,
    }

    async with httpx.AsyncClient(timeout=30.0) as client:
        last_exc: httpx.HTTPStatusError | None = None
        for attempt in range(_MAX_RETRIES):
            response = await client.post(url, headers=headers, json=payload)
            if response.status_code < 500:
                response.raise_for_status()
                break
            last_exc = httpx.HTTPStatusError(
                message=f"Server error '{response.status_code}' for url '{url}'",
                request=response.request,
                response=response,
            )
            if attempt < _MAX_RETRIES - 1:
                delay = _RETRY_BACKOFF[attempt]
                logger.warning(
                    "LLM API returned %s — retrying in %.0fs (attempt %d/%d)",
                    response.status_code, delay, attempt + 1, _MAX_RETRIES,
                )
                await asyncio.sleep(delay)
        else:
            raise last_exc  # type: ignore[misc]

    data = response.json()
    return str(data["choices"][0]["message"]["content"])
