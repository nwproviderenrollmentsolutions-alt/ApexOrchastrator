from apex_orchestrator.contracts import ContentBrief, Script
from apex_orchestrator.quality_control.disclosure import check_disclosure


def _brief(disclosure_required: bool) -> ContentBrief:
    return ContentBrief(
        brief_id="a", topic="t", angle="a", cta="c", disclosure_required=disclosure_required
    )


def test_no_disclosure_required_passes_regardless_of_tag():
    script = Script(brief_id="a", hook="h", beats=[], cta="c", keywords=[])
    passed, _ = check_disclosure(_brief(False), script)
    assert passed


def test_missing_tag_fails_when_required():
    script = Script(brief_id="a", hook="h", beats=[], cta="c", keywords=[])
    passed, notes = check_disclosure(_brief(True), script)
    assert not passed
    assert notes


def test_tag_present_passes_when_required():
    script = Script(brief_id="a", hook="h", beats=[], cta="c", keywords=[], disclosure_tag="#ad")
    passed, _ = check_disclosure(_brief(True), script)
    assert passed
