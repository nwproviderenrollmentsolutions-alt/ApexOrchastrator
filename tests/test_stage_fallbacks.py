"""Confirms every live-API stage degrades to its mocked path on failure."""

from __future__ import annotations

from unittest.mock import patch

from apex import llm, youtube
from apex.stages.ugc_creator import UGCCreator
from apex.stages.viral_analyst import ViralAnalyst
from apex.stages.viral_radar import ViralRadar


def test_radar_falls_back_to_mock_when_youtube_configured_but_fails():
    radar = ViralRadar(seed=1)
    with patch.object(youtube, "is_configured", return_value=True):
        with patch.object(youtube, "fetch_trending_shorts", side_effect=youtube.YouTubeError("boom")):
            signals = radar.scan(limit=3)
    assert len(signals) == 3


def test_analyst_falls_back_to_mock_when_groq_configured_but_fails():
    radar = ViralRadar(seed=1)
    analyst = ViralAnalyst(seed=1)
    signal = radar.scan(limit=1)[0]
    with patch.object(llm, "is_configured", return_value=True):
        with patch.object(llm, "complete_json", side_effect=llm.LLMError("boom")):
            report = analyst.analyze(signal)
    assert report.signal is signal
    assert report.hook


def test_ugc_creator_falls_back_to_template_when_groq_configured_but_fails():
    from apex.stages.content_strategist import ContentStrategist

    radar = ViralRadar(seed=1)
    analyst = ViralAnalyst(seed=1)
    strategist = ContentStrategist(seed=1)
    creator = UGCCreator(seed=1)

    signal = radar.scan(limit=1)[0]
    strategy = strategist.strategize(analyst.analyze(signal))
    with patch.object(llm, "is_configured", return_value=True):
        with patch.object(llm, "complete", side_effect=llm.LLMError("boom")):
            package = creator.create(strategy)
    assert "[HOOK]" in package.script
    assert "#ad" in package.captions
