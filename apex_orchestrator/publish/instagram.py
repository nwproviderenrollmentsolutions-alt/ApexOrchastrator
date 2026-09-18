"""Instagram Reels publishing via the (free) Instagram Graph API.

Setup: create a free Meta developer app, connect an Instagram Business/
Creator account, get a long-lived access token with `instagram_content_
publish`, and set IG_ACCESS_TOKEN / IG_BUSINESS_ACCOUNT_ID.

Graph API fetches the video from a public URL rather than accepting a
direct upload, so IG_PUBLIC_VIDEO_BASE_URL must point at somewhere the
rendered .mp4 is already reachable (e.g. a free static host you sync
`runs/<id>/video/` to). Without it, this stage is reported as skipped
rather than guessing at a URL.
"""

from __future__ import annotations

import time
from pathlib import Path

import requests

from apex_orchestrator.config import CONFIG
from apex_orchestrator.contracts import ContentBrief, PublishResult, Script

GRAPH_BASE = "https://graph.facebook.com/v19.0"


def publish(video_path: str, script: Script, brief: ContentBrief) -> PublishResult:
    if not CONFIG.has_instagram:
        return PublishResult(
            platform="instagram_reels",
            status="skipped_no_credentials",
            error="IG_ACCESS_TOKEN / IG_BUSINESS_ACCOUNT_ID not set (see README for the free setup steps)",
        )
    if not CONFIG.ig_public_video_base_url:
        return PublishResult(
            platform="instagram_reels",
            status="skipped_no_credentials",
            error=(
                "IG_PUBLIC_VIDEO_BASE_URL not set: the Graph API requires a publicly "
                "reachable video URL, not a direct file upload"
            ),
        )

    try:
        video_url = f"{CONFIG.ig_public_video_base_url.rstrip('/')}/{Path(video_path).name}"
        caption = script.full_text

        create_resp = requests.post(
            f"{GRAPH_BASE}/{CONFIG.ig_business_account_id}/media",
            data={
                "media_type": "REELS",
                "video_url": video_url,
                "caption": caption,
                "access_token": CONFIG.ig_access_token,
            },
            timeout=30,
        )
        create_resp.raise_for_status()
        container_id = create_resp.json()["id"]

        status = "IN_PROGRESS"
        for _ in range(15):
            time.sleep(3)
            status_resp = requests.get(
                f"{GRAPH_BASE}/{container_id}",
                params={"fields": "status_code", "access_token": CONFIG.ig_access_token},
                timeout=30,
            )
            status_resp.raise_for_status()
            status = status_resp.json()["status_code"]
            if status in ("FINISHED", "ERROR"):
                break

        if status != "FINISHED":
            return PublishResult(
                platform="instagram_reels", status="failed", remote_id=container_id, error=f"container status: {status}"
            )

        publish_resp = requests.post(
            f"{GRAPH_BASE}/{CONFIG.ig_business_account_id}/media_publish",
            data={"creation_id": container_id, "access_token": CONFIG.ig_access_token},
            timeout=30,
        )
        publish_resp.raise_for_status()
        media_id = publish_resp.json()["id"]
        return PublishResult(platform="instagram_reels", status="published", remote_id=media_id)

    except Exception as e:  # noqa: BLE001 - publish failures must never crash the run
        return PublishResult(platform="instagram_reels", status="failed", error=str(e))
