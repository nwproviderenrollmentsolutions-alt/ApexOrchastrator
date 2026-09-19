"""Post-publish analytics for a YouTube Shorts video via the free YouTube
Analytics API (v2), reusing the same OAuth credentials as publishing (see
apex_orchestrator/google_auth.py -- the combined scope list includes
yt-analytics.readonly).

Analytics for a freshly published video usually aren't available for a few
hours, so this is meant to be run well after publish, not immediately --
see `--collect-performance` in cli.py.
"""

from __future__ import annotations

import datetime as dt

import requests

from apex_orchestrator.config import CONFIG
from apex_orchestrator.contracts import PerformanceSnapshot
from apex_orchestrator.google_auth import get_credentials

REPORTS_URL = "https://youtubeanalytics.googleapis.com/v2/reports"
METRICS = ["views", "estimatedMinutesWatched", "averageViewPercentage", "comments", "shares"]


def fetch_performance(remote_id: str) -> PerformanceSnapshot | None:
    if not CONFIG.has_youtube:
        return None

    try:
        creds = get_credentials()
        resp = requests.get(
            REPORTS_URL,
            headers={"Authorization": f"Bearer {creds.token}"},
            params={
                "ids": "channel==MINE",
                "startDate": "2020-01-01",
                "endDate": dt.date.today().isoformat(),
                "metrics": ",".join(METRICS),
                "filters": f"video=={remote_id}",
            },
            timeout=30,
        )
        resp.raise_for_status()
        rows = resp.json().get("rows")
        if not rows:
            return PerformanceSnapshot(platform="youtube_shorts", remote_id=remote_id)

        views, watch_minutes, avg_pct, comments, shares = rows[0]
        return PerformanceSnapshot(
            platform="youtube_shorts",
            remote_id=remote_id,
            views=int(views),
            watch_time_sec=float(watch_minutes) * 60,
            retention_pct=float(avg_pct),
            shares=int(shares),
            comments=int(comments),
        )
    except Exception:
        return None
