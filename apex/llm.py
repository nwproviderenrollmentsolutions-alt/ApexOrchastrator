"""Thin client for Groq's free-tier, OpenAI-compatible chat completions API.

Get a free key (no credit card required) at https://console.groq.com/keys
and put it in `.env` as `GROQ_API_KEY=...`. See SETUP.md for the full steps.

Every stage that calls `complete()` is expected to catch `LLMError` and fall
back to its mocked behavior, so the pipeline still runs with no key set.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from .config import settings

GROQ_CHAT_URL = "https://api.groq.com/openai/v1/chat/completions"


class LLMError(RuntimeError):
    pass


def is_configured() -> bool:
    return bool(settings.groq_api_key)


def complete(system_prompt: str, user_prompt: str, *, temperature: float = 0.8, max_tokens: int = 600) -> str:
    """Call Groq chat completions and return the assistant's text reply."""
    if not settings.groq_api_key:
        raise LLMError("GROQ_API_KEY is not set")

    body = json.dumps(
        {
            "model": settings.groq_model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
        }
    ).encode()

    request = urllib.request.Request(
        GROQ_CHAT_URL,
        data=body,
        headers={
            "Authorization": f"Bearer {settings.groq_api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            payload = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:300]
        raise LLMError(f"Groq API returned {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise LLMError(f"Groq API unreachable: {exc.reason}") from exc

    try:
        return payload["choices"][0]["message"]["content"]
    except (KeyError, IndexError) as exc:
        raise LLMError(f"Unexpected Groq API response shape: {payload}") from exc


def complete_json(system_prompt: str, user_prompt: str, **kwargs) -> dict:
    """Call `complete()` and parse the reply as JSON, stripping any markdown fencing."""
    text = complete(system_prompt, user_prompt, **kwargs).strip()
    if text.startswith("```"):
        text = text.strip("`")
        if text.lower().startswith("json"):
            text = text[4:]
    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise LLMError(f"Groq reply was not valid JSON: {text[:300]}") from exc
