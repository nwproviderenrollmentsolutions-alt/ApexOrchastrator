"""UGC CREATOR AI: turns a strategy into a scripted, ready-to-render package.

Script generation uses Groq (free tier, see SETUP.md) when `GROQ_API_KEY` is
set, falling back to a templated script on any LLM error. Captions stay
template-based either way, so the `#ad` disclosure tag Quality Control
checks for is always present.
"""

from __future__ import annotations

import random
import sys

from .. import llm
from ..models import ContentStrategy, UGCPackage

_AVATARS = ["ai-avatar-jordan", "ai-avatar-mia", "voiceover-only-female", "voiceover-only-male"]

_SYSTEM_PROMPT = (
    "You write short, punchy UGC-style scripts for TikTok/Shorts/Reels (30-45 seconds spoken). "
    "Structure the script with these labeled beats on separate lines: [HOOK], [SETUP], [STORY], "
    "[EDITING] (camera/editing direction, not spoken), [CTA]. Keep spoken lines conversational, "
    "first-person, no hashtags. Reply with ONLY the script text, no extra commentary."
)


class UGCCreator:
    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def create(self, strategy: ContentStrategy) -> UGCPackage:
        script = self._build_script_live(strategy) if llm.is_configured() else None
        if script is None:
            script = self._build_script_mock(strategy)

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

    def _build_script_live(self, strategy: ContentStrategy) -> str | None:
        a = strategy.analysis
        user_prompt = (
            f"Framework: {strategy.framework}\n"
            f"Working title: {strategy.working_title}\n"
            f"Hook to riff on: {a.hook}\n"
            f"Story structure: {a.story_structure}\n"
            f"Product/angle to weave in: {strategy.product_angle}\n"
            f"Editing notes to include: {a.editing_notes}\n"
            f"CTA: {a.cta}"
        )
        try:
            return llm.complete(_SYSTEM_PROMPT, user_prompt)
        except llm.LLMError as exc:
            print(f"[UGCCreator] Groq script generation failed, falling back to template: {exc}", file=sys.stderr)
            return None

    def _build_script_mock(self, strategy: ContentStrategy) -> str:
        a = strategy.analysis
        return (
            f"[HOOK] {a.hook}\n"
            f"[SETUP - {strategy.framework}] {strategy.product_angle}\n"
            f"[STORY - {a.story_structure}] Walk through the pain point, "
            f"then the moment it clicked.\n"
            f"[EDITING] {a.editing_notes}\n"
            f"[CTA] {a.cta}"
        )
