"""VIRAL ANALYST AI: breaks a trending post into hook / pattern / story / editing / CTA / comments.

Mocked heuristics stand in for an actual LLM-vision/transcript analysis pass.
"""

from __future__ import annotations

import random

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


class ViralAnalyst:
    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def analyze(self, signal: TrendSignal) -> AnalysisReport:
        # Velocity is the strongest proxy we have for "this is actually working"
        # until we plug in real engagement-rate / retention-curve data.
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
