from __future__ import annotations

from apex_orchestrator.contracts import AnalysisReport, ContentBrief
from apex_orchestrator.content_strategist.strategist import build_brief, select_framework
from apex_orchestrator.events import EventBus


def run_content_strategist(
    brief_id: str,
    niche: str,
    analysis: AnalysisReport,
    bus: EventBus,
    *,
    product_name: str | None = None,
    cta: str | None = None,
    platforms: list[str] | None = None,
    key_claims: list[str] | None = None,
    disclosure_required: bool = False,
    max_duration_sec: int = 45,
) -> ContentBrief:
    bus.emit("strategist.brief", "running", "selecting framework and building brief")
    framework = select_framework(analysis)
    brief = build_brief(
        brief_id,
        niche,
        analysis,
        product_name=product_name,
        cta=cta,
        platforms=platforms,
        key_claims=key_claims,
        disclosure_required=disclosure_required,
        max_duration_sec=max_duration_sec,
    )
    bus.emit("strategist.brief", "ok", f"framework={framework.framework}", {"brief": brief})
    return brief
