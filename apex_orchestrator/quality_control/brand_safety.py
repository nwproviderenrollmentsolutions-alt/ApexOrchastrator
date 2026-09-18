"""Keyword-blocklist brand-safety scan.

Deliberately not an LLM call: brand safety gates should be deterministic
and auditable, not subject to model sampling variance. Add to the
blocklist as your brand's needs grow.
"""

from __future__ import annotations

import re

from apex_orchestrator.contracts import Script

BLOCKLIST = [
    "guaranteed profit", "guaranteed return", "risk-free investment",
    "get rich quick", "miracle cure", "no risk",
    "cure cancer", "fda approved" ,  # unverifiable/regulated medical claims
    "kill", "suicide", "self-harm",
    "slur",  # placeholder marker; extend with an actual slur list privately
]


def check_brand_safety(script: Script) -> tuple[bool, list[str]]:
    text = script.full_text.lower()
    flags = [term for term in BLOCKLIST if re.search(re.escape(term), text)]
    return (len(flags) == 0), flags
