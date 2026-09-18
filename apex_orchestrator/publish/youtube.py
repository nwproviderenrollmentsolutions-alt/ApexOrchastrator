"""YouTube Shorts publishing via the YouTube Data API v3 (free daily quota).

Setup (free): create a Google Cloud project, enable "YouTube Data API v3",
create an OAuth "Desktop app" client, download the client secret JSON, and
point YOUTUBE_CLIENT_SECRETS_FILE at it. First run opens a browser for the
one-time consent flow; the refresh token is cached at YOUTUBE_TOKEN_FILE.
"""

from __future__ import annotations

from pathlib import Path

from apex_orchestrator.config import CONFIG
from apex_orchestrator.contracts import ContentBrief, PublishResult, Script

SCOPES = ["https://www.googleapis.com/auth/youtube.upload"]


def _get_credentials():
    from google.auth.transport.requests import Request
    from google.oauth2.credentials import Credentials
    from google_auth_oauthlib.flow import InstalledAppFlow

    token_path = Path(CONFIG.youtube_token_file)
    creds = None
    if token_path.exists():
        creds = Credentials.from_authorized_user_file(str(token_path), SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CONFIG.youtube_client_secrets_file, SCOPES)
            creds = flow.run_local_server(port=0)
        token_path.parent.mkdir(parents=True, exist_ok=True)
        token_path.write_text(creds.to_json())
    return creds


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

        creds = _get_credentials()
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
