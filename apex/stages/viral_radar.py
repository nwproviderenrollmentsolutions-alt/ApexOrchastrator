"""VIRAL RADAR: scans TikTok / YouTube Shorts / Instagram for rising content.

Mocked for now — swap `scan()` for real platform API / scraper calls once
credentials are available. `boosted_topics` lets the Learning Database steer
future scans toward topics that performed well.
"""

from __future__ import annotations

import random
from datetime import datetime

from ..models import Platform, TrendSignal

_TOPICS = [
    "morning routine hack",
    "budgeting app walkthrough",
    "AI coding tip",
    "side hustle breakdown",
    "productivity myth debunked",
    "before/after transformation",
    "day in the life",
    "unpopular opinion take",
]

_SOUNDS = ["trending-audio-1", "trending-audio-2", "original-sound", "voiceover-only"]


class ViralRadar:
    def __init__(self, seed: int | None = None) -> None:
        self._rng = random.Random(seed)
        self.boosted_topics: list[str] = []

    def scan(self, limit: int = 5) -> list[TrendSignal]:
        """Return the top `limit` trending candidates across all platforms."""
        topics = self._TOPICS_weighted()
        signals = []
        for i in range(limit):
            platform = self._rng.choice(list(Platform))
            topic = self._rng.choice(topics)
            views = self._rng.randint(50_000, 5_000_000)
            velocity = views / self._rng.randint(1, 48)
            signals.append(
                TrendSignal(
                    id=f"trend-{datetime.utcnow().timestamp():.0f}-{i}",
                    platform=platform,
                    source_url=f"https://{platform.value}.example/post/{self._rng.randint(10**6, 10**7)}",
                    topic=topic,
                    audio_or_sound=self._rng.choice(_SOUNDS),
                    view_count=views,
                    velocity=velocity,
                )
            )
        return sorted(signals, key=lambda s: s.velocity, reverse=True)

    def boost(self, topic: str) -> None:
        """Called by the Learning Database loop to weight future scans."""
        self.boosted_topics.append(topic)

    def _TOPICS_weighted(self) -> list[str]:
        return _TOPICS + self.boosted_topics * 3
