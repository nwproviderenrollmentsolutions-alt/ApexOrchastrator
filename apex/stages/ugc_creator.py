"""UGC CREATOR AI: turns a strategy into a scripted, ready-to-render package.

Mocked script/avatar/b-roll/caption generation. In production this is where
an LLM script-writer plus an avatar/voice renderer (e.g. an MCP video tool)
would plug in.
"""

from __future__ import annotations

import random

from ..models import ContentStrategy, UGCPackage

_AVATARS = ["ai-avatar-jordan", "ai-avatar-mia", "voiceover-only-female", "voiceover-only-male"]


class UGCCreator:
    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def create(self, strategy: ContentStrategy) -> UGCPackage:
        script = self._build_script(strategy)
        b_roll = [
            "screen recording of product in use",
            "close-up reaction shot",
            "text-on-screen stat callout",
        ]
        captions = f"{strategy.working_title}\n\n{strategy.analysis.cta} 👇\n\n#ad"
        return UGCPackage(
            strategy=strategy,
            script=script,
            avatar_or_voice=self._rng.choice(_AVATARS),
            b_roll_plan=b_roll,
            captions=captions,
        )

    def _build_script(self, strategy: ContentStrategy) -> str:
        a = strategy.analysis
        return (
            f"[HOOK] {a.hook}\n"
            f"[SETUP - {strategy.framework}] {strategy.product_angle}\n"
            f"[STORY - {a.story_structure}] Walk through the pain point, "
            f"then the moment it clicked.\n"
            f"[EDITING] {a.editing_notes}\n"
            f"[CTA] {a.cta}"
        )
