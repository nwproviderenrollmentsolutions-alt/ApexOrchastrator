"""B-roll sourcing: Pexels free API, or a generated color-bar placeholder
clip (via ffmpeg's lavfi source, no network / no key needed) when Pexels
isn't configured. Either way every clip's license is recorded so Quality
Control's copyright check has something concrete to verify.
"""

from __future__ import annotations

import subprocess
from pathlib import Path

import requests

from apex_orchestrator.config import CONFIG
from apex_orchestrator.contracts import BRollClip

PEXELS_SEARCH_URL = "https://api.pexels.com/videos/search"

PLACEHOLDER_COLORS = ["0x1d4ed8", "0x059669", "0x7c3aed", "0xea580c", "0xdb2777", "0x0891b2"]


def _fetch_pexels_clip(query: str, out_dir: Path, index: int) -> BRollClip | None:
    resp = requests.get(
        PEXELS_SEARCH_URL,
        headers={"Authorization": CONFIG.pexels_api_key},
        params={"query": query, "orientation": "portrait", "per_page": 1},
        timeout=20,
    )
    resp.raise_for_status()
    results = resp.json().get("videos", [])
    if not results:
        return None

    video = results[0]
    # Prefer a moderate-resolution vertical file to keep downloads small.
    files = sorted(video["video_files"], key=lambda f: f.get("height", 0))
    best = next((f for f in files if 480 <= f.get("height", 0) <= 1080), files[-1])

    out_path = out_dir / f"broll_{index}_{query.replace(' ', '_')}.mp4"
    with requests.get(best["link"], stream=True, timeout=60) as r:
        r.raise_for_status()
        with out_path.open("wb") as f:
            for chunk in r.iter_content(chunk_size=1 << 16):
                f.write(chunk)

    return BRollClip(
        path=str(out_path),
        query=query,
        source="pexels",
        license="Pexels License (free to use, no attribution required)",
        attribution=f"Video by {video.get('user', {}).get('name', 'Pexels contributor')} on Pexels",
    )


def _generate_placeholder_clip(query: str, out_dir: Path, index: int, duration_sec: float = 6.0) -> BRollClip:
    color = PLACEHOLDER_COLORS[index % len(PLACEHOLDER_COLORS)]
    out_path = out_dir / f"broll_{index}_placeholder.mp4"
    # 9:16 solid-color clip with the search term burned in, standing in for
    # real footage when no Pexels key is configured.
    drawtext = query.replace(":", "").replace("'", "")[:40]
    cmd = [
        "ffmpeg", "-y", "-loglevel", "error",
        "-f", "lavfi", "-i", f"color=c={color}:s=1080x1920:d={duration_sec}",
        "-vf", f"drawtext=text='{drawtext}':fontcolor=white:fontsize=48:x=(w-text_w)/2:y=(h-text_h)/2",
        str(out_path),
    ]
    subprocess.run(cmd, check=True)
    return BRollClip(
        path=str(out_path),
        query=query,
        source="generated_placeholder",
        license="generated (no external media, safe to publish as-is or swap for real footage)",
    )


def fetch_broll(keywords: list[str], out_dir: Path) -> list[BRollClip]:
    out_dir.mkdir(parents=True, exist_ok=True)
    clips: list[BRollClip] = []
    for i, query in enumerate(keywords):
        clip = None
        if CONFIG.has_pexels:
            try:
                clip = _fetch_pexels_clip(query, out_dir, i)
            except requests.RequestException:
                clip = None
        if clip is None:
            clip = _generate_placeholder_clip(query, out_dir, i)
        clips.append(clip)
    return clips
