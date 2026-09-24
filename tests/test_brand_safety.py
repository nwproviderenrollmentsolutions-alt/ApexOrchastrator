from apex_orchestrator.contracts import Script
from apex_orchestrator.quality_control.brand_safety import check_brand_safety


def test_clean_script_passes():
    script = Script(brief_id="a", hook="Learn to cook pasta fast.", beats=["It's easy."], cta="Try it today.", keywords=[])
    passed, flags = check_brand_safety(script)
    assert passed
    assert flags == []


def test_flagged_terms_are_caught():
    script = Script(
        brief_id="b",
        hook="This is a guaranteed profit strategy.",
        beats=[],
        cta="",
        keywords=[],
    )
    passed, flags = check_brand_safety(script)
    assert not passed
    assert "guaranteed profit" in flags
