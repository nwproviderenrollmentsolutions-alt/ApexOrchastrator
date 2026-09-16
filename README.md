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

## Structure

- `apex/models.py` — data contracts passed between stages
- `apex/config.py` — loads `.env` / environment variables
- `apex/llm.py` — Groq (free-tier LLM) client
- `apex/youtube.py` — YouTube Data API v3 client
- `apex/stages/` — one module per box in the pipeline diagram
- `apex/pipeline.py` — `Orchestrator`, which chains every stage into a runnable cycle
- `main.py` — CLI entry point
- `tests/` — pytest suite covering each stage, the full chain, and live-API fallback behavior

## Live vs. mocked

Every stage runs mocked with zero setup. Add either free key and that stage
switches to live automatically:

| Key | Powers | Get it |
|---|---|---|
| `GROQ_API_KEY` | Viral Analyst's trend breakdown, UGC Creator's script | free, see [SETUP.md](SETUP.md) |
| `YOUTUBE_API_KEY` | Viral Radar's real YouTube Shorts trend data | free, see [SETUP.md](SETUP.md) |

TikTok and Instagram have no free public trend API, so those two stay
mocked in Viral Radar regardless. If a live call fails (bad key, rate
limit, network), that stage logs a warning to stderr and falls back to
mocked data for that item — a bad key never crashes a run.

```bash
cp .env.example .env   # then paste your keys in
```

See [SETUP.md](SETUP.md) for exact steps to get both free keys.

## Run it

```bash
python3 main.py --cycles 2 --signals-per-scan 5 --product "your product" --seed 42
```

Drop `--seed` once you have live keys — a fixed seed only pins the mocked
RNG paths, not live LLM/YouTube results.

## Test it

```bash
pip install -r requirements.txt   # pytest only; the app itself has no deps
python3 -m pytest tests/ -q
```
