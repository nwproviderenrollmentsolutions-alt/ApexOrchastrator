"""Top-level orchestrator.

Two entry points to generate + publish content:
- `run_pipeline(brief)`: ContentBrief -> UGC Creator -> QC -> Publish. Use
  this when you already have a brief (hand-written, loaded from JSON, or
  from your own upstream stage).
- `run_full_pipeline(niche, ...)`: the whole loop, Viral Radar -> Viral
  Analyst AI -> Content Strategist -> [same three stages as above].

Plus one to close the loop after the fact:
- `collect_performance_for_run(run_id)`: Performance Engine -> Learning
  Database, for a run that already published. Analytics aren't available
  right after publishing, so this is meant to run later (hours/days), as
  its own step -- see `--collect-performance` in cli.py.

QC is a hard gate: if a rendered asset fails Quality Control, the run stops
before Publish and the failure reasons are reported through the event bus.
"""

from __future__ import annotations

import json
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path

from apex_orchestrator.config import CONFIG
from apex_orchestrator.content_strategist.pipeline import run_content_strategist
from apex_orchestrator.contracts import ContentBrief, PerformanceSnapshot, PublishResult, QCReport, RenderedAsset
from apex_orchestrator.events import EventBus
from apex_orchestrator.learning_database.pipeline import run_learning_database
from apex_orchestrator.performance_engine.pipeline import run_performance_engine
from apex_orchestrator.publish.pipeline import run_publish
from apex_orchestrator.quality_control.pipeline import run_quality_control
from apex_orchestrator.ugc_creator.pipeline import run_ugc_creator
from apex_orchestrator.viral_analyst.pipeline import run_viral_analyst
from apex_orchestrator.viral_radar.pipeline import run_viral_radar


@dataclass
class PipelineResult:
    brief: ContentBrief
    asset: RenderedAsset
    qc_report: QCReport
    publish_results: list[PublishResult]
    run_id: str
    niche: str
    framework: str


def _execute_from_brief(brief: ContentBrief, framework: str, bus: EventBus, skip_qc_gate: bool) -> PipelineResult:
    work_dir = Path(CONFIG.runs_dir) / bus.run_id / "assets"

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
        niche=brief.topic,
        framework=framework,
    )


def run_pipeline(brief: ContentBrief, skip_qc_gate: bool = False) -> PipelineResult:
    bus = EventBus()
    try:
        return _execute_from_brief(brief, "manual", bus, skip_qc_gate)
    finally:
        bus.stop()


def run_full_pipeline(
    niche: str,
    *,
    product_name: str | None = None,
    cta: str | None = None,
    platforms: list[str] | None = None,
    key_claims: list[str] | None = None,
    disclosure_required: bool = False,
    max_duration_sec: int = 45,
    skip_qc_gate: bool = False,
) -> PipelineResult:
    bus = EventBus()
    try:
        signals = run_viral_radar(niche, bus)
        analysis = run_viral_analyst(niche, signals, bus)
        brief, framework = run_content_strategist(
            uuid.uuid4().hex[:8],
            niche,
            analysis,
            bus,
            product_name=product_name,
            cta=cta,
            platforms=platforms,
            key_claims=key_claims,
            disclosure_required=disclosure_required,
            max_duration_sec=max_duration_sec,
        )
        return _execute_from_brief(brief, framework, bus, skip_qc_gate)
    finally:
        bus.stop()


def collect_performance_for_run(run_id: str) -> list[PerformanceSnapshot]:
    """Performance Engine -> Learning Database for a run that already
    published. Reuses that run's event log (a fresh, non-live EventBus
    bound to the same run_id) so the dashboard shows this as a later
    chapter of the same run instead of a disconnected one.
    """
    summary_path = Path(CONFIG.runs_dir) / run_id / "summary.json"
    summary = json.loads(summary_path.read_text())

    publish_results = [PublishResult(**p) for p in summary["publish_results"]]
    niche = summary["niche"]
    framework = summary["framework"]
    brief_id = summary["brief"]["brief_id"]

    bus = EventBus(run_id=run_id, live_console=False)
    try:
        snapshots = run_performance_engine(publish_results, bus)
        run_learning_database(run_id, niche, framework, brief_id, snapshots, bus)
    finally:
        bus.stop()

    summary["performance_snapshots"] = [asdict(s) for s in snapshots]
    summary_path.write_text(json.dumps(summary, indent=2))
    return snapshots
