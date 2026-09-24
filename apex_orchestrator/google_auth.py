"""Shared Google OAuth helper for everything that talks to a YouTube API
under the same account: uploading (publish/youtube.py) and reading
analytics (performance_engine/youtube_analytics.py).

One shared scope list + token file means a single one-time consent screen
covers both, instead of asking the user to re-auth when a new stage needs
a new scope.
"""

from __future__ import annotations

from pathlib import Path

from apex_orchestrator.config import CONFIG

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/yt-analytics.readonly",
]


def get_credentials():
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
