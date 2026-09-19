# Render service

Turns an approved script into a talking-head video in **your own cloned
voice and face** -- free, open-source, runs on your GPU machine. This is the
last pipeline stage: `web/` calls it over HTTP once a package passes QC.

Scope: this produces **one continuous clip of you reading the script**. It
does not auto-cut b-roll or match jump-cut editing style -- the Analyst's
`editing_notes` / `b_roll_plan` come through as director's notes for you to
edit with afterward, not automated editing.

## Quick start (mock mode, no GPU needed)

Lets you wire up and test the rest of the pipeline before installing the
real models:

```bash
cd render
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env      # RENDER_MOCK=true by default
python3 app.py
```

`GET http://localhost:8000/health` should report `{"ok": true, "mock": true, ...}`.
`POST /render` returns a fake path instantly instead of a real video.

## Going live: real voice + avatar cloning

### 1. Your assets

- `render/assets/avatar.png` (or .jpg) -- a clear, front-facing photo of you.
  Neutral expression, looking at camera, decent lighting.
- `render/assets/voice_sample.wav` -- ~10-30 seconds of just your voice,
  clean audio (no music/background noise), mono, any reasonable sample rate.
  This is what XTTS clones from on every render -- no separate "training" step.

Neither file is committed (see `.gitignore`) -- they're yours, kept local.

### 2. Voice cloning (Coqui XTTS-v2)

Already covered by `pip install -r requirements.txt` (installs `coqui-tts`).
First real call downloads the XTTS model (a few GB) -- give it a minute.

**GPU strongly recommended.** Install the CUDA build of torch matching your
GPU *before* `pip install -r requirements.txt` (https://pytorch.org/get-started/locally/),
otherwise pip grabs a CPU-only wheel and inference will be slow.

### 3. Talking-head video (SadTalker)

Not a pip package -- a one-time repo clone:

```bash
git clone https://github.com/OpenTalker/SadTalker.git
cd SadTalker
pip install -r requirements.txt
bash scripts/download_models.sh   # pulls the checkpoints, a few GB
```

Then in `render/.env`:
```
SADTALKER_DIR=/absolute/path/to/SadTalker
RENDER_MOCK=false
```

### 4. Run it for real

```bash
cd render
source .venv/bin/activate
python3 app.py
```

`GET /health` should now show `avatarConfigured`, `voiceConfigured`, and
`sadtalkerConfigured` all `true`. `POST /render {"script": "..."}` will take
real time (expect low-single-digit minutes per short clip on a consumer GPU,
first call slower while models load into memory) and return a real `.mp4`
path under `render/output/`.

## Wiring it into the dashboard

In `web/.env`:
```
RENDER_SERVICE_URL=http://localhost:8000
```

If this render service and `web/` run on different machines (e.g. dashboard
on a cheap always-on box, rendering on your GPU rig), point
`RENDER_SERVICE_URL` at that machine's address instead of localhost, and
make sure port 8000 is reachable from the dashboard's machine.

If `RENDER_SERVICE_URL` is unset, or the service is unreachable, or a render
call fails, the dashboard marks that item "script-ready, render pending" and
keeps going -- a render failure never blocks the rest of the pipeline.
