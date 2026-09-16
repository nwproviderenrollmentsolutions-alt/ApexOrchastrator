"""Thin client for the free-tier YouTube Data API v3.

Get a free key at https://console.cloud.google.com/apis/credentials (enable
"YouTube Data API v3" on a project first) and put it in `.env` as
`YOUTUBE_API_KEY=...`. See SETUP.md for the full steps.

Free quota is 10,000 units/day; one scan here costs ~101 units
(1 search.list @ 100 + 1 videos.list @ 1).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.parse
import urllib.request

from .config import settings

SEARCH_URL = "https://www.googleapis.com/youtube/v3/search"
VIDEOS_URL = "https://www.googleapis.com/youtube/v3/videos"


class YouTubeError(RuntimeError):
    pass


def is_configured() -> bool:
    return bool(settings.youtube_api_key)


def _get(url: str, params: dict) -> dict:
    query = urllib.parse.urlencode({**params, "key": settings.youtube_api_key})
    try:
        with urllib.request.urlopen(f"{url}?{query}", timeout=15) as response:
            return json.loads(response.read())
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode(errors="replace")[:300]
        raise YouTubeError(f"YouTube API returned {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise YouTubeError(f"YouTube API unreachable: {exc.reason}") from exc


def fetch_trending_shorts(max_results: int = 10, query: str = "#shorts") -> list[dict]:
    """Search for recent short-form videos, then hydrate them with view stats.

    Returns raw API item dicts (snippet + statistics); callers convert them
    into TrendSignal objects.
    """
    if not settings.youtube_api_key:
        raise YouTubeError("YOUTUBE_API_KEY is not set")

    search_payload = _get(
        SEARCH_URL,
        {
            "part": "snippet",
            "q": query,
            "type": "video",
            "order": "viewCount",
            "videoDuration": "short",
            "regionCode": settings.youtube_region,
            "maxResults": str(max_results),
        },
    )
    video_ids = [
        item["id"]["videoId"] for item in search_payload.get("items", []) if item.get("id", {}).get("videoId")
    ]
    if not video_ids:
        return []

    stats_payload = _get(VIDEOS_URL, {"part": "snippet,statistics", "id": ",".join(video_ids)})
    return stats_payload.get("items", [])
