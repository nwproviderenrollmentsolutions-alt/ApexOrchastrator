"""Tests for the live-API wrappers, using stubbed network calls only.

None of these hit the real network or require an API key.
"""

from __future__ import annotations

import json
from unittest.mock import patch

from apex import llm, youtube
from apex.config import Settings


def _settings(**overrides):
    base = dict(groq_api_key=None, groq_model="llama-3.1-8b-instant", youtube_api_key=None, youtube_region="US")
    base.update(overrides)
    return Settings(**base)


def test_llm_not_configured_without_key():
    with patch.object(llm, "settings", _settings()):
        assert llm.is_configured() is False


def test_llm_complete_raises_without_key():
    with patch.object(llm, "settings", _settings()):
        try:
            llm.complete("system", "user")
            assert False, "expected LLMError"
        except llm.LLMError:
            pass


class _FakeResponse:
    def __init__(self, payload: dict) -> None:
        self._payload = json.dumps(payload).encode()

    def read(self) -> bytes:
        return self._payload

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


def test_llm_complete_parses_groq_response():
    fake_payload = {"choices": [{"message": {"content": "hello world"}}]}
    with patch.object(llm, "settings", _settings(groq_api_key="fake-key")):
        with patch("urllib.request.urlopen", return_value=_FakeResponse(fake_payload)):
            result = llm.complete("system", "user")
    assert result == "hello world"


def test_llm_complete_json_strips_markdown_fencing():
    fake_payload = {"choices": [{"message": {"content": '```json\n{"a": 1}\n```'}}]}
    with patch.object(llm, "settings", _settings(groq_api_key="fake-key")):
        with patch("urllib.request.urlopen", return_value=_FakeResponse(fake_payload)):
            result = llm.complete_json("system", "user")
    assert result == {"a": 1}


def test_youtube_not_configured_without_key():
    with patch.object(youtube, "settings", _settings()):
        assert youtube.is_configured() is False


def test_youtube_fetch_raises_without_key():
    with patch.object(youtube, "settings", _settings()):
        try:
            youtube.fetch_trending_shorts()
            assert False, "expected YouTubeError"
        except youtube.YouTubeError:
            pass


def test_youtube_fetch_trending_shorts_hydrates_stats():
    search_payload = {"items": [{"id": {"videoId": "abc123"}}]}
    stats_payload = {
        "items": [
            {
                "id": "abc123",
                "snippet": {"title": "cool video", "publishedAt": "2026-09-16T00:00:00Z"},
                "statistics": {"viewCount": "1000"},
            }
        ]
    }
    responses = [_FakeResponse(search_payload), _FakeResponse(stats_payload)]
    with patch.object(youtube, "settings", _settings(youtube_api_key="fake-key")):
        with patch("urllib.request.urlopen", side_effect=responses):
            items = youtube.fetch_trending_shorts(max_results=1)
    assert len(items) == 1
    assert items[0]["statistics"]["viewCount"] == "1000"
