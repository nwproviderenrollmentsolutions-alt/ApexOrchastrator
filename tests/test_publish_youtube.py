from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from apex_orchestrator.contracts import ContentBrief, Script
from apex_orchestrator.publish import youtube


def _script() -> Script:
    return Script(brief_id="b1", hook="hook", beats=[], cta="cta", keywords=[])


def _brief() -> ContentBrief:
    return ContentBrief(brief_id="b1", topic="t", angle="a", cta="c")


def test_publish_success(tmp_path, monkeypatch):
    monkeypatch.setattr(youtube, "CONFIG", SimpleNamespace(has_youtube=True))
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"fake video")

    fake_client = MagicMock()
    fake_client.videos.return_value.insert.return_value.execute.return_value = {"id": "yt123"}

    with (
        patch.object(youtube, "get_credentials", return_value=MagicMock()),
        patch("googleapiclient.discovery.build", return_value=fake_client),
        patch("googleapiclient.http.MediaFileUpload", return_value=MagicMock()),
    ):
        result = youtube.publish(str(video_path), _script(), _brief())

    assert result.status == "published"
    assert result.remote_id == "yt123"
    assert result.url == "https://youtube.com/shorts/yt123"


def test_publish_skips_without_credentials(monkeypatch):
    monkeypatch.setattr(youtube, "CONFIG", SimpleNamespace(has_youtube=False))
    result = youtube.publish("whatever.mp4", _script(), _brief())
    assert result.status == "skipped_no_credentials"


def test_publish_auth_failure_returns_failed_result(tmp_path, monkeypatch):
    monkeypatch.setattr(youtube, "CONFIG", SimpleNamespace(has_youtube=True))
    video_path = tmp_path / "video.mp4"
    video_path.write_bytes(b"fake video")

    with patch.object(youtube, "get_credentials", side_effect=Exception("auth failed")):
        result = youtube.publish(str(video_path), _script(), _brief())

    assert result.status == "failed"
    assert "auth failed" in result.error
