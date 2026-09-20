from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from apex_orchestrator.viral_radar import youtube_trending


def _fake_config(has_key: bool = True):
    return SimpleNamespace(has_youtube_api_key=has_key, youtube_api_key="fake-key")


def test_returns_none_without_api_key(monkeypatch):
    monkeypatch.setattr(youtube_trending, "CONFIG", _fake_config(has_key=False))
    assert youtube_trending.fetch_youtube_trending_signal("budget travel") is None


def test_matches_niche_titles_and_ranks_by_views(monkeypatch):
    monkeypatch.setattr(youtube_trending, "CONFIG", _fake_config())
    items = [
        {"snippet": {"title": "Budget travel tips for 2026"}, "statistics": {"viewCount": "500000"}},
        {"snippet": {"title": "Budget travel hacks that actually work"}, "statistics": {"viewCount": "2000000"}},
        {"snippet": {"title": "Unrelated cooking video"}, "statistics": {"viewCount": "9000000"}},
    ]
    fake_resp = MagicMock()
    fake_resp.json.return_value = {"items": items}

    with patch.object(youtube_trending.requests, "get", return_value=fake_resp) as mock_get:
        signal = youtube_trending.fetch_youtube_trending_signal("budget travel")

    mock_get.assert_called_once()
    assert signal.source == "youtube_trending"
    assert signal.sample_titles[0] == "Budget travel hacks that actually work"
    assert "Unrelated cooking video" not in signal.sample_titles
    assert 0 < signal.velocity_score <= 1.0


def test_no_matches_returns_zero_velocity_signal(monkeypatch):
    monkeypatch.setattr(youtube_trending, "CONFIG", _fake_config())
    fake_resp = MagicMock()
    fake_resp.json.return_value = {"items": [{"snippet": {"title": "totally unrelated"}, "statistics": {"viewCount": "1"}}]}

    with patch.object(youtube_trending.requests, "get", return_value=fake_resp):
        signal = youtube_trending.fetch_youtube_trending_signal("budget travel")

    assert signal.velocity_score == 0.0
    assert signal.sample_titles == []


def test_network_failure_returns_none(monkeypatch):
    monkeypatch.setattr(youtube_trending, "CONFIG", _fake_config())

    with patch.object(youtube_trending.requests, "get", side_effect=youtube_trending.requests.RequestException("boom")):
        assert youtube_trending.fetch_youtube_trending_signal("budget travel") is None
