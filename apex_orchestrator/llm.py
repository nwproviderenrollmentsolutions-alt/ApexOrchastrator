"""Thin wrapper around Groq's free-tier chat completions API.

Groq's OpenAI-compatible REST API needs no SDK -- a single `requests.post`
call is enough. If no GROQ_API_KEY is configured, `complete()` raises
LLMUnavailable and callers fall back to their own offline heuristics.
"""

from __future__ import annotations

import json

import requests

from apex_orchestrator.config import CONFIG

GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


class LLMUnavailable(RuntimeError):
    pass


def complete(system: str, user: str, *, json_mode: bool = False, temperature: float = 0.7) -> str:
    if not CONFIG.has_llm:
        raise LLMUnavailable("GROQ_API_KEY not configured")

    payload = {
        "model": CONFIG.groq_model,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": temperature,
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    resp = requests.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {CONFIG.groq_api_key}",
            "Content-Type": "application/json",
        },
        data=json.dumps(payload),
        timeout=30,
    )
    resp.raise_for_status()
    return resp.json()["choices"][0]["message"]["content"]
