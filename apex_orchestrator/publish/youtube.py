"""YouTube Shorts publishing via the YouTube Data API v3 (free daily quota).

Setup (free): create a Google Cloud project, enable "YouTube Data API v3",
create an OAuth "Desktop app" client, download the client secret JSON, and
point YOUTUBE_CLIENT_SECRETS_FILE at it. First run opens a browser for the
one-time consent flow; the refresh token is cached at YOUTUBE_TOKEN_FILE.
"""

from __future__ import annotations

from apex_orchestrator.config import CONFIG
from apex_orchestrator.contracts import ContentBrief, PublishResult, Script
from apex_orchestrator.google_auth import get_credentials


def publish(video_path: str, script: Script, brief: ContentBrief) -> PublishResult:
    if not CONFIG.has_youtube:
        return PublishResult(
            platform="youtube_shorts",
            status="skipped_no_credentials",
            error="YOUTUBE_CLIENT_SECRETS_FILE not set (see README for the free setup steps)",
        )

    try:
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload

        creds = get_credentials()
        youtube = build("youtube", "v3", credentials=creds)

        title = (script.hook or brief.topic)[:95] + " #shorts"
        body = {
            "snippet": {
                "title": title,
                "description": script.full_text,
                "categoryId": "22",
            },
            "status": {"privacyStatus": "public", "selfDeclaredMadeForKids": False},
        }
        media = MediaFileUpload(video_path, chunksize=-1, resumable=True, mimetype="video/mp4")
        request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
        response = request.execute()
        video_id = response["id"]
        return PublishResult(
            platform="youtube_shorts",
            status="published",
            remote_id=video_id,
            url=f"https://youtube.com/shorts/{video_id}",
        )
    except Exception as e:  # noqa: BLE001 - publish failures must never crash the run
        return PublishResult(platform="youtube_shorts", status="failed", error=str(e))
