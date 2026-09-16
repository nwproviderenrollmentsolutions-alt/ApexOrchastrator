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
- `apex/stages/` — one module per box in the pipeline diagram
- `apex/pipeline.py` — `Orchestrator`, which chains every stage into a runnable cycle
- `main.py` — CLI entry point
- `tests/` — pytest suite covering each stage and the full chain

All stages are currently mocked (deterministic with a `--seed`, randomized
otherwise) so the pipeline runs with no external credentials. Each stage's
docstring notes what to swap in for real platform/API calls.

## Run it

```bash
python3 main.py --cycles 2 --signals-per-scan 5 --product "your product" --seed 42
```

## Test it

```bash
python3 -m pytest tests/ -q
```
