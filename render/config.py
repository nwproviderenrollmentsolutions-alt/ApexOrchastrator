"""Loads settings from a `.env` file (if present) and the environment."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

_BASE_DIR = Path(__file__).resolve().parent
_ENV_PATH = _BASE_DIR / ".env"


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
    mock: bool
    host: str
    port: int
    avatar_image_path: Path
    voice_sample_path: Path
    sadtalker_dir: Path | None
    output_dir: Path
    xtts_model: str


def _get_settings() -> Settings:
    return Settings(
        mock=os.environ.get("RENDER_MOCK", "true").lower() != "false",
        host=os.environ.get("HOST", "0.0.0.0"),
        port=int(os.environ.get("PORT", "8000")),
        avatar_image_path=_BASE_DIR / os.environ.get("AVATAR_IMAGE_PATH", "assets/avatar.png"),
        voice_sample_path=_BASE_DIR / os.environ.get("VOICE_SAMPLE_PATH", "assets/voice_sample.wav"),
        sadtalker_dir=(Path(os.environ["SADTALKER_DIR"]).expanduser() if os.environ.get("SADTALKER_DIR") else None),
        output_dir=_BASE_DIR / os.environ.get("OUTPUT_DIR", "output"),
        xtts_model=os.environ.get("XTTS_MODEL", "tts_models/multilingual/multi-dataset/xtts_v2"),
    )


settings = _get_settings()
