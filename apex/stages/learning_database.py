"""LEARNING DATABASE: stores every cycle's outcome and feeds winners back to the Viral Radar.

In-memory store for now — swap `_records` for a real DB (Postgres/Supabase)
once this needs to persist across runs.
"""

from __future__ import annotations

from ..models import LearningRecord, PerformanceMetrics

_WORKED_ENGAGEMENT_THRESHOLD = 0.03


class LearningDatabase:
    def __init__(self) -> None:
        self._records: list[LearningRecord] = []

    def record(self, metrics: PerformanceMetrics) -> LearningRecord:
        worked = metrics.engagement_rate >= _WORKED_ENGAGEMENT_THRESHOLD
        topic = metrics.publish_result.qc_result.package.strategy.analysis.signal.topic
        notes = (
            f"topic='{topic}' engagement_rate={metrics.engagement_rate:.4f} "
            f"retention={metrics.retention_pct}% -> {'worked' if worked else 'underperformed'}"
        )
        record = LearningRecord(metrics=metrics, worked=worked, notes=notes)
        self._records.append(record)
        return record

    @property
    def records(self) -> list[LearningRecord]:
        return list(self._records)

    def winning_topics(self) -> list[str]:
        return [
            r.metrics.publish_result.qc_result.package.strategy.analysis.signal.topic
            for r in self._records
            if r.worked
        ]
