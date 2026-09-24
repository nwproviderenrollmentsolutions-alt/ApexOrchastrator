from __future__ import annotations

from dataclasses import dataclass

from apex_orchestrator.contracts import TrendSignal
from apex_orchestrator.events import EventBus
from apex_orchestrator.learning_database import store as learning_store
from apex_orchestrator.viral_radar.google_trends import fetch_google_trends_signal
from apex_orchestrator.viral_radar.youtube_trending import fetch_youtube_trending_signal


def _fetch_signals(niche: str) -> list[TrendSignal]:
    signals: list[TrendSignal] = [fetch_google_trends_signal(niche)]

    yt_signal = fetch_youtube_trending_signal(niche)
    if yt_signal is not None:
        signals.append(yt_signal)

    return signals


def _avg_velocity(signals: list[TrendSignal]) -> float:
    if not signals:
        return 0.0
    return sum(s.velocity_score for s in signals) / len(signals)


def run_viral_radar(niche: str, bus: EventBus) -> list[TrendSignal]:
    bus.emit("radar.trends", "running", f"scanning trends for {niche!r}")

    signals = _fetch_signals(niche)

    used_sources = [s.source for s in signals]
    bus.emit(
        "radar.trends",
        "ok" if "offline_fallback" not in used_sources else "mocked",
        f"sources: {used_sources}",
        {"signals": signals},
    )
    return signals


@dataclass
class NicheCandidate:
    niche: str
    signals: list[TrendSignal]
    trend_velocity: float
    historical_avg_views: float | None
    composite_score: float


def rank_niches(niches: list[str], bus: EventBus, trend_weight: float = 0.6) -> list[NicheCandidate]:
    """Ranks candidate niches by blending fresh trend velocity with the
    Learning Database's historical performance for each -- this is the
    feedback loop from Performance Engine / Learning Database back to the
    top of the pipeline, deciding *what to research* rather than just how
    to frame it.

    A niche with no recorded history yet gets a neutral 0.5 historical
    score instead of 0, so a brand-new niche can still win on trend
    strength alone rather than being permanently locked out for lack of a
    track record.
    """
    bus.emit("radar.trends", "running", f"ranking {len(niches)} candidate niche(s): {niches}")

    fetched = []
    for niche in niches:
        signals = _fetch_signals(niche)
        velocity = _avg_velocity(signals)
        try:
            historical = learning_store.niche_average_views(niche)
        except Exception:
            historical = None
        fetched.append((niche, signals, velocity, historical))

    known_history = [h for _, _, _, h in fetched if h is not None]
    max_history = max(known_history) if known_history else 0.0

    candidates: list[NicheCandidate] = []
    for niche, signals, velocity, historical in fetched:
        if historical is None or max_history <= 0:
            normalized_history = 0.5
        else:
            normalized_history = historical / max_history
        composite = trend_weight * velocity + (1 - trend_weight) * normalized_history
        candidates.append(
            NicheCandidate(
                niche=niche,
                signals=signals,
                trend_velocity=velocity,
                historical_avg_views=historical,
                composite_score=composite,
            )
        )

    candidates.sort(key=lambda c: c.composite_score, reverse=True)

    summary = ", ".join(f"{c.niche!r} ({c.composite_score:.2f})" for c in candidates)
    bus.emit(
        "radar.trends",
        "ok",
        f"ranked: {summary} -> selected {candidates[0].niche!r}",
        {"candidates": candidates},
    )
    return candidates
