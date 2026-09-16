"""CONTENT STRATEGIST: picks a content framework and a brand/product angle.

`product_context` lets you tell it what you're actually promoting; it's used
to pick a believable "Replit angle" (or whatever product this pipeline is
selling) rather than just aping the trend verbatim.
"""

from __future__ import annotations

import random

from ..models import AnalysisReport, ContentStrategy

_FRAMEWORKS = [
    "problem-agitate-solve",
    "listicle",
    "before/after case study",
    "myth vs reality",
    "day-in-the-life demo",
]


class ContentStrategist:
    def __init__(self, product_context: str = "our product", seed: int | None = None) -> None:
        self.product_context = product_context
        self._rng = random.Random(seed)

    def strategize(self, analysis: AnalysisReport) -> ContentStrategy:
        framework = self._rng.choice(_FRAMEWORKS)
        angle = f"{self.product_context} solves the pain point behind '{analysis.signal.topic}'"
        title = f"{analysis.hook} ({analysis.signal.topic})"
        return ContentStrategy(
            analysis=analysis,
            framework=framework,
            product_angle=angle,
            target_platform=analysis.signal.platform,
            working_title=title,
        )
