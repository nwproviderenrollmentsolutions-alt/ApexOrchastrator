from __future__ import annotations

from apex_orchestrator.contracts import AnalysisReport, ContentBrief
from apex_orchestrator.content_strategist.strategist import build_brief, select_framework
from apex_orchestrator.events import EventBus
from apex_orchestrator.learning_database import store as learning_store


def _lookup_learned_framework(niche: str) -> str | None:
    try:
        return learning_store.best_framework_for_niche(niche)
    except Exception:
        return None


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
) -> tuple[ContentBrief, str]:
    bus.emit("strategist.brief", "running", "selecting framework and building brief")

    learned_framework = _lookup_learned_framework(niche)
    framework = select_framework(analysis, learned_framework)
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
        learned_framework=learned_framework,
    )

    source = "learning database" if learned_framework else "Viral Analyst AI"
    bus.emit("strategist.brief", "ok", f"framework={framework.framework} (source: {source})", {"brief": brief})
    return brief, framework.framework
