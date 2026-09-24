"""Turns a ContentBrief into a short-form Script.

Uses Groq (free tier) when configured; otherwise falls back to a
template-based writer so the pipeline still produces something testable
offline. Faceless-friendly: no avatar/on-camera direction, matches the
README ("YouTube faceless") -- voiceover + B-roll + captions instead.
"""

from __future__ import annotations

import json
import re

from apex_orchestrator.contracts import ContentBrief, Script
from apex_orchestrator.llm import LLMUnavailable, complete

SYSTEM_PROMPT = """You are a short-form video scriptwriter for faceless \
TikTok/Reels/YouTube Shorts content. Write tight, high-retention scripts: \
a scroll-stopping hook in the first line, 3-5 punchy body beats, and a \
clear call to action. No stage directions, no emojis, no camera talk -- \
this is narration over B-roll footage. Return strict JSON with keys: \
hook (string), beats (array of strings), cta (string), keywords (array of \
3-6 short search terms for stock B-roll footage that matches the script)."""


def _build_user_prompt(brief: ContentBrief) -> str:
    claims = "; ".join(brief.key_claims) if brief.key_claims else "none given"
    return (
        f"Topic: {brief.topic}\n"
        f"Angle: {brief.angle}\n"
        f"Tone: {brief.tone}\n"
        f"Product/subject: {brief.product_name or 'n/a'}\n"
        f"Key claims to include: {claims}\n"
        f"Call to action goal: {brief.cta}\n"
        f"Max duration: {brief.max_duration_sec} seconds\n"
    )


def _fallback_script(brief: ContentBrief) -> Script:
    """Offline template writer used when no LLM key is configured."""
    hook = f"Stop scrolling if you care about {brief.topic}."
    beats = [
        f"Here's the angle nobody's talking about: {brief.angle}.",
    ]
    for claim in brief.key_claims[:3]:
        beats.append(claim)
    if not brief.key_claims:
        beats.append(f"{brief.product_name or brief.topic} changes how you think about this.")
    cta = brief.cta
    keywords = re.findall(r"[a-zA-Z]{4,}", f"{brief.topic} {brief.angle}")[:5] or ["technology"]
    return Script(brief_id=brief.brief_id, hook=hook, beats=beats, cta=cta, keywords=keywords)


def write_script(brief: ContentBrief) -> tuple[Script, bool]:
    """Returns (script, used_llm)."""
    try:
        raw = complete(SYSTEM_PROMPT, _build_user_prompt(brief), json_mode=True, temperature=0.8)
        data = json.loads(raw)
        script = Script(
            brief_id=brief.brief_id,
            hook=data["hook"],
            beats=list(data.get("beats", [])),
            cta=data.get("cta") or brief.cta,
            keywords=list(data.get("keywords", [])) or [brief.topic],
            disclosure_tag="#ad" if brief.disclosure_required else None,
        )
        return script, True
    except (LLMUnavailable, KeyError, json.JSONDecodeError, Exception):
        script = _fallback_script(brief)
        if brief.disclosure_required:
            script.disclosure_tag = "#ad"
        return script, False
