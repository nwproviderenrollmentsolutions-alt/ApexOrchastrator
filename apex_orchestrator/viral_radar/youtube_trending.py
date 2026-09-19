"""YouTube "trending now" signal for a niche.

Uses the public videos.list(chart=mostPopular) endpoint, which only needs
a free API key (no OAuth) -- get one free at console.cloud.google.com by
enabling "YouTube Data API v3" and creating an API key credential. This is
deliberately a *different* config value (YOUTUBE_API_KEY) from the OAuth
client used for publishing, since it's a much lighter-weight setup.

TikTok and Instagram have no equivalent free, ToS-compliant trending
endpoint for arbitrary developers, so this pipeline doesn't attempt to
scrape either platform -- Google Trends is the cross-platform proxy signal
instead (see google_trends.py).
"""

from __future__ import annotations

import requests

from apex_orchestrator.config import CONFIG
from apex_orchestrator.contracts import TrendSignal

VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


def fetch_youtube_trending_signal(niche: str, region: str = "US", max_results: int = 50) -> TrendSignal | None:
    """Returns None (not a fallback signal) when there's nothing relevant --
    an empty match against global trending is a real, informative result,
    unlike a network failure.
    """
    if not CONFIG.has_youtube_api_key:
        return None

    try:
        resp = requests.get(
            VIDEOS_URL,
            params={
                "part": "snippet,statistics",
                "chart": "mostPopular",
                "regionCode": region,
                "maxResults": max_results,
                "key": CONFIG.youtube_api_key,
            },
            timeout=20,
        )
        resp.raise_for_status()
        items = resp.json().get("items", [])
    except requests.RequestException:
        return None

    niche_words = [w.lower() for w in niche.split() if len(w) > 2]
    matches = []
    for item in items:
        title = item["snippet"]["title"]
        if any(word in title.lower() for word in niche_words):
            views = int(item.get("statistics", {}).get("viewCount", 0))
            matches.append((title, views))

    if not matches:
        return TrendSignal(niche=niche, source="youtube_trending", velocity_score=0.0, sample_titles=[], region=region)

    matches.sort(key=lambda m: -m[1])
    top_titles = [title for title, _ in matches[:5]]
    avg_views = sum(v for _, v in matches) / len(matches)
    velocity = max(0.0, min(1.0, avg_views / 1_000_000))

    return TrendSignal(niche=niche, source="youtube_trending", velocity_score=velocity, sample_titles=top_titles, region=region)
