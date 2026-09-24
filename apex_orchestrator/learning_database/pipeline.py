from __future__ import annotations

from apex_orchestrator.contracts import PerformanceSnapshot
from apex_orchestrator.events import EventBus
from apex_orchestrator.learning_database import store


def run_learning_database(
    run_id: str,
    niche: str,
    framework: str,
    brief_id: str,
    performance_snapshots: list[PerformanceSnapshot],
    bus: EventBus,
) -> None:
    bus.emit("learning.record", "running", "recording run and performance")
    try:
        store.record_run(run_id, niche, framework, brief_id)
        store.record_performance(run_id, performance_snapshots)
        bus.emit("learning.record", "ok", f"recorded run + {len(performance_snapshots)} snapshot(s)")
    except Exception as e:  # noqa: BLE001 - recording failures must never crash the run
        bus.emit("learning.record", "failed", str(e))
