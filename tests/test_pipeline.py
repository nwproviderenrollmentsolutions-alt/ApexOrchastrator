from apex.models import Platform
from apex.pipeline import Orchestrator
from apex.stages.content_strategist import ContentStrategist
from apex.stages.learning_database import LearningDatabase
from apex.stages.performance_engine import PerformanceEngine
from apex.stages.publisher import Publisher
from apex.stages.quality_control import QualityControl
from apex.stages.ugc_creator import UGCCreator
from apex.stages.viral_analyst import ViralAnalyst
from apex.stages.viral_radar import ViralRadar


def test_radar_returns_requested_signal_count():
    radar = ViralRadar(seed=1)
    signals = radar.scan(limit=3)
    assert len(signals) == 3
    assert all(s.platform in Platform for s in signals)


def test_radar_boost_weights_future_scans():
    radar = ViralRadar(seed=1)
    radar.boost("my favorite topic")
    assert radar.boosted_topics == ["my favorite topic"]


def test_full_stage_chain_produces_qc_result():
    radar = ViralRadar(seed=1)
    analyst = ViralAnalyst(seed=1)
    strategist = ContentStrategist(product_context="Replit", seed=1)
    creator = UGCCreator(seed=1)
    qc = QualityControl(seed=1)

    signal = radar.scan(limit=1)[0]
    analysis = analyst.analyze(signal)
    strategy = strategist.strategize(analysis)
    package = creator.create(strategy)
    result = qc.review(package)

    assert result.package is package
    assert 0 <= result.hook_score <= 100
    assert isinstance(result.approved, bool)


def test_publisher_refuses_unapproved_package():
    radar = ViralRadar(seed=2)
    analyst = ViralAnalyst(seed=2)
    strategist = ContentStrategist(seed=2)
    creator = UGCCreator(seed=2)
    qc = QualityControl(seed=2)
    publisher = Publisher(seed=2)

    signal = radar.scan(limit=1)[0]
    package = creator.create(strategist.strategize(analyst.analyze(signal)))
    result = qc.review(package)
    result.brand_safety_pass = False  # force a rejection

    try:
        publisher.publish(result)
        assert False, "expected ValueError for unapproved package"
    except ValueError:
        pass


def test_learning_database_flags_worked_vs_underperformed():
    radar = ViralRadar(seed=3)
    analyst = ViralAnalyst(seed=3)
    strategist = ContentStrategist(seed=3)
    creator = UGCCreator(seed=3)
    qc = QualityControl(seed=3)
    publisher = Publisher(seed=3)
    perf = PerformanceEngine(seed=3)
    learning_db = LearningDatabase()

    signal = radar.scan(limit=1)[0]
    package = creator.create(strategist.strategize(analyst.analyze(signal)))
    result = qc.review(package)
    result.hook_score = 90
    result.brand_safety_pass = True
    result.disclosure_pass = True
    result.copyright_pass = True

    for publish_result in publisher.publish(result, platforms=[Platform.TIKTOK]):
        metrics = perf.measure(publish_result)
        record = learning_db.record(metrics)
        assert isinstance(record.worked, bool)

    assert len(learning_db.records) == 1


def test_orchestrator_run_cycle_end_to_end():
    orchestrator = Orchestrator(product_context="Replit", seed=42)
    results = orchestrator.run_cycle(signals_per_scan=3)
    assert len(results) == 3
    for result in results:
        if result.published:
            assert result.qc_result.approved
            assert len(result.learning_records) >= 1
        else:
            assert result.reject_reason
