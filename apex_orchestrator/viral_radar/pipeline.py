from __future__ import annotations

from apex_orchestrator.contracts import TrendSignal
from apex_orchestrator.events import EventBus
from apex_orchestrator.viral_radar.google_trends import fetch_google_trends_signal
from apex_orchestrator.viral_radar.youtube_trending import fetch_youtube_trending_signal


def run_viral_radar(niche: str, bus: EventBus) -> list[TrendSignal]:
    bus.emit("radar.trends", "running", f"scanning trends for {niche!r}")

    signals: list[TrendSignal] = [fetch_google_trends_signal(niche)]

    yt_signal = fetch_youtube_trending_signal(niche)
    if yt_signal is not None:
        signals.append(yt_signal)

    used_sources = [s.source for s in signals]
    bus.emit(
        "radar.trends",
        "ok" if "offline_fallback" not in used_sources else "mocked",
        f"sources: {used_sources}",
        {"signals": signals},
    )
    return signals
