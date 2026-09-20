from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from apex_orchestrator.contracts import ContentBrief, Script
from apex_orchestrator.publish import tiktok


def _fake_config(has_tiktok: bool = True):
    return SimpleNamespace(has_tiktok=has_tiktok, tiktok_access_token="token123")


def _script() -> Script:
    return Script(brief_id="b1", hook="hook", beats=[], cta="cta", keywords=[])


def _brief() -> ContentBrief:
    return ContentBrief(brief_id="b1", topic="t", angle="a", cta="c")


def _init_and_upload_mocks():
    init_resp = MagicMock()
    init_resp.json.return_value = {"data": {"upload_url": "https://upload.example.com", "publish_id": "pub123"}}
    upload_resp = MagicMock()
    return init_resp, upload_resp


def test_publish_success_extracts_public_post_id(tmp_path, monkeypatch):
    monkeypatch.setattr(tiktok, "CONFIG", _fake_config())
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"fake video")

    init_resp, upload_resp = _init_and_upload_mocks()
    status_resp = MagicMock()
    status_resp.json.return_value = {
        "data": {"status": "PUBLISH_COMPLETE", "publicaly_available_post_id": ["real_video_id"]}
    }

    with (
        patch.object(tiktok.requests, "post", side_effect=[init_resp, status_resp]),
        patch.object(tiktok.requests, "put", return_value=upload_resp),
        patch.object(tiktok.time, "sleep"),
    ):
        result = tiktok.publish(str(video_path), _script(), _brief())

    assert result.status == "published"
    assert result.remote_id == "real_video_id"


def test_publish_falls_back_to_publish_id_when_no_post_id(tmp_path, monkeypatch):
    monkeypatch.setattr(tiktok, "CONFIG", _fake_config())
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"fake video")

    init_resp, upload_resp = _init_and_upload_mocks()
    status_resp = MagicMock()
    status_resp.json.return_value = {"data": {"status": "PUBLISH_COMPLETE"}}

    with (
        patch.object(tiktok.requests, "post", side_effect=[init_resp, status_resp]),
        patch.object(tiktok.requests, "put", return_value=upload_resp),
        patch.object(tiktok.time, "sleep"),
    ):
        result = tiktok.publish(str(video_path), _script(), _brief())

    assert result.status == "published"
    assert result.remote_id == "pub123"


def test_publish_failed_status_returns_failed_result(tmp_path, monkeypatch):
    monkeypatch.setattr(tiktok, "CONFIG", _fake_config())
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"fake video")

    init_resp, upload_resp = _init_and_upload_mocks()
    status_resp = MagicMock()
    status_resp.json.return_value = {"data": {"status": "FAILED"}}

    with (
        patch.object(tiktok.requests, "post", side_effect=[init_resp, status_resp]),
        patch.object(tiktok.requests, "put", return_value=upload_resp),
        patch.object(tiktok.time, "sleep"),
    ):
        result = tiktok.publish(str(video_path), _script(), _brief())

    assert result.status == "failed"
    assert result.remote_id == "pub123"


def test_publish_skips_without_credentials(monkeypatch):
    monkeypatch.setattr(tiktok, "CONFIG", _fake_config(has_tiktok=False))
    result = tiktok.publish("whatever.mp4", _script(), _brief())
    assert result.status == "skipped_no_credentials"
