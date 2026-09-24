from __future__ import annotations

from pathlib import Path

from apex_orchestrator.contracts import ContentBrief, RenderedAsset
from apex_orchestrator.events import EventBus
from apex_orchestrator.ugc_creator import broll, captions, script_writer, voiceover
from apex_orchestrator.ugc_creator.assembler import FfmpegNotFound, assemble_video


def run_ugc_creator(brief: ContentBrief, work_dir: Path, bus: EventBus) -> RenderedAsset:
    bus.emit("ugc.script", "running", "writing script")
    script, used_llm = script_writer.write_script(brief)
    bus.emit(
        "ugc.script",
        "ok",
        f"{'Groq LLM' if used_llm else 'offline template (no GROQ_API_KEY)'} -> hook: {script.hook[:60]!r}",
        {"script": script},
    )

    bus.emit("ugc.voiceover", "running", "synthesizing narration (edge-tts)")
    vo = voiceover.synthesize_voiceover(script, work_dir / "audio")
    bus.emit("ugc.voiceover", "ok", f"{vo.duration_sec:.1f}s, {len(vo.word_timings)} words", {"voiceover": vo})

    bus.emit("ugc.broll", "running", f"sourcing clips for {script.keywords}")
    clips = broll.fetch_broll(script.keywords, work_dir / "broll")
    n_real = sum(1 for c in clips if c.source == "pexels")
    bus.emit(
        "ugc.broll",
        "ok" if n_real == len(clips) else "mocked",
        f"{n_real}/{len(clips)} from Pexels, rest generated placeholders",
        {"clips": clips},
    )

    bus.emit("ugc.captions", "running", "building caption track")
    srt_path = captions.build_captions(vo, work_dir / "captions", brief.brief_id)
    bus.emit("ugc.captions", "ok", srt_path)

    bus.emit("ugc.assemble", "running", "rendering final video with ffmpeg")
    try:
        video_path = assemble_video(clips, vo, srt_path, work_dir / "video", brief.brief_id)
        bus.emit("ugc.assemble", "ok", video_path)
    except FfmpegNotFound as e:
        bus.emit("ugc.assemble", "failed", str(e))
        raise

    return RenderedAsset(
        brief_id=brief.brief_id,
        video_path=video_path,
        caption_path=srt_path,
        duration_sec=vo.duration_sec,
        script=script,
        voiceover=vo,
        broll_clips=clips,
    )
