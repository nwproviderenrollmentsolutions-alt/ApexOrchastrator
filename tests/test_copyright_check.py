from apex_orchestrator.contracts import BRollClip
from apex_orchestrator.quality_control.copyright_check import check_copyright


def test_pexels_and_placeholder_sources_pass():
    clips = [
        BRollClip(path="a.mp4", query="q", source="pexels", license="Pexels License"),
        BRollClip(path="b.mp4", query="q", source="generated_placeholder", license="generated"),
    ]
    passed, _ = check_copyright(clips)
    assert passed


def test_unknown_source_fails():
    clips = [BRollClip(path="a.mp4", query="q", source="random_scrape", license="unknown")]
    passed, notes = check_copyright(clips)
    assert not passed
    assert any("unrecognized" in n for n in notes)
