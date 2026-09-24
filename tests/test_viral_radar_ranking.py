from types import SimpleNamespace
from unittest.mock import patch

from apex_orchestrator import events as events_module
from apex_orchestrator.contracts import TrendSignal
from apex_orchestrator.events import EventBus
from apex_orchestrator.viral_radar import pipeline as radar_pipeline


def _signals(velocity: float) -> list[TrendSignal]:
    return [TrendSignal(niche="x", source="google_trends", velocity_score=velocity, sample_titles=["x"])]


def _bus(tmp_path, monkeypatch) -> EventBus:
    monkeypatch.setattr(events_module, "CONFIG", SimpleNamespace(runs_dir=str(tmp_path)))
    return EventBus(run_id="test-ranking", live_console=False)


def test_rank_niches_blends_trend_and_history(tmp_path, monkeypatch):
    def fake_fetch(niche: str) -> list[TrendSignal]:
        return {
            "low_trend_high_history": _signals(0.1),
            "high_trend_no_history": _signals(0.9),
        }[niche]

    def fake_history(niche: str) -> float | None:
        return {"low_trend_high_history": 10000.0, "high_trend_no_history": None}[niche]

    bus = _bus(tmp_path, monkeypatch)
    try:
        with (
            patch.object(radar_pipeline, "_fetch_signals", side_effect=fake_fetch),
            patch.object(radar_pipeline.learning_store, "niche_average_views", side_effect=fake_history),
        ):
            candidates = radar_pipeline.rank_niches(
                ["low_trend_high_history", "high_trend_no_history"], bus, trend_weight=0.6
            )
    finally:
        bus.stop()

    by_niche = {c.niche: c for c in candidates}
    # low_trend_high_history: 0.6*0.1 + 0.4*1.0 (normalized against itself, the only known history) = 0.46
    assert round(by_niche["low_trend_high_history"].composite_score, 2) == 0.46
    # high_trend_no_history: 0.6*0.9 + 0.4*0.5 (neutral, no history) = 0.74
    assert round(by_niche["high_trend_no_history"].composite_score, 2) == 0.74
    assert candidates[0].niche == "high_trend_no_history"


def test_rank_niches_falls_back_to_trend_velocity_when_no_niche_has_history(tmp_path, monkeypatch):
    def fake_fetch(niche: str) -> list[TrendSignal]:
        return {"a": _signals(0.3), "b": _signals(0.8)}[niche]

    bus = _bus(tmp_path, monkeypatch)
    try:
        with (
            patch.object(radar_pipeline, "_fetch_signals", side_effect=fake_fetch),
            patch.object(radar_pipeline.learning_store, "niche_average_views", return_value=None),
        ):
            candidates = radar_pipeline.rank_niches(["a", "b"], bus)
    finally:
        bus.stop()

    assert candidates[0].niche == "b"
    assert candidates[0].historical_avg_views is None


def test_rank_niches_survives_learning_database_error(tmp_path, monkeypatch):
    bus = _bus(tmp_path, monkeypatch)
    try:
        with (
            patch.object(radar_pipeline, "_fetch_signals", return_value=_signals(0.5)),
            patch.object(radar_pipeline.learning_store, "niche_average_views", side_effect=RuntimeError("db locked")),
        ):
            candidates = radar_pipeline.rank_niches(["a"], bus)
    finally:
        bus.stop()

    assert candidates[0].historical_avg_views is None
