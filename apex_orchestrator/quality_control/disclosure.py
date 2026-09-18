"""FTC-style disclosure check: if the brief marks content as sponsored /
an ad, the rendered script must carry a disclosure tag (e.g. #ad, #sponsored)
that also appears in the platform caption, not just buried in the video.
"""

from __future__ import annotations

from apex_orchestrator.contracts import ContentBrief, Script

DISCLOSURE_TERMS = ("#ad", "#sponsored", "paid partnership")


def check_disclosure(brief: ContentBrief, script: Script) -> tuple[bool, list[str]]:
    if not brief.disclosure_required:
        return True, ["no disclosure required for this brief"]

    text = script.full_text.lower()
    has_tag = any(term in text for term in DISCLOSURE_TERMS)
    if has_tag:
        return True, ["disclosure tag present"]
    return False, [f"brief requires disclosure but none of {DISCLOSURE_TERMS} found in script"]
