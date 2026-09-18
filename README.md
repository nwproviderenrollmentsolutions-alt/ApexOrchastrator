# ApexOrchastrator

YouTube faceless content pipeline: scans TikTok/YouTube Shorts/Instagram for
trends, breaks down why they work, drafts a UGC-style script and package,
gates it through quality control, publishes, measures performance, and feeds
what worked back into the next scan.

```
Viral Radar -> Viral Analyst AI -> Content Strategist -> UGC Creator AI
  -> Quality Control -> [TikTok/Reels, YouTube Shorts] -> Performance Engine
  -> Learning Database -> (loops back to) Viral Radar
```

Two runnable copies of this pipeline live here, both powered by **Groq's
free-tier API** for AI (analysis + script writing) and both mocked
end-to-end with zero setup:

- **`web/`** — a Node/Express dashboard with a live UI. **Start here.**
- **root (`main.py`)** — the original Python CLI.

Both share the same optional free Groq key and free YouTube Data API key.
See [SETUP.md](SETUP.md) for exact steps to get either.

## Quickest start: the web dashboard

```bash
cd web
npm install
npm start
```

Open http://localhost:3000 and click **Run cycle**. Structure:

- `web/server.js` — Express app: static dashboard + JSON API for every stage
  (radar, analyst, strategist, script writer, QC, publisher, performance
  engine, learning database)
- `web/lib/stages/` — one module per box in the pipeline diagram
- `web/lib/groq.js` — Groq (free-tier LLM) client
- `web/lib/youtube.js` — YouTube Data API v3 client
- `web/public/` — the dashboard: `app.js` drives the API in sequence and
  renders live stat tiles, a platform-views chart, an activity log, and a
  recent-items table
- `web/test/` — `node --test` suite covering the stage chain and fallbacks

## Python CLI

- `apex/models.py` — data contracts passed between stages
- `apex/config.py` — loads `.env` / environment variables
- `apex/llm.py` — Groq (free-tier LLM) client
- `apex/youtube.py` — YouTube Data API v3 client
- `apex/stages/` — one module per box in the pipeline diagram
- `apex/pipeline.py` — `Orchestrator`, which chains every stage into a runnable cycle
- `main.py` — CLI entry point
- `tests/` — pytest suite covering each stage, the full chain, and live-API fallback behavior

```bash
python3 main.py --cycles 2 --signals-per-scan 5 --product "your product" --seed 42
```

Drop `--seed` once you have live keys — a fixed seed only pins the mocked
RNG paths, not live LLM/YouTube results.

## Live vs. mocked

Every stage runs mocked with zero setup in both surfaces. Add a free key
and that stage switches to live automatically:

| Key | Powers | Get it |
|---|---|---|
| `GROQ_API_KEY` | Analyst + script writing (both surfaces) | free, see [SETUP.md](SETUP.md) |
| `YOUTUBE_API_KEY` | Real YouTube Shorts trend data (both surfaces) | free, see [SETUP.md](SETUP.md) |

TikTok and Instagram have no free public trend API, so those two stay
mocked in the radar regardless. If a live call fails (bad key, rate limit,
network), that stage logs a warning and falls back to mocked data for that
item — a bad key never crashes a run.

## Test it

```bash
# web dashboard
cd web && npm install && npm test

# Python CLI
pip install -r requirements.txt   # pytest only; the app itself has no deps
python3 -m pytest tests/ -q
```
