"""Data contracts shared across pipeline stages.

The full pipeline has 8 stages (see README architecture diagram). This
codebase implements three of them end-to-end: UGC Creator AI, Quality
Control, and Publish. The remaining stages (Viral Radar, Viral Analyst AI,
Content Strategist, Performance Engine, Learning Database) are represented
here only as the data contracts a future implementation must produce or
consume, so they can be plugged in without touching the stages below.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional


# ---------------------------------------------------------------------------
# Upstream contracts (produced by stages not yet implemented)
# ---------------------------------------------------------------------------


@dataclass
class ContentBrief:
    """Handoff from Content Strategist -> UGC Creator AI.

    This is the entry point for the implemented part of the pipeline. Until
    Viral Radar / Analyst / Strategist are built, callers construct this by
    hand or load it from a JSON file (see cli.py --brief).
    """

    brief_id: str
    topic: str
    angle: str
    cta: str
    key_claims: list[str] = field(default_factory=list)
    target_platforms: list[str] = field(default_factory=lambda: ["youtube_shorts"])
    tone: str = "energetic, fast-paced"
    product_name: Optional[str] = None
    source_trend: Optional[str] = None
    disclosure_required: bool = False
    max_duration_sec: int = 45


# ---------------------------------------------------------------------------
# UGC Creator AI
# ---------------------------------------------------------------------------


@dataclass
class Script:
    brief_id: str
    hook: str
    beats: list[str]
    cta: str
    keywords: list[str]
    disclosure_tag: Optional[str] = None

    @property
    def full_text(self) -> str:
        parts = [self.hook, *self.beats, self.cta]
        if self.disclosure_tag:
            parts.append(self.disclosure_tag)
        return "\n".join(p for p in parts if p)


@dataclass
class WordTiming:
    word: str
    start_sec: float
    end_sec: float


@dataclass
class VoiceoverAsset:
    audio_path: str
    duration_sec: float
    word_timings: list[WordTiming] = field(default_factory=list)
    provider: str = "edge-tts"


@dataclass
class BRollClip:
    path: str
    query: str
    source: str  # "pexels" | "generated_placeholder"
    license: str  # e.g. "Pexels License" | "generated"
    attribution: Optional[str] = None


@dataclass
class RenderedAsset:
    brief_id: str
    video_path: str
    caption_path: str
    duration_sec: float
    script: Script
    voiceover: VoiceoverAsset
    broll_clips: list[BRollClip]


# ---------------------------------------------------------------------------
# Quality Control
# ---------------------------------------------------------------------------


@dataclass
class QCReport:
    brief_id: str
    hook_score: float
    hook_reasons: list[str]
    brand_safety_pass: bool
    brand_safety_flags: list[str]
    disclosure_pass: bool
    disclosure_notes: list[str]
    copyright_pass: bool
    copyright_notes: list[str]

    @property
    def passed(self) -> bool:
        return (
            self.hook_score >= 0.4
            and self.brand_safety_pass
            and self.disclosure_pass
            and self.copyright_pass
        )


# ---------------------------------------------------------------------------
# Publish
# ---------------------------------------------------------------------------


@dataclass
class PublishResult:
    platform: str
    status: str  # "published" | "mocked" | "failed" | "skipped_no_credentials"
    remote_id: Optional[str] = None
    url: Optional[str] = None
    error: Optional[str] = None


# ---------------------------------------------------------------------------
# Downstream contracts (consumed by stages not yet implemented)
# ---------------------------------------------------------------------------


@dataclass
class PerformanceSnapshot:
    """What the Performance Engine would collect per published post."""

    platform: str
    remote_id: str
    views: int = 0
    watch_time_sec: float = 0.0
    retention_pct: float = 0.0
    shares: int = 0
    saves: int = 0
    comments: int = 0
    clicks: int = 0
