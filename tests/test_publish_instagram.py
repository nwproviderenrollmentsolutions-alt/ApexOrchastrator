from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from apex_orchestrator.contracts import ContentBrief, Script
from apex_orchestrator.publish import instagram


def _fake_config(has_creds: bool = True, has_url: bool = True):
    return SimpleNamespace(
        has_instagram=has_creds,
        ig_public_video_base_url="https://static.example.com/videos" if has_url else None,
        ig_access_token="token",
        ig_business_account_id="123",
    )


def _script() -> Script:
    return Script(brief_id="b1", hook="hook", beats=[], cta="cta", keywords=[])


def _brief() -> ContentBrief:
    return ContentBrief(brief_id="b1", topic="t", angle="a", cta="c")


def test_publish_success(monkeypatch):
    monkeypatch.setattr(instagram, "CONFIG", _fake_config())

    create_resp = MagicMock()
    create_resp.json.return_value = {"id": "container123"}
    status_resp = MagicMock()
    status_resp.json.return_value = {"status_code": "FINISHED"}
    publish_resp = MagicMock()
    publish_resp.json.return_value = {"id": "media456"}

    with (
        patch.object(instagram.requests, "post", side_effect=[create_resp, publish_resp]),
        patch.object(instagram.requests, "get", return_value=status_resp),
        patch.object(instagram.time, "sleep"),
    ):
        result = instagram.publish("/tmp/final.mp4", _script(), _brief())

    assert result.status == "published"
    assert result.remote_id == "media456"


def test_publish_container_error_returns_failed(monkeypatch):
    monkeypatch.setattr(instagram, "CONFIG", _fake_config())
    create_resp = MagicMock()
    create_resp.json.return_value = {"id": "container123"}
    status_resp = MagicMock()
    status_resp.json.return_value = {"status_code": "ERROR"}

    with (
        patch.object(instagram.requests, "post", return_value=create_resp),
        patch.object(instagram.requests, "get", return_value=status_resp),
        patch.object(instagram.time, "sleep"),
    ):
        result = instagram.publish("/tmp/final.mp4", _script(), _brief())

    assert result.status == "failed"
    assert result.remote_id == "container123"


def test_publish_skipped_without_credentials(monkeypatch):
    monkeypatch.setattr(instagram, "CONFIG", _fake_config(has_creds=False))
    result = instagram.publish("/tmp/final.mp4", _script(), _brief())
    assert result.status == "skipped_no_credentials"


def test_publish_skipped_without_public_url(monkeypatch):
    monkeypatch.setattr(instagram, "CONFIG", _fake_config(has_url=False))
    result = instagram.publish("/tmp/final.mp4", _script(), _brief())
    assert result.status == "skipped_no_credentials"
    assert "IG_PUBLIC_VIDEO_BASE_URL" in result.error
