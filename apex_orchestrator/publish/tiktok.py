"""TikTok publishing via the (free) Content Posting API.

Setup: register a free developer app at https://developers.tiktok.com,
add the "Content Posting API" product, complete OAuth to get an access
token with `video.publish` scope, and set TIKTOK_CLIENT_KEY /
TIKTOK_ACCESS_TOKEN. Unaudited apps publish to the account's private
drafts; audited apps can publish directly.
"""

from __future__ import annotations

import os
import time

import requests

from apex_orchestrator.config import CONFIG
from apex_orchestrator.contracts import ContentBrief, PublishResult, Script

INIT_URL = "https://open.tiktokapis.com/v2/post/publish/video/init/"
STATUS_URL = "https://open.tiktokapis.com/v2/post/publish/status/fetch/"


def publish(video_path: str, script: Script, brief: ContentBrief) -> PublishResult:
    if not CONFIG.has_tiktok:
        return PublishResult(
            platform="tiktok",
            status="skipped_no_credentials",
            error="TIKTOK_CLIENT_KEY / TIKTOK_ACCESS_TOKEN not set (see README for the free setup steps)",
        )

    headers = {
        "Authorization": f"Bearer {CONFIG.tiktok_access_token}",
        "Content-Type": "application/json; charset=UTF-8",
    }

    try:
        video_size = os.path.getsize(video_path)
        chunk_size = video_size  # single-chunk upload; fine for short-form clips
        init_body = {
            "post_info": {
                "title": (script.hook or brief.topic)[:150],
                "privacy_level": "SELF_ONLY",  # flip to PUBLIC_TO_EVERYONE once your app is audited
                "disable_duet": False,
                "disable_comment": False,
                "disable_stitch": False,
            },
            "source_info": {
                "source": "FILE_UPLOAD",
                "video_size": video_size,
                "chunk_size": chunk_size,
                "total_chunk_count": 1,
            },
        }
        init_resp = requests.post(INIT_URL, headers=headers, json=init_body, timeout=30)
        init_resp.raise_for_status()
        init_data = init_resp.json()["data"]
        upload_url = init_data["upload_url"]
        publish_id = init_data["publish_id"]

        with open(video_path, "rb") as f:
            video_bytes = f.read()
        upload_resp = requests.put(
            upload_url,
            headers={
                "Content-Type": "video/mp4",
                "Content-Range": f"bytes 0-{video_size - 1}/{video_size}",
            },
            data=video_bytes,
            timeout=120,
        )
        upload_resp.raise_for_status()

        status = "PROCESSING_UPLOAD"
        for _ in range(10):
            time.sleep(2)
            status_resp = requests.post(
                STATUS_URL, headers=headers, json={"publish_id": publish_id}, timeout=30
            )
            status_resp.raise_for_status()
            status = status_resp.json()["data"]["status"]
            if status in ("PUBLISH_COMPLETE", "FAILED"):
                break

        if status == "PUBLISH_COMPLETE":
            return PublishResult(platform="tiktok", status="published", remote_id=publish_id)
        return PublishResult(platform="tiktok", status="failed", remote_id=publish_id, error=f"final status: {status}")

    except Exception as e:  # noqa: BLE001 - publish failures must never crash the run
        return PublishResult(platform="tiktok", status="failed", error=str(e))
