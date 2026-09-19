"""Lip-synced talking-head video via SadTalker (https://github.com/OpenTalker/SadTalker).

SadTalker isn't a pip package -- it's a research repo you clone once and run
via its inference.py script (see README.md for the one-time setup). This
just shells out to it: photo + audio in, lip-synced mp4 out.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from config import settings


class VideoRenderError(RuntimeError):
    pass


def render(audio_path: Path, out_dir: Path) -> Path:
    if settings.sadtalker_dir is None:
        raise VideoRenderError("SADTALKER_DIR is not set. See README.md for one-time SadTalker setup.")
    if not settings.sadtalker_dir.exists():
        raise VideoRenderError(f"SADTALKER_DIR does not exist: {settings.sadtalker_dir}")
    if not settings.avatar_image_path.exists():
        raise VideoRenderError(
            f"Avatar photo not found at {settings.avatar_image_path}. "
            "Drop a clear, front-facing photo there (see README.md)."
        )

    inference_script = settings.sadtalker_dir / "inference.py"
    if not inference_script.exists():
        raise VideoRenderError(f"SadTalker inference.py not found at {inference_script}")

    out_dir.mkdir(parents=True, exist_ok=True)
    cmd = [
        "python",
        str(inference_script),
        "--driven_audio",
        str(audio_path),
        "--source_image",
        str(settings.avatar_image_path),
        "--result_dir",
        str(out_dir),
        "--still",
        "--preprocess",
        "full",
    ]
    result = subprocess.run(cmd, cwd=settings.sadtalker_dir, capture_output=True, text=True, timeout=1800)
    if result.returncode != 0:
        raise VideoRenderError(f"SadTalker exited {result.returncode}: {result.stderr[-2000:]}")

    produced = sorted(out_dir.glob("**/*.mp4"), key=lambda p: p.stat().st_mtime, reverse=True)
    if not produced:
        raise VideoRenderError(f"SadTalker ran but no .mp4 appeared under {out_dir}")

    final_path = out_dir / "final.mp4"
    shutil.copy(produced[0], final_path)
    return final_path
