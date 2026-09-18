from apex_orchestrator.contracts import ContentBrief
from apex_orchestrator.ugc_creator.script_writer import write_script


def test_fallback_writer_used_without_llm_key():
    brief = ContentBrief(
        brief_id="a",
        topic="budget travel hacks",
        angle="the $20/day method",
        cta="follow for part 2",
        key_claims=["book flights on Tuesdays", "use points for hotels"],
    )
    script, used_llm = write_script(brief)

    assert used_llm is False  # no GROQ_API_KEY configured in the test environment
    assert script.brief_id == "a"
    assert script.hook
    assert "book flights on Tuesdays" in script.beats
    assert script.cta == "follow for part 2"


def test_disclosure_tag_added_when_required():
    brief = ContentBrief(brief_id="b", topic="t", angle="a", cta="c", disclosure_required=True)
    script, _ = write_script(brief)
    assert script.disclosure_tag == "#ad"
    assert "#ad" in script.full_text
