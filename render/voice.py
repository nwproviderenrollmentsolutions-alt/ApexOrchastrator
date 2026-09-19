"""Voice cloning via Coqui XTTS-v2 -- zero-shot from a short reference clip.

No training step: XTTS clones the voice directly from `settings.voice_sample_path`
on every call. A ~10-30s clean recording of your own voice (WAV, mono) is enough.
"""

from __future__ import annotations

from pathlib import Path

from config import settings


class VoiceCloneError(RuntimeError):
    pass


_tts_singleton = None


def _get_tts():
    global _tts_singleton
    if _tts_singleton is None:
        try:
            from TTS.api import TTS
        except ImportError as exc:
            raise VoiceCloneError(
                "coqui-tts is not installed. Run `pip install -r requirements.txt` "
                "on your GPU machine first (see README.md)."
            ) from exc

        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        _tts_singleton = TTS(settings.xtts_model).to(device)
    return _tts_singleton


def synthesize(script_text: str, out_path: Path) -> Path:
    """Render `script_text` in the cloned voice from `settings.voice_sample_path`."""
    if not settings.voice_sample_path.exists():
        raise VoiceCloneError(
            f"Voice sample not found at {settings.voice_sample_path}. "
            "Drop a short (~10-30s) recording of your own voice there (see README.md)."
        )

    tts = _get_tts()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    tts.tts_to_file(
        text=script_text,
        speaker_wav=str(settings.voice_sample_path),
        language="en",
        file_path=str(out_path),
    )
    return out_path
