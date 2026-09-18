"""Verifies every asset in the rendered video came from a licensed source.

Since B-roll only ever comes from two places in this pipeline (Pexels'
free license, or a locally generated placeholder clip), this check is a
whitelist of allowed `BRollClip.source` values -- it fails loudly if a
future stage ever wires in an unlicensed source without updating this list.
"""

from __future__ import annotations

from apex_orchestrator.contracts import BRollClip

ALLOWED_SOURCES = {"pexels", "generated_placeholder"}


def check_copyright(clips: list[BRollClip]) -> tuple[bool, list[str]]:
    notes: list[str] = []
    ok = True
    for clip in clips:
        if clip.source not in ALLOWED_SOURCES:
            ok = False
            notes.append(f"clip {clip.path!r} has unrecognized/unlicensed source {clip.source!r}")
        else:
            notes.append(f"{clip.path}: {clip.license}")
    return ok, notes
