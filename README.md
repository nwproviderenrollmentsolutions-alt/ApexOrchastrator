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

Two runnable copies of this pipeline live here:

- **`web/`** — a Node/Express dashboard with a live UI. AI runs via
  **[Puter.js](https://developer.puter.com) in the browser — zero API keys**,
  just a free Puter.com account. **Start here.**
- **root (`main.py`)** — the original Python CLI, using Groq for AI.

Both are mocked end-to-end with zero setup, and both share the same
optional free YouTube Data API key for real trend data. See
[SETUP.md](SETUP.md) for exact steps.

## Quickest start: the web dashboard

```bash
cd web
npm install
npm start
```

Open http://localhost:3000 and click **Run cycle**. First AI call opens a
free Puter.com login popup; after that it just works. Structure:

- `web/server.js` — Express app: static dashboard + JSON API for every
  deterministic stage (radar, strategist, QC, publisher, performance engine,
  learning database)
- `web/lib/stages/` — one module per box in the pipeline diagram
- `web/lib/youtube.js` — YouTube Data API v3 client (server-side)
- `web/public/` — the dashboard itself; `app.js` calls `puter.ai.chat()`
  client-side for the Analyst and UGC Creator (script) stages, POSTing
  results back through the server's API to continue the pipeline
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
and that stage switches to live:

| Key | Powers | Where |
|---|---|---|
| *(none — Puter.js)* | Analyst + script writing | `web/` dashboard, in-browser |
| `GROQ_API_KEY` | Analyst + script writing | `main.py` CLI |
| `YOUTUBE_API_KEY` | Real YouTube Shorts trend data | both |

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
