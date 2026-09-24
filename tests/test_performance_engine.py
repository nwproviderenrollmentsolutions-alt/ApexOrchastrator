from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from apex_orchestrator.performance_engine import instagram_insights, tiktok_analytics, youtube_analytics


# --- TikTok ---------------------------------------------------------------


def test_tiktok_fetch_performance_success(monkeypatch):
    monkeypatch.setattr(tiktok_analytics, "CONFIG", SimpleNamespace(has_tiktok=True, tiktok_access_token="token"))
    resp = MagicMock()
    resp.json.return_value = {
        "data": {"videos": [{"view_count": 1000, "like_count": 50, "comment_count": 5, "share_count": 2}]}
    }
    with patch.object(tiktok_analytics.requests, "post", return_value=resp):
        snap = tiktok_analytics.fetch_performance("vid123")

    assert snap.views == 1000
    assert snap.shares == 2
    assert snap.comments == 5


def test_tiktok_fetch_performance_no_video_found(monkeypatch):
    monkeypatch.setattr(tiktok_analytics, "CONFIG", SimpleNamespace(has_tiktok=True, tiktok_access_token="token"))
    resp = MagicMock()
    resp.json.return_value = {"data": {"videos": []}}
    with patch.object(tiktok_analytics.requests, "post", return_value=resp):
        snap = tiktok_analytics.fetch_performance("vid123")

    assert snap.views == 0


def test_tiktok_fetch_performance_without_credentials(monkeypatch):
    monkeypatch.setattr(tiktok_analytics, "CONFIG", SimpleNamespace(has_tiktok=False))
    assert tiktok_analytics.fetch_performance("vid123") is None


def test_tiktok_fetch_performance_network_error_returns_none(monkeypatch):
    monkeypatch.setattr(tiktok_analytics, "CONFIG", SimpleNamespace(has_tiktok=True, tiktok_access_token="token"))
    with patch.object(tiktok_analytics.requests, "post", side_effect=Exception("boom")):
        assert tiktok_analytics.fetch_performance("vid123") is None


# --- Instagram --------------------------------------------------------------


def test_instagram_fetch_performance_success(monkeypatch):
    monkeypatch.setattr(instagram_insights, "CONFIG", SimpleNamespace(has_instagram=True, ig_access_token="token"))
    resp = MagicMock()
    resp.json.return_value = {
        "data": [
            {"name": "plays", "values": [{"value": 1000}]},
            {"name": "shares", "values": [{"value": 10}]},
            {"name": "saved", "values": [{"value": 20}]},
            {"name": "comments", "values": [{"value": 5}]},
        ]
    }
    with patch.object(instagram_insights.requests, "get", return_value=resp):
        snap = instagram_insights.fetch_performance("media123")

    assert snap.views == 1000
    assert snap.saves == 20


def test_instagram_fetch_performance_without_credentials(monkeypatch):
    monkeypatch.setattr(instagram_insights, "CONFIG", SimpleNamespace(has_instagram=False))
    assert instagram_insights.fetch_performance("media123") is None


# --- YouTube ------------------------------------------------------------


def test_youtube_fetch_performance_success(monkeypatch):
    monkeypatch.setattr(youtube_analytics, "CONFIG", SimpleNamespace(has_youtube=True))
    resp = MagicMock()
    resp.json.return_value = {"rows": [[1000, 500.0, 45.5, 10, 3]]}

    with (
        patch.object(youtube_analytics, "get_credentials", return_value=SimpleNamespace(token="access-token")),
        patch.object(youtube_analytics.requests, "get", return_value=resp),
    ):
        snap = youtube_analytics.fetch_performance("yt123")

    assert snap.views == 1000
    assert snap.watch_time_sec == 500.0 * 60
    assert snap.retention_pct == 45.5


def test_youtube_fetch_performance_no_rows(monkeypatch):
    monkeypatch.setattr(youtube_analytics, "CONFIG", SimpleNamespace(has_youtube=True))
    resp = MagicMock()
    resp.json.return_value = {}

    with (
        patch.object(youtube_analytics, "get_credentials", return_value=SimpleNamespace(token="access-token")),
        patch.object(youtube_analytics.requests, "get", return_value=resp),
    ):
        snap = youtube_analytics.fetch_performance("yt123")

    assert snap.views == 0


def test_youtube_fetch_performance_without_credentials(monkeypatch):
    monkeypatch.setattr(youtube_analytics, "CONFIG", SimpleNamespace(has_youtube=False))
    assert youtube_analytics.fetch_performance("yt123") is None
