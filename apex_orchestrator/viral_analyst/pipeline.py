from __future__ import annotations

from apex_orchestrator.contracts import AnalysisReport, TrendSignal
from apex_orchestrator.events import EventBus
from apex_orchestrator.viral_analyst.analyze import analyze_trends


def run_viral_analyst(niche: str, signals: list[TrendSignal], bus: EventBus) -> AnalysisReport:
    bus.emit("analyst.patterns", "running", "analyzing trend titles")
    report = analyze_trends(niche, signals)
    bus.emit(
        "analyst.patterns",
        "ok" if report.used_llm else "mocked",
        f"pattern={report.content_pattern}, hook={report.hook_pattern[:60]!r}",
        {"analysis": report},
    )
    return report
