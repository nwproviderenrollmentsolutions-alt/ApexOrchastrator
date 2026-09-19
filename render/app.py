"""Render service: script text in, a talking-head video in your cloned
voice/face out. Runs on your GPU machine.

RENDER_MOCK=true (the default) skips real inference and returns a fake path
immediately -- useful for wiring up and testing the rest of the pipeline
before XTTS/SadTalker are actually installed. Set RENDER_MOCK=false once
you've done the setup in README.md.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

from config import settings

app = FastAPI(title="ApexOrchastrator render service")


class RenderRequest(BaseModel):
    script: str
    title: str | None = None


class RenderResponse(BaseModel):
    videoPath: str
    mock: bool
    tookSeconds: float


@app.get("/health")
def health():
    return {
        "ok": True,
        "mock": settings.mock,
        "avatarConfigured": settings.avatar_image_path.exists(),
        "voiceConfigured": settings.voice_sample_path.exists(),
        "sadtalkerConfigured": bool(settings.sadtalker_dir and settings.sadtalker_dir.exists()),
    }


@app.post("/render", response_model=RenderResponse)
def render_endpoint(req: RenderRequest):
    started = time.monotonic()
    job_id = uuid.uuid4().hex[:12]

    if settings.mock:
        settings.output_dir.mkdir(parents=True, exist_ok=True)
        fake_path = settings.output_dir / f"{job_id}.mock.mp4"
        fake_path.write_text(f"[mock render]\ntitle={req.title}\nscript=\n{req.script}\n")
        return RenderResponse(videoPath=str(fake_path), mock=True, tookSeconds=time.monotonic() - started)

    try:
        from voice import VoiceCloneError, synthesize
        from video import VideoRenderError, render

        audio_path = settings.output_dir / job_id / "narration.wav"
        synthesize(req.script, audio_path)
        video_path = render(audio_path, settings.output_dir / job_id)
    except (VoiceCloneError, VideoRenderError) as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc

    return RenderResponse(videoPath=str(video_path), mock=False, tookSeconds=time.monotonic() - started)


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=settings.host, port=settings.port)
