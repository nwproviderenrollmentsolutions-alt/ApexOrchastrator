from __future__ import annotations

from apex_orchestrator.contracts import ContentBrief, PublishResult, RenderedAsset
from apex_orchestrator.events import EventBus
from apex_orchestrator.publish import instagram, tiktok, youtube

PLATFORM_MODULES = {
    "youtube_shorts": (youtube, "publish.youtube_shorts"),
    "tiktok": (tiktok, "publish.tiktok"),
    "instagram_reels": (instagram, "publish.instagram"),
}


def run_publish(brief: ContentBrief, asset: RenderedAsset, bus: EventBus) -> list[PublishResult]:
    results: list[PublishResult] = []
    for platform in brief.target_platforms:
        module_entry = PLATFORM_MODULES.get(platform)
        if module_entry is None:
            bus.emit(f"publish.{platform}", "skipped", f"unknown platform {platform!r}")
            continue
        module, stage_name = module_entry

        bus.emit(stage_name, "running", "publishing")
        result = module.publish(asset.video_path, asset.script, brief)
        status_map = {
            "published": "ok",
            "failed": "failed",
            "skipped_no_credentials": "skipped",
        }
        bus.emit(stage_name, status_map.get(result.status, result.status), result.error or result.url or result.status)
        results.append(result)
    return results
