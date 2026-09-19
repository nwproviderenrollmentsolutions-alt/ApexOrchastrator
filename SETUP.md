# Getting set up

There are two runnable surfaces in this repo — **`web/`** (a Node dashboard)
and **root** (`main.py`, a Python CLI) — sharing the same two optional free
keys. Neither surface needs any key to run; both fall back to mocked data
with zero setup.

## 1. Run something right now (no keys required)

Web dashboard:

```bash
cd web
npm install
npm start
```

Open http://localhost:3000, click **Run cycle**.

Python CLI:

```bash
python3 main.py --cycles 1 --signals-per-scan 5 --product "your product"
```

## 2. Groq (LLM — powers the Analyst + script-writing stages, both surfaces)

Free tier, no credit card required.

1. Go to https://console.groq.com/keys
2. Sign in (Google/GitHub/email) and click **Create API Key**
3. Copy the key (starts with `gsk_...`)

**Free tier limits** (subject to change, check https://console.groq.com/settings/limits
after signing in): generous per-minute/per-day request and token caps on
models like `llama-3.1-8b-instant`. If you hit a rate limit mid-run, that
stage just falls back to mocked analysis/script for that item.

## 3. YouTube Data API v3 (real trending Shorts for Viral Radar, both surfaces)

Free tier, no credit card required for the free quota.

1. Go to https://console.cloud.google.com/apis/library/youtube.googleapis.com
2. Create a project if you don't have one, then click **Enable**
3. Go to https://console.cloud.google.com/apis/credentials
4. Click **Create Credentials → API key**
5. (Recommended) Click **Restrict key** → restrict it to "YouTube Data API v3"
6. Copy the key

**Free tier limits**: 10,000 quota units/day. Each scan costs ~101 units
(one `search.list` @ 100 + one `videos.list` @ 1), so ~99 scans/day before
hitting quota. TikTok and Instagram have no comparable free public trend
API, so those two platforms stay mocked regardless of this key.

## 4. Wire them in

Web dashboard:

```bash
cd web
cp .env.example .env
# edit .env, paste in GROQ_API_KEY and/or YOUTUBE_API_KEY
npm start
```

Python CLI:

```bash
cp .env.example .env
# edit .env, paste in GROQ_API_KEY and/or YOUTUBE_API_KEY
python3 main.py --cycles 2 --signals-per-scan 5 --product "your product"
```

Each `.env` is gitignored — your keys never get committed. Drop `--seed`
on the CLI once you have live keys, since a fixed seed only pins the
mocked RNG paths, not live LLM/YouTube results.

If a live call fails (rate limit, bad key, network), it logs a warning
(console/stderr) and falls back to mocked data for that item — a bad key
never crashes a run, in either surface.

## 5. (Optional) Render videos in your own cloned avatar/voice

`render/` renders each approved script as a video in **your** voice and
face — free, open-source (Coqui XTTS-v2 + SadTalker), no paid API, but it
needs a GPU machine and real setup: full steps in
[render/README.md](render/README.md). It's decoupled from `web/` — without
it, the dashboard still runs end to end and just marks items
"script-ready, render pending."
