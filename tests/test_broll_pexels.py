from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, patch

from apex_orchestrator.contracts import BRollClip
from apex_orchestrator.ugc_creator import broll


def _fake_config():
    return SimpleNamespace(pexels_api_key="fake-key", has_pexels=True)


def test_fetch_pexels_clip_picks_moderate_resolution_and_downloads(tmp_path, monkeypatch):
    monkeypatch.setattr(broll, "CONFIG", _fake_config())

    search_resp = MagicMock()
    search_resp.json.return_value = {
        "videos": [
            {
                "user": {"name": "Jane Doe"},
                "video_files": [
                    {"height": 2160, "link": "https://example.com/4k.mp4"},
                    {"height": 720, "link": "https://example.com/720.mp4"},
                ],
            }
        ]
    }

    download_resp = MagicMock()
    download_resp.__enter__.return_value = download_resp
    download_resp.iter_content.return_value = [b"fake video bytes"]

    with patch.object(broll.requests, "get", side_effect=[search_resp, download_resp]) as mock_get:
        clip = broll._fetch_pexels_clip("travel", tmp_path, 0)

    assert mock_get.call_count == 2
    downloaded_url = mock_get.call_args_list[1].args[0]
    assert downloaded_url == "https://example.com/720.mp4"  # in the preferred 480-1080 range, not the 4k file

    assert clip.source == "pexels"
    assert "Jane Doe" in clip.attribution
    assert Path(clip.path).read_bytes() == b"fake video bytes"


def test_fetch_pexels_clip_returns_none_when_no_results(tmp_path, monkeypatch):
    monkeypatch.setattr(broll, "CONFIG", _fake_config())
    empty_resp = MagicMock()
    empty_resp.json.return_value = {"videos": []}

    with patch.object(broll.requests, "get", return_value=empty_resp):
        clip = broll._fetch_pexels_clip("travel", tmp_path, 0)

    assert clip is None


def test_fetch_broll_falls_back_to_placeholder_on_pexels_failure(tmp_path, monkeypatch):
    monkeypatch.setattr(broll, "CONFIG", _fake_config())
    placeholder = BRollClip(path="x.mp4", query="travel", source="generated_placeholder", license="generated")

    with (
        patch.object(broll.requests, "get", side_effect=broll.requests.RequestException("boom")),
        patch.object(broll, "_generate_placeholder_clip", return_value=placeholder) as mock_placeholder,
    ):
        clips = broll.fetch_broll(["travel"], tmp_path)

    assert clips == [placeholder]
    mock_placeholder.assert_called_once()
