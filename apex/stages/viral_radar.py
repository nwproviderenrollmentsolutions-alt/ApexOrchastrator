"""VIRAL RADAR: scans TikTok / YouTube Shorts / Instagram for rising content.

YouTube Shorts are pulled live from the free YouTube Data API v3 when
`YOUTUBE_API_KEY` is set (see SETUP.md). TikTok and Instagram have no
equivalent free public trend API, so those two stay mocked regardless.
`boosted_topics` lets the Learning Database steer future scans toward
topics that performed well.
"""

from __future__ import annotations

import random
import sys
from datetime import datetime, timezone

from .. import youtube
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
        signals: list[TrendSignal] = []

        if youtube.is_configured():
            try:
                signals.extend(self._scan_youtube_live(limit))
            except youtube.YouTubeError as exc:
                print(f"[ViralRadar] YouTube live scan failed, falling back to mock: {exc}", file=sys.stderr)

        remaining = limit - len(signals)
        if remaining > 0:
            signals.extend(self._scan_mock(remaining))

        return sorted(signals, key=lambda s: s.velocity, reverse=True)[:limit]

    def boost(self, topic: str) -> None:
        """Called by the Learning Database loop to weight future mock scans."""
        self.boosted_topics.append(topic)

    def _scan_youtube_live(self, limit: int) -> list[TrendSignal]:
        query = self._rng.choice(self.boosted_topics + _TOPICS) if self._rng.random() < 0.5 else "#shorts"
        items = youtube.fetch_trending_shorts(max_results=limit, query=query)
        now = datetime.now(timezone.utc)
        signals = []
        for item in items:
            snippet = item.get("snippet", {})
            stats = item.get("statistics", {})
            view_count = int(stats.get("viewCount", 0))
            published_at = snippet.get("publishedAt")
            hours_live = 1.0
            if published_at:
                published = datetime.fromisoformat(published_at.replace("Z", "+00:00"))
                hours_live = max(1.0, (now - published).total_seconds() / 3600)
            signals.append(
                TrendSignal(
                    id=f"yt-{item.get('id', self._rng.randint(10**6, 10**7))}",
                    platform=Platform.YOUTUBE_SHORTS,
                    source_url=f"https://youtube.com/shorts/{item.get('id', '')}",
                    topic=snippet.get("title", query)[:80],
                    audio_or_sound="original-sound",
                    view_count=view_count,
                    velocity=view_count / hours_live,
                )
            )
        return signals

    def _scan_mock(self, limit: int) -> list[TrendSignal]:
        topics = _TOPICS + self.boosted_topics * 3
        signals = []
        for i in range(limit):
            platform = self._rng.choice([Platform.TIKTOK, Platform.INSTAGRAM_REELS])
            topic = self._rng.choice(topics)
            views = self._rng.randint(50_000, 5_000_000)
            velocity = views / self._rng.randint(1, 48)
            signals.append(
                TrendSignal(
                    id=f"mock-{datetime.utcnow().timestamp():.0f}-{i}",
                    platform=platform,
                    source_url=f"https://{platform.value}.example/post/{self._rng.randint(10**6, 10**7)}",
                    topic=topic,
                    audio_or_sound=self._rng.choice(_SOUNDS),
                    view_count=views,
                    velocity=velocity,
                )
            )
        return signals
