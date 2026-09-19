from __future__ import annotations

from apex_orchestrator.contracts import PerformanceSnapshot, PublishResult
from apex_orchestrator.events import EventBus
from apex_orchestrator.performance_engine import instagram_insights, tiktok_analytics, youtube_analytics

PLATFORM_FETCHERS = {
    "youtube_shorts": youtube_analytics.fetch_performance,
    "tiktok": tiktok_analytics.fetch_performance,
    "instagram_reels": instagram_insights.fetch_performance,
}


def run_performance_engine(publish_results: list[PublishResult], bus: EventBus) -> list[PerformanceSnapshot]:
    bus.emit("performance.collect", "running", "collecting post-publish analytics")

    snapshots: list[PerformanceSnapshot] = []
    for result in publish_results:
        if result.status != "published" or not result.remote_id:
            continue
        fetcher = PLATFORM_FETCHERS.get(result.platform)
        if fetcher is None:
            continue
        snapshot = fetcher(result.remote_id)
        if snapshot is not None:
            snapshots.append(snapshot)

    if snapshots:
        bus.emit("performance.collect", "ok", f"{len(snapshots)} snapshot(s) collected", {"snapshots": snapshots})
    else:
        bus.emit(
            "performance.collect",
            "skipped",
            "no analytics available yet (nothing published, or too soon after publish -- try again later)",
        )
    return snapshots
