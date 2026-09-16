"""VIRAL ANALYST AI: breaks a trending post into hook / pattern / story / editing / CTA / comments.

Uses Groq (free tier, see SETUP.md) to actually reason about the trend when
`GROQ_API_KEY` is set; falls back to deterministic mock heuristics on any
LLM error or when no key is configured, so the pipeline never breaks.
"""

from __future__ import annotations

import random
import sys

from .. import llm
from ..models import AnalysisReport, TrendSignal

_HOOKS = [
    "POV: you just found out...",
    "Nobody is talking about this, but...",
    "I tried this for 30 days and...",
    "Stop doing X, do this instead",
]
_PATTERNS = ["3-act reveal", "listicle countdown", "problem-agitate-solve", "before/after"]
_STORY_STRUCTURES = ["cold open + payoff", "relatable setup + twist", "tutorial + result"]
_EDITING_NOTES = [
    "fast cuts every 1-2s, captions burned in, jump cuts on filler words",
    "single continuous take, subtle zoom for emphasis",
    "text overlays synced to voiceover beats",
]
_CTAS = ["follow for part 2", "comment your result", "link in bio", "save this for later"]
_COMMENT_THEMES = [
    ["asking for source", "tagging friends", "disagreement in replies"],
    ["asking for a tutorial", "sharing their own results", "requesting a discount code"],
    ["relating personal story", "asking follow-up questions"],
]

_SYSTEM_PROMPT = (
    "You are a short-form video virality analyst. Given a trending post's metadata, "
    "break down why it works. Reply with ONLY a JSON object with keys: "
    "hook (string), pattern (string, e.g. '3-act reveal'), story_structure (string), "
    "editing_notes (string), cta (string), top_comments_themes (array of 2-4 short strings), "
    "virality_score (number 0-100). No prose, no markdown fencing."
)


class ViralAnalyst:
    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def analyze(self, signal: TrendSignal) -> AnalysisReport:
        if llm.is_configured():
            try:
                return self._analyze_live(signal)
            except llm.LLMError as exc:
                print(f"[ViralAnalyst] Groq analysis failed, falling back to mock: {exc}", file=sys.stderr)
        return self._analyze_mock(signal)

    def _analyze_live(self, signal: TrendSignal) -> AnalysisReport:
        user_prompt = (
            f"Platform: {signal.platform.value}\n"
            f"Topic: {signal.topic}\n"
            f"Views: {signal.view_count}\n"
            f"Velocity (views/hour): {signal.velocity:.0f}\n"
            f"Audio/sound: {signal.audio_or_sound}"
        )
        data = llm.complete_json(_SYSTEM_PROMPT, user_prompt)
        return AnalysisReport(
            signal=signal,
            hook=str(data["hook"]),
            pattern=str(data["pattern"]),
            story_structure=str(data["story_structure"]),
            editing_notes=str(data["editing_notes"]),
            cta=str(data["cta"]),
            top_comments_themes=[str(t) for t in data.get("top_comments_themes", [])],
            virality_score=float(data.get("virality_score", 50.0)),
        )

    def _analyze_mock(self, signal: TrendSignal) -> AnalysisReport:
        # Velocity is the strongest proxy we have for "this is actually working"
        # without a live analysis pass.
        virality_score = min(100.0, (signal.velocity / 50_000) * 100)
        return AnalysisReport(
            signal=signal,
            hook=self._rng.choice(_HOOKS),
            pattern=self._rng.choice(_PATTERNS),
            story_structure=self._rng.choice(_STORY_STRUCTURES),
            editing_notes=self._rng.choice(_EDITING_NOTES),
            cta=self._rng.choice(_CTAS),
            top_comments_themes=self._rng.choice(_COMMENT_THEMES),
            virality_score=round(virality_score, 1),
        )
