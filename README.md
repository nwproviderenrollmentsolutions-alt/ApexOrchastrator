# ApexOrchastrator

Faceless short-form content automation: UGC Creator AI → Quality Control → Publish,
built entirely on free-tier services. This is a working slice of the larger 8-stage
pipeline (Viral Radar → Viral Analyst AI → Content Strategist → **UGC Creator AI** →
**Quality Control** → Publish → Performance Engine → Learning Database) — the three
bolded stages are implemented; the rest are documented as data contracts in
`apex_orchestrator/contracts.py` so they can be plugged in later without touching
this code.

## What it does

Given a `ContentBrief` (topic, angle, CTA, target platforms — normally the handoff
from a Content Strategist stage that doesn't exist yet, so you supply it directly):

1. **UGC Creator AI** — writes a script, synthesizes a faceless voiceover, sources
   9:16 B-roll, builds animated captions, and renders a final MP4 with ffmpeg.
2. **Quality Control** — scores the hook, scans for brand-unsafe language, checks
   FTC-style disclosure requirements, and verifies every clip's license. Failing QC
   blocks publish.
3. **Publish** — posts the rendered video to YouTube Shorts, TikTok, and/or
   Instagram Reels via each platform's official free API.

Every stage reports through a shared event bus, visible live in the terminal and in
a local browser dashboard.

## Free services used

| Purpose | Service | Free tier |
|---|---|---|
| Script writing + QC judgment | [Groq](https://console.groq.com) | Yes (generous free API) |
| Voiceover | [edge-tts](https://github.com/rany2/edge-tts) | Yes, no key needed |
| B-roll | [Pexels API](https://www.pexels.com/api) | Yes |
| Video rendering | ffmpeg | Yes, local binary |
| YouTube Shorts | [YouTube Data API v3](https://console.cloud.google.com) | Yes, daily quota |
| TikTok | [Content Posting API](https://developers.tiktok.com) | Yes, developer account |
| Instagram Reels | [Graph API](https://developers.facebook.com) | Yes, Business account |

**Nothing here requires a paid key.** Any integration you skip just runs in an
offline/mock mode instead of crashing — the terminal and dashboard say so
explicitly (`off` vs `on`).

## Setup

```bash
pip install -r requirements.txt
sudo apt-get install ffmpeg   # or your platform's equivalent
cp .env.example .env          # fill in whichever free keys you have
```

See `.env.example` for where to get each key. At minimum, nothing is required —
`GROQ_API_KEY` and `PEXELS_API_KEY` noticeably improve quality (real script
writing / hook judging and real stock footage instead of placeholders); the
publish keys are only needed once you're ready to actually post.

## Running it

```bash
python -m apex_orchestrator.cli \
  --topic "5 budget travel hacks" \
  --angle "the \$20/day method" \
  --cta "Follow for part 2" \
  --claims "book flights on Tuesdays|use points for hotels" \
  --platforms youtube_shorts,tiktok
```

Or load a brief from JSON (shape matches `ContentBrief` in `contracts.py`):

```bash
python -m apex_orchestrator.cli --brief brief.json
```

Each run gets an id and writes everything to `runs/<run_id>/`: rendered assets,
`events.jsonl` (the full event log), and `summary.json` (QC + publish results).

### Watching it run

- **Terminal**: a live `rich` table updates in place as each stage runs — no setup.
- **Browser**: `python -m apex_orchestrator.dashboard`, then open
  `http://127.0.0.1:8765` and pick a run from the dropdown. It polls the same
  event log, so it works for runs in progress or already finished.

## Project layout

```
apex_orchestrator/
  contracts.py          # data contracts for all 8 pipeline stages
  config.py              # env-driven config, reports which integrations are active
  events.py               # event bus: rich terminal live view + JSONL log
  llm.py                   # Groq wrapper, raises LLMUnavailable if unconfigured
  pipeline.py               # top-level orchestrator (brief -> ugc -> qc -> publish)
  cli.py                     # entrypoint
  dashboard.py                # FastAPI live dashboard
  ugc_creator/                 # script, voiceover, broll, captions, ffmpeg assembly
  quality_control/               # hook score, brand safety, disclosure, copyright
  publish/                        # youtube / tiktok / instagram clients
tests/                              # offline-testable logic (QC heuristics, contracts)
```

## Notes on the publish stage

- **YouTube**: uses OAuth (installed-app flow); the first run opens a browser for
  one-time consent, then caches a refresh token.
- **TikTok**: unaudited developer apps publish to the account's private drafts
  only (`privacy_level: SELF_ONLY` in `publish/tiktok.py`) — flip it once your app
  passes TikTok's review.
- **Instagram**: the Graph API fetches video from a public URL rather than
  accepting a direct upload, so `IG_PUBLIC_VIDEO_BASE_URL` must point somewhere
  the rendered `.mp4` is already reachable.

## Not yet built

`Viral Radar`, `Viral Analyst AI`, `Content Strategist` (upstream of UGC Creator)
and `Performance Engine`, `Learning Database` (downstream of Publish) are only
sketched as data contracts (`ContentBrief` in, `PerformanceSnapshot` out) in
`contracts.py`. Wiring those up is the natural next step — trend research fits
the `shortform-trend-scout` skill, and the Performance Engine would poll each
platform's analytics API and feed `PerformanceSnapshot`s back into brief
generation.
