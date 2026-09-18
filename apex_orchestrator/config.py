"""Runtime configuration, loaded from environment / .env.

Every integration here has a free tier. Missing keys don't crash the
pipeline -- they downgrade the relevant stage to a mock/offline mode and
that is reported loudly through the event log so it's obvious what's real
and what's a placeholder.
"""

from __future__ import annotations

import os
from dataclasses import dataclass

try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass


def _env(name: str) -> str | None:
    val = os.environ.get(name, "").strip()
    return val or None


@dataclass(frozen=True)
class Config:
    # LLM for script writing + QC judgment. Free tier: https://console.groq.com
    groq_api_key: str | None = _env("GROQ_API_KEY")
    groq_model: str = os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant")

    # B-roll stock footage. Free tier: https://www.pexels.com/api
    pexels_api_key: str | None = _env("PEXELS_API_KEY")

    # YouTube Data API v3 (free quota). https://console.cloud.google.com
    youtube_client_secrets_file: str | None = _env("YOUTUBE_CLIENT_SECRETS_FILE")
    youtube_token_file: str = os.environ.get("YOUTUBE_TOKEN_FILE", ".secrets/youtube_token.json")

    # TikTok Content Posting API (free developer account).
    # https://developers.tiktok.com
    tiktok_client_key: str | None = _env("TIKTOK_CLIENT_KEY")
    tiktok_access_token: str | None = _env("TIKTOK_ACCESS_TOKEN")

    # Instagram Graph API (free Meta developer app + Business account).
    # https://developers.facebook.com
    ig_access_token: str | None = _env("IG_ACCESS_TOKEN")
    ig_business_account_id: str | None = _env("IG_BUSINESS_ACCOUNT_ID")
    # Graph API requires a publicly reachable URL for the video file.
    ig_public_video_base_url: str | None = _env("IG_PUBLIC_VIDEO_BASE_URL")

    dashboard_host: str = os.environ.get("DASHBOARD_HOST", "127.0.0.1")
    dashboard_port: int = int(os.environ.get("DASHBOARD_PORT", "8765"))

    runs_dir: str = os.environ.get("APEX_RUNS_DIR", "runs")

    @property
    def has_llm(self) -> bool:
        return self.groq_api_key is not None

    @property
    def has_pexels(self) -> bool:
        return self.pexels_api_key is not None

    @property
    def has_youtube(self) -> bool:
        return self.youtube_client_secrets_file is not None

    @property
    def has_tiktok(self) -> bool:
        return self.tiktok_client_key is not None and self.tiktok_access_token is not None

    @property
    def has_instagram(self) -> bool:
        return self.ig_access_token is not None and self.ig_business_account_id is not None

    def integration_summary(self) -> dict[str, bool]:
        return {
            "llm (Groq)": self.has_llm,
            "broll (Pexels)": self.has_pexels,
            "publish:youtube": self.has_youtube,
            "publish:tiktok": self.has_tiktok,
            "publish:instagram": self.has_instagram,
        }


CONFIG = Config()
