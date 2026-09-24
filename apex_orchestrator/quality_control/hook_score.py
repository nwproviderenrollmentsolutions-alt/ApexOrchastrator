"""Scores how likely a script's hook is to stop the scroll.

Uses the free-tier LLM as a judge when available; otherwise a heuristic
based on known high-retention hook patterns (question, bold claim, number,
"stop scrolling" style pattern interrupts, negative framing).
"""

from __future__ import annotations

import json
import re

from apex_orchestrator.contracts import Script
from apex_orchestrator.llm import LLMUnavailable, complete

SYSTEM_PROMPT = """You are a short-form video hook evaluator. Score the \
given hook line for scroll-stopping power on a 0.0-1.0 scale, considering: \
curiosity gap, specificity, pattern interrupt, and whether it front-loads \
value. Return strict JSON: {"score": <float 0-1>, "reasons": [<string>, ...]}."""

HOOK_PATTERNS = {
    r"^(stop|wait|don'?t)\b": "opens with a pattern-interrupt command",
    r"\?\s*$": "ends on a question, opens a curiosity gap",
    r"\b\d+\b": "uses a specific number",
    r"\b(secret|mistake|nobody|never|actually|truth)\b": "uses a curiosity/contrarian trigger word",
    r"^(how|why|what)\b": "opens with a how/why/what curiosity frame",
}


def _heuristic_score(hook: str) -> tuple[float, list[str]]:
    hook_l = hook.lower().strip()
    reasons: list[str] = []
    score = 0.15  # baseline

    for pattern, reason in HOOK_PATTERNS.items():
        if re.search(pattern, hook_l):
            score += 0.18
            reasons.append(reason)

    word_count = len(hook.split())
    if 4 <= word_count <= 14:
        score += 0.1
        reasons.append("hook length is in the tight 4-14 word sweet spot")
    elif word_count > 20:
        score -= 0.15
        reasons.append("hook is too long, likely to lose attention before the payoff")

    if not reasons:
        reasons.append("no strong retention pattern detected; consider a question, number, or bold claim")

    return max(0.0, min(1.0, score)), reasons


def score_hook(script: Script) -> tuple[float, list[str]]:
    try:
        raw = complete(SYSTEM_PROMPT, script.hook, json_mode=True, temperature=0.2)
        data = json.loads(raw)
        score = float(data["score"])
        reasons = list(data.get("reasons", []))
        return max(0.0, min(1.0, score)), reasons
    except (LLMUnavailable, KeyError, ValueError, json.JSONDecodeError, Exception):
        return _heuristic_score(script.hook)
