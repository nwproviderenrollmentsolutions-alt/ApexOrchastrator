"""PERFORMANCE ENGINE: pulls post-publish metrics.

Mocked — swap `measure()` for real platform analytics API calls (TikTok
Business API, YouTube Analytics API, IG Graph API) once available.
"""

from __future__ import annotations

import random

from ..models import PerformanceMetrics, PublishResult


class PerformanceEngine:
    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)

    def measure(self, publish_result: PublishResult) -> PerformanceMetrics:
        # Higher QC hook_score biases toward better simulated performance,
        # so the learning loop below has a real signal to chase.
        quality = publish_result.qc_result.hook_score / 100
        views = int(self._rng.randint(1_000, 200_000) * (0.5 + quality))
        return PerformanceMetrics(
            publish_result=publish_result,
            views=views,
            watch_time_seconds=round(views * self._rng.uniform(3, 25), 1),
            retention_pct=round(min(100.0, 30 + quality * 50 + self._rng.uniform(-10, 10)), 1),
            shares=int(views * self._rng.uniform(0.001, 0.02)),
            saves=int(views * self._rng.uniform(0.001, 0.03)),
            comments=int(views * self._rng.uniform(0.0005, 0.01)),
            clicks=int(views * self._rng.uniform(0.001, 0.015)),
        )
