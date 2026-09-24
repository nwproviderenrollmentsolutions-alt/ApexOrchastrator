from apex_orchestrator.content_strategist.strategist import build_brief, select_framework
from apex_orchestrator.contracts import AnalysisReport


def _analysis(content_pattern: str = "listicle") -> AnalysisReport:
    return AnalysisReport(
        niche="budget travel",
        hook_pattern="uses a specific number",
        content_pattern=content_pattern,
        editing_notes="fast cuts",
        cta_style="follow for part 2",
        predicted_comment_themes=["agreement"],
    )


def test_select_framework_maps_known_pattern():
    framework = select_framework(_analysis("myth_vs_fact"))
    assert framework.framework == "myth_vs_fact"
    assert "Myth vs. Fact" in framework.angle


def test_select_framework_falls_back_for_unknown_pattern():
    framework = select_framework(_analysis("something_new"))
    assert "Problem-Agitate-Solve" in framework.angle


def test_build_brief_uses_cta_override_when_given():
    brief = build_brief("id1", "budget travel", _analysis(), cta="Follow now")
    assert brief.cta == "Follow now"


def test_build_brief_falls_back_to_analysis_cta_style():
    brief = build_brief("id1", "budget travel", _analysis())
    assert brief.cta == "follow for part 2"


def test_build_brief_includes_product_name_in_angle():
    brief = build_brief("id1", "budget travel", _analysis(), product_name="TravelApp")
    assert "TravelApp" in brief.angle
    assert brief.product_name == "TravelApp"


def test_build_brief_defaults_platforms_when_none_given():
    brief = build_brief("id1", "budget travel", _analysis())
    assert brief.target_platforms == ["youtube_shorts"]


def test_learned_framework_overrides_analyst_pattern():
    framework = select_framework(_analysis("listicle"), learned_framework="storytime")
    assert framework.framework == "storytime"
    assert "learning database" in framework.angle


def test_no_override_note_when_learned_matches_analyst():
    framework = select_framework(_analysis("listicle"), learned_framework="listicle")
    assert framework.framework == "listicle"
    assert "learning database" not in framework.angle
