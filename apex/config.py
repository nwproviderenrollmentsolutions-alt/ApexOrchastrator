"""Loads settings from a `.env` file (if present) and the environment.

Stdlib-only, no python-dotenv dependency: parses `KEY=VALUE` lines and sets
them via `os.environ.setdefault` so real environment variables always win.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"


def _load_dotenv(path: Path) -> None:
    if not path.exists():
        return
    for raw_line in path.read_text().splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            os.environ.setdefault(key, value)


_load_dotenv(_ENV_PATH)


@dataclass(frozen=True)
class Settings:
    groq_api_key: str | None
    groq_model: str
    youtube_api_key: str | None
    youtube_region: str


def _get_settings() -> Settings:
    return Settings(
        groq_api_key=os.environ.get("GROQ_API_KEY") or None,
        groq_model=os.environ.get("GROQ_MODEL", "llama-3.1-8b-instant"),
        youtube_api_key=os.environ.get("YOUTUBE_API_KEY") or None,
        youtube_region=os.environ.get("YOUTUBE_REGION", "US"),
    )


settings = _get_settings()
