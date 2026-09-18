"""Top-level orchestrator: ContentBrief -> UGC Creator -> QC -> Publish.

QC is a hard gate: if a rendered asset fails Quality Control, the run stops
before Publish and the failure reasons are reported through the event bus.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from apex_orchestrator.config import CONFIG
from apex_orchestrator.contracts import ContentBrief, PublishResult, QCReport, RenderedAsset
from apex_orchestrator.events import EventBus
from apex_orchestrator.publish.pipeline import run_publish
from apex_orchestrator.quality_control.pipeline import run_quality_control
from apex_orchestrator.ugc_creator.pipeline import run_ugc_creator


@dataclass
class PipelineResult:
    brief: ContentBrief
    asset: RenderedAsset
    qc_report: QCReport
    publish_results: list[PublishResult]
    run_id: str


def run_pipeline(brief: ContentBrief, skip_qc_gate: bool = False) -> PipelineResult:
    bus = EventBus()
    work_dir = Path(CONFIG.runs_dir) / bus.run_id / "assets"

    try:
        asset = run_ugc_creator(brief, work_dir, bus)
        qc_report = run_quality_control(brief, asset, bus)

        publish_results: list[PublishResult] = []
        if qc_report.passed or skip_qc_gate:
            publish_results = run_publish(brief, asset, bus)
        else:
            reasons = []
            if qc_report.hook_score < 0.4:
                reasons.append(f"hook_score={qc_report.hook_score:.2f} < 0.4")
            if not qc_report.brand_safety_pass:
                reasons.append(f"brand safety flags: {qc_report.brand_safety_flags}")
            if not qc_report.disclosure_pass:
                reasons.append(f"disclosure: {qc_report.disclosure_notes}")
            if not qc_report.copyright_pass:
                reasons.append(f"copyright: {qc_report.copyright_notes}")
            for platform in brief.target_platforms:
                bus.emit(f"publish.{platform}", "skipped", "blocked by failed QC gate: " + "; ".join(reasons))

        return PipelineResult(
            brief=brief,
            asset=asset,
            qc_report=qc_report,
            publish_results=publish_results,
            run_id=bus.run_id,
        )
    finally:
        bus.stop()
