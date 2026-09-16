"""QUALITY CONTROL: gates a UGCPackage before it's allowed to publish.

Checks hook strength, brand safety, disclosure (FTC-style #ad requirement),
and copyright risk (e.g. use of someone else's trending audio without
clearance). Mocked scoring; a real implementation would run text moderation
and a copyright/audio-fingerprint check.
"""

from __future__ import annotations

import random

from ..models import QCResult, UGCPackage

_BANNED_TERMS = {"guaranteed", "cure", "get rich quick"}


class QualityControl:
    def __init__(self, seed: int | None = None, disclosure_required: bool = True) -> None:
        self._rng = random.Random(seed)
        self.disclosure_required = disclosure_required

    def review(self, package: UGCPackage) -> QCResult:
        hook_score = self._score_hook(package)
        brand_safety = self._check_brand_safety(package)
        disclosure = self._check_disclosure(package)
        copyright_ok = self._check_copyright(package)
        return QCResult(
            package=package,
            hook_score=hook_score,
            brand_safety_pass=brand_safety,
            disclosure_pass=disclosure,
            copyright_pass=copyright_ok,
        )

    def _score_hook(self, package: UGCPackage) -> float:
        base = package.strategy.analysis.virality_score
        jitter = self._rng.uniform(-10, 10)
        return round(max(0.0, min(100.0, base + jitter)), 1)

    def _check_brand_safety(self, package: UGCPackage) -> bool:
        text = (package.script + package.captions).lower()
        return not any(term in text for term in _BANNED_TERMS)

    def _check_disclosure(self, package: UGCPackage) -> bool:
        if not self.disclosure_required:
            return True
        return "#ad" in package.captions.lower()

    def _check_copyright(self, package: UGCPackage) -> bool:
        return package.strategy.analysis.signal.audio_or_sound != "unlicensed-track"
