"""Final video assembly via ffmpeg (system binary, free, no API key).

Two passes, kept separate for clarity and easier debugging:
1. Normalize + concatenate the B-roll clips into one silent 9:16 reel.
2. Loop that reel to cover the voiceover's duration, mix in the narration
   audio, and burn in the caption track.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

from apex_orchestrator.contracts import BRollClip, VoiceoverAsset

WIDTH, HEIGHT, FPS = 1080, 1920, 30


class FfmpegNotFound(RuntimeError):
    pass


def _require_ffmpeg() -> None:
    if shutil.which("ffmpeg") is None:
        raise FfmpegNotFound(
            "ffmpeg not found on PATH. Install it (e.g. `apt-get install ffmpeg`) "
            "to render video; script/voiceover/broll/captions still work without it."
        )


def _concat_broll(clips: list[BRollClip], out_path: Path) -> None:
    inputs: list[str] = []
    filters: list[str] = []
    for i, clip in enumerate(clips):
        inputs += ["-i", clip.path]
        filters.append(
            f"[{i}:v]scale={WIDTH}:{HEIGHT}:force_original_aspect_ratio=increase,"
            f"crop={WIDTH}:{HEIGHT},setsar=1,fps={FPS}[v{i}]"
        )
    concat_inputs = "".join(f"[v{i}]" for i in range(len(clips)))
    filters.append(f"{concat_inputs}concat=n={len(clips)}:v=1:a=0[vout]")

    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        *inputs,
        "-filter_complex", "; ".join(filters),
        "-map", "[vout]", "-an",
        str(out_path),
    ]
    subprocess.run(cmd, check=True)


def _finalize(
    broll_concat_path: Path,
    voiceover: VoiceoverAsset,
    captions_srt_path: str,
    out_path: Path,
) -> None:
    style = (
        "FontName=Arial,FontSize=22,PrimaryColour=&H00FFFFFF,"
        "OutlineColour=&H00000000,BorderStyle=3,Outline=2,Alignment=2,MarginV=140"
    )
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-stream_loop", "-1", "-i", str(broll_concat_path),
        "-i", voiceover.audio_path,
        "-filter_complex", f"[0:v]subtitles={captions_srt_path}:force_style='{style}'[vout]",
        "-map", "[vout]", "-map", "1:a",
        "-t", f"{voiceover.duration_sec:.3f}",
        "-c:v", "libx264", "-c:a", "aac", "-shortest",
        str(out_path),
    ]
    subprocess.run(cmd, check=True)


def assemble_video(
    broll_clips: list[BRollClip],
    voiceover: VoiceoverAsset,
    captions_srt_path: str,
    out_dir: Path,
    brief_id: str,
) -> str:
    _require_ffmpeg()
    out_dir.mkdir(parents=True, exist_ok=True)
    concat_path = out_dir / f"{brief_id}_broll_concat.mp4"
    final_path = out_dir / f"{brief_id}_final.mp4"

    _concat_broll(broll_clips, concat_path)
    _finalize(concat_path, voiceover, captions_srt_path, final_path)
    return str(final_path)
