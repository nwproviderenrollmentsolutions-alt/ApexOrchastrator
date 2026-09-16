"""Data contracts passed between pipeline stages.

Every stage in the diagram takes one of these in and returns the next one out,
so the pipeline can chain stages without each one knowing the others' internals.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum


class Platform(str, Enum):
    TIKTOK = "tiktok"
    YOUTUBE_SHORTS = "youtube_shorts"
    INSTAGRAM_REELS = "instagram_reels"


@dataclass
class TrendSignal:
    """One candidate spotted by the Viral Radar."""

    id: str
    platform: Platform
    source_url: str
    topic: str
    audio_or_sound: str
    view_count: int
    velocity: float  # views/hour, used to separate trending from merely popular
    detected_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class AnalysisReport:
    """Viral Analyst AI's breakdown of a TrendSignal."""

    signal: TrendSignal
    hook: str
    pattern: str
    story_structure: str
    editing_notes: str
    cta: str
    top_comments_themes: list[str]
    virality_score: float  # 0-100


@dataclass
class ContentStrategy:
    """Content Strategist's pick of framework + brand angle."""

    analysis: AnalysisReport
    framework: str  # e.g. "problem-agitate-solve", "listicle", "poet-story"
    product_angle: str
    target_platform: Platform
    working_title: str


@dataclass
class UGCPackage:
    """UGC Creator AI's output: everything needed to render a video."""

    strategy: ContentStrategy
    script: str
    avatar_or_voice: str
    b_roll_plan: list[str]
    captions: str


@dataclass
class QCResult:
    """Quality Control's verdict on a UGCPackage."""

    package: UGCPackage
    hook_score: float  # 0-100
    brand_safety_pass: bool
    disclosure_pass: bool
    copyright_pass: bool

    @property
    def approved(self) -> bool:
        return self.brand_safety_pass and self.disclosure_pass and self.copyright_pass and self.hook_score >= 60


@dataclass
class PublishResult:
    """Result of pushing an approved package to a platform."""

    qc_result: QCResult
    platform: Platform
    post_url: str
    published_at: datetime = field(default_factory=datetime.utcnow)


@dataclass
class PerformanceMetrics:
    """Performance Engine's read on a published post."""

    publish_result: PublishResult
    views: int
    watch_time_seconds: float
    retention_pct: float
    shares: int
    saves: int
    comments: int
    clicks: int

    @property
    def engagement_rate(self) -> float:
        if self.views == 0:
            return 0.0
        return (self.shares + self.saves + self.comments) / self.views


@dataclass
class LearningRecord:
    """What the Learning Database keeps, and feeds back to the Viral Radar."""

    metrics: PerformanceMetrics
    worked: bool
    notes: str
