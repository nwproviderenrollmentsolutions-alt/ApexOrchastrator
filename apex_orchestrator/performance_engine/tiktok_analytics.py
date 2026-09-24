"""Post-publish stats for a TikTok video via the Content Posting API's
video/query endpoint (free, same access token as publishing, `video.list`
scope).

Note: TikTok's API surface for organic post analytics has shifted between
API versions; this targets the documented v2 video/query/ shape as of
writing. Since it's read via the same access_token as publish/tiktok.py,
no extra setup is needed beyond what publishing already requires.
"""

from __future__ import annotations

import requests

from apex_orchestrator.config import CONFIG
from apex_orchestrator.contracts import PerformanceSnapshot

QUERY_URL = "https://open.tiktokapis.com/v2/video/query/"
FIELDS = "id,view_count,like_count,comment_count,share_count"


def fetch_performance(remote_id: str) -> PerformanceSnapshot | None:
    if not CONFIG.has_tiktok:
        return None

    try:
        resp = requests.post(
            QUERY_URL,
            headers={
                "Authorization": f"Bearer {CONFIG.tiktok_access_token}",
                "Content-Type": "application/json",
            },
            params={"fields": FIELDS},
            json={"filters": {"video_ids": [remote_id]}},
            timeout=30,
        )
        resp.raise_for_status()
        videos = resp.json().get("data", {}).get("videos", [])
        if not videos:
            return PerformanceSnapshot(platform="tiktok", remote_id=remote_id)

        v = videos[0]
        return PerformanceSnapshot(
            platform="tiktok",
            remote_id=remote_id,
            views=v.get("view_count", 0),
            shares=v.get("share_count", 0),
            comments=v.get("comment_count", 0),
        )
    except Exception:
        return None
