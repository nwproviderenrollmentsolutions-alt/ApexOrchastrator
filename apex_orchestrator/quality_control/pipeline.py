from __future__ import annotations

from apex_orchestrator.contracts import ContentBrief, QCReport, RenderedAsset
from apex_orchestrator.events import EventBus
from apex_orchestrator.quality_control import brand_safety, copyright_check, disclosure, hook_score


def run_quality_control(brief: ContentBrief, asset: RenderedAsset, bus: EventBus) -> QCReport:
    bus.emit("qc.hook_score", "running", "scoring hook")
    score, reasons = hook_score.score_hook(asset.script)
    bus.emit("qc.hook_score", "ok" if score >= 0.4 else "failed", f"score={score:.2f}", {"reasons": reasons})

    bus.emit("qc.brand_safety", "running", "scanning for brand-unsafe terms")
    safe, flags = brand_safety.check_brand_safety(asset.script)
    bus.emit("qc.brand_safety", "ok" if safe else "failed", "clean" if safe else f"flags: {flags}")

    bus.emit("qc.disclosure", "running", "checking disclosure requirements")
    disclosed, disc_notes = disclosure.check_disclosure(brief, asset.script)
    bus.emit("qc.disclosure", "ok" if disclosed else "failed", "; ".join(disc_notes))

    bus.emit("qc.copyright", "running", "verifying B-roll licensing")
    licensed, cr_notes = copyright_check.check_copyright(asset.broll_clips)
    bus.emit("qc.copyright", "ok" if licensed else "failed", "; ".join(cr_notes))

    return QCReport(
        brief_id=brief.brief_id,
        hook_score=score,
        hook_reasons=reasons,
        brand_safety_pass=safe,
        brand_safety_flags=flags,
        disclosure_pass=disclosed,
        disclosure_notes=disc_notes,
        copyright_pass=licensed,
        copyright_notes=cr_notes,
    )
