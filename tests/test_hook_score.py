from apex_orchestrator.contracts import Script
from apex_orchestrator.quality_control.hook_score import _heuristic_score


def test_strong_hook_scores_higher_than_weak_hook():
    strong = Script(brief_id="a", hook="Why does nobody talk about this mistake?", beats=[], cta="", keywords=[])
    weak = Script(brief_id="b", hook="This is a video about a topic.", beats=[], cta="", keywords=[])

    strong_score, _ = _heuristic_score(strong.hook)
    weak_score, _ = _heuristic_score(weak.hook)

    assert strong_score > weak_score


def test_score_is_clamped_to_unit_interval():
    score, _ = _heuristic_score("Stop! Why does nobody know this secret truth about 5 mistakes?")
    assert 0.0 <= score <= 1.0


def test_reasons_are_never_empty():
    _, reasons = _heuristic_score("a plain sentence")
    assert len(reasons) > 0
