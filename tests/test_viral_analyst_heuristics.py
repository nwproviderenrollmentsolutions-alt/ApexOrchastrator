from apex_orchestrator.viral_analyst.analyze import _dominant_content_pattern, _dominant_hook_pattern, _heuristic_analysis


def test_numbered_titles_detected_as_listicle():
    titles = ["5 mistakes everyone makes", "7 tips for beginners", "3 things nobody tells you"]
    assert _dominant_content_pattern(titles) == "listicle"


def test_how_to_titles_detected_as_tutorial():
    titles = ["How to save money fast", "A guide to budgeting"]
    assert _dominant_content_pattern(titles) == "tutorial"


def test_empty_titles_default_to_problem_agitate_solve():
    assert _dominant_content_pattern([]) == "problem_agitate_solve"


def test_hook_pattern_detects_question_titles():
    titles = ["Why does nobody talk about this?", "What if you could save more?"]
    pattern = _dominant_hook_pattern(titles)
    assert "curiosity" in pattern or "how/why/what" in pattern


def test_heuristic_analysis_never_uses_llm_and_fills_all_fields():
    report = _heuristic_analysis("budget travel", ["5 travel hacks", "7 flight tips"])
    assert report.used_llm is False
    assert report.niche == "budget travel"
    assert report.content_pattern == "listicle"
    assert report.editing_notes
    assert report.cta_style
    assert len(report.predicted_comment_themes) > 0
