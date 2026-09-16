"""Orchestrator: wires every stage in the diagram into one runnable pipeline.

Radar -> Analyst -> Strategist -> UGC Creator -> QC -> Publish (fan-out) ->
Performance Engine -> Learning Database -> back into Radar via boosted topics.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .models import LearningRecord, Platform, QCResult
from .stages.content_strategist import ContentStrategist
from .stages.learning_database import LearningDatabase
from .stages.performance_engine import PerformanceEngine
from .stages.publisher import Publisher
from .stages.quality_control import QualityControl
from .stages.ugc_creator import UGCCreator
from .stages.viral_analyst import ViralAnalyst
from .stages.viral_radar import ViralRadar


@dataclass
class CycleResult:
    qc_result: QCResult
    published: bool
    learning_records: list[LearningRecord] = field(default_factory=list)
    reject_reason: str | None = None


class Orchestrator:
    def __init__(self, product_context: str = "our product", seed: int | None = None) -> None:
        self.radar = ViralRadar(seed=seed)
        self.analyst = ViralAnalyst(seed=seed)
        self.strategist = ContentStrategist(product_context=product_context, seed=seed)
        self.ugc_creator = UGCCreator(seed=seed)
        self.qc = QualityControl(seed=seed)
        self.publisher = Publisher(seed=seed)
        self.performance_engine = PerformanceEngine(seed=seed)
        self.learning_db = LearningDatabase()

    def run_cycle(self, signals_per_scan: int = 5) -> list[CycleResult]:
        """One full pass: scan -> analyze -> strategize -> create -> QC ->
        publish -> measure -> learn -> boost the radar, for every signal
        found in this scan."""
        results = []
        for signal in self.radar.scan(limit=signals_per_scan):
            analysis = self.analyst.analyze(signal)
            strategy = self.strategist.strategize(analysis)
            package = self.ugc_creator.create(strategy)
            qc_result = self.qc.review(package)

            if not qc_result.approved:
                results.append(
                    CycleResult(
                        qc_result=qc_result,
                        published=False,
                        reject_reason=self._reject_reason(qc_result),
                    )
                )
                continue

            publish_results = self.publisher.publish(qc_result, platforms=self._fanout(strategy.target_platform))
            learning_records = [self.learning_db.record(self.performance_engine.measure(pr)) for pr in publish_results]

            for record in learning_records:
                if record.worked:
                    self.radar.boost(signal.topic)

            results.append(CycleResult(qc_result=qc_result, published=True, learning_records=learning_records))
        return results

    @staticmethod
    def _fanout(primary: Platform) -> list[Platform]:
        # Cross-post to the two short-form platforms the diagram publishes to.
        targets = {Platform.TIKTOK, Platform.YOUTUBE_SHORTS}
        targets.add(primary)
        return sorted(targets, key=lambda p: p.value)

    @staticmethod
    def _reject_reason(qc_result: QCResult) -> str:
        reasons = []
        if qc_result.hook_score < 60:
            reasons.append(f"hook_score {qc_result.hook_score} < 60")
        if not qc_result.brand_safety_pass:
            reasons.append("brand safety failed")
        if not qc_result.disclosure_pass:
            reasons.append("missing disclosure")
        if not qc_result.copyright_pass:
            reasons.append("copyright risk")
        return "; ".join(reasons)
