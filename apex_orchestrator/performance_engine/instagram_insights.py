"""Post-publish insights for an Instagram Reel via the free Graph API
media insights endpoint, reusing the same access token as publishing.
"""

from __future__ import annotations

import requests

from apex_orchestrator.config import CONFIG
from apex_orchestrator.contracts import PerformanceSnapshot
from apex_orchestrator.publish.instagram import GRAPH_BASE

METRICS = "plays,reach,saved,shares,comments,likes"


def fetch_performance(remote_id: str) -> PerformanceSnapshot | None:
    if not CONFIG.has_instagram:
        return None

    try:
        resp = requests.get(
            f"{GRAPH_BASE}/{remote_id}/insights",
            params={"metric": METRICS, "access_token": CONFIG.ig_access_token},
            timeout=30,
        )
        resp.raise_for_status()
        values = {d["name"]: d["values"][0]["value"] for d in resp.json().get("data", [])}

        return PerformanceSnapshot(
            platform="instagram_reels",
            remote_id=remote_id,
            views=values.get("plays", 0),
            shares=values.get("shares", 0),
            saves=values.get("saved", 0),
            comments=values.get("comments", 0),
        )
    except Exception:
        return None
