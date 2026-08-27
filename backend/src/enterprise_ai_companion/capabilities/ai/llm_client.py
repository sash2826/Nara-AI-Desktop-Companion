"""Thin async wrapper around the Volvo GenAI Hub (OpenAI-compatible) API.

Auth: APIM subscription key via EAC_APIM_SUBSCRIPTION_KEY env var.
The model deployment ID is configurable via EAC_LLM_MODEL_ID.
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


def _auth_headers() -> dict[str, str]:
    """Return the APIM subscription key header."""
    cfg = get_config()
    if cfg.apim_subscription_key:
        return {"api-key": cfg.apim_subscription_key.get_secret_value()}

    logger.warning(
        "No APIM subscription key configured — APIM calls will likely fail with 401."
    )
    return {}


def _model_id() -> str:
    return get_config().llm_model_id


async def chat_complete(
    messages: list[dict[str, str]],
    max_tokens: int = 1024,
    temperature: float = 0.0,
) -> str:
    """Send a chat completion request and return the assistant message content.

    Raises:
        httpx.HTTPStatusError: If the API returns a non-2xx status.
    """
    url = f"{_base_url()}/chat/completions?api-version={_API_VERSION}"
    headers = {
        "Content-Type": "application/json",
        **_auth_headers(),
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
                    response.status_code,
                    delay,
                    attempt + 1,
                    _MAX_RETRIES,
                )
                await asyncio.sleep(delay)
        else:
            raise last_exc  # type: ignore[misc]

    data = response.json()
    return str(data["choices"][0]["message"]["content"])
