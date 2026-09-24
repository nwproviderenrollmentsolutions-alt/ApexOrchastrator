"""Builds a burned-in-ready .srt from the voiceover's word timings.

Words are grouped into short chunks (~4 words) so captions read like
short-form-native subtitles rather than a wall of text.
"""

from __future__ import annotations

from pathlib import Path

from apex_orchestrator.contracts import VoiceoverAsset

CHUNK_SIZE = 4


def _fmt_ts(seconds: float) -> str:
    ms = int(round(seconds * 1000))
    h, ms = divmod(ms, 3_600_000)
    m, ms = divmod(ms, 60_000)
    s, ms = divmod(ms, 1000)
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def build_captions(voiceover: VoiceoverAsset, out_dir: Path, brief_id: str) -> str:
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{brief_id}_captions.srt"

    timings = voiceover.word_timings
    lines: list[str] = []
    index = 1
    for i in range(0, len(timings), CHUNK_SIZE):
        chunk = timings[i : i + CHUNK_SIZE]
        if not chunk:
            continue
        start = chunk[0].start_sec
        end = chunk[-1].end_sec
        text = " ".join(w.word for w in chunk)
        lines.append(str(index))
        lines.append(f"{_fmt_ts(start)} --> {_fmt_ts(end)}")
        lines.append(text)
        lines.append("")
        index += 1

    out_path.write_text("\n".join(lines), encoding="utf-8")
    return str(out_path)
