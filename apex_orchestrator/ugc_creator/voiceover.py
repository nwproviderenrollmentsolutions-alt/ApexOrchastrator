"""Narration via edge-tts (Microsoft Edge's neural TTS, free, no API key).

edge-tts streams WordBoundary events alongside the audio, which gives us
per-word timings for free -- exactly what we need to drive animated
captions without a separate transcription pass.
"""

from __future__ import annotations

import asyncio
from pathlib import Path

import edge_tts

from apex_orchestrator.contracts import Script, VoiceoverAsset, WordTiming

DEFAULT_VOICE = "en-US-GuyNeural"


async def _synthesize(text: str, voice: str, out_path: Path) -> list[WordTiming]:
    communicate = edge_tts.Communicate(text, voice)
    timings: list[WordTiming] = []
    with out_path.open("wb") as audio_file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                audio_file.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                start = chunk["offset"] / 1e7  # 100-ns units -> seconds
                dur = chunk["duration"] / 1e7
                timings.append(WordTiming(word=chunk["text"], start_sec=start, end_sec=start + dur))
    return timings


def synthesize_voiceover(script: Script, out_dir: Path, voice: str = DEFAULT_VOICE) -> VoiceoverAsset:
    out_dir.mkdir(parents=True, exist_ok=True)
    audio_path = out_dir / f"{script.brief_id}_voiceover.mp3"
    narration = "\n".join([script.hook, *script.beats, script.cta])

    timings = asyncio.run(_synthesize(narration, voice, audio_path))
    duration = timings[-1].end_sec if timings else 0.0

    return VoiceoverAsset(
        audio_path=str(audio_path),
        duration_sec=duration,
        word_timings=timings,
        provider=f"edge-tts:{voice}",
    )
