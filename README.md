# ApexOrchastrator

Faceless short-form content automation, built entirely on free-tier services:
Viral Radar → Viral Analyst AI → Content Strategist → UGC Creator AI → Quality
Control → Publish. That's six of the full 8-stage pipeline; Performance Engine
and Learning Database (feeding results back into the next Radar pass) are
documented as data contracts in `apex_orchestrator/contracts.py` so they can be
plugged in without touching this code.

## What it does

Given a niche (e.g. `"budget travel"`):

1. **Viral Radar** — pulls a trend velocity signal from Google Trends (free,
   no key) and, if configured, real trending-video titles from YouTube's free
   public API, for that niche.
2. **Viral Analyst AI** — turns those titles into a concrete take: dominant
   hook pattern, content framework (listicle / myth-vs-fact / tutorial /
   storytime / before-after / problem-agitate-solve), editing notes, CTA
   style, predicted comment themes.
3. **Content Strategist** — picks the framework and builds a `ContentBrief`
   (topic, angle, CTA, claims, target platforms, product tie-in).
4. **UGC Creator AI** — writes a script, synthesizes a faceless voiceover,
   sources 9:16 B-roll, builds animated captions, and renders a final MP4.
5. **Quality Control** — scores the hook, scans for brand-unsafe language,
   checks FTC-style disclosure requirements, verifies every clip's license.
   Failing QC blocks Publish.
6. **Publish** — posts to YouTube Shorts, TikTok, and/or Instagram Reels via
   each platform's official free API.

You can also skip straight to step 4 with a hand-written brief (see
**Running it** below) if you don't want automated trend research.

Every stage reports through a shared event bus, visible live in the terminal and
in a local browser dashboard.

## Free services used

| Purpose | Service | Free tier |
|---|---|---|
| Trend velocity | [Google Trends](https://trends.google.com) via `pytrends` | Yes, no key (unofficial, best-effort) |
| Trending video titles | [YouTube Data API v3](https://console.cloud.google.com) (API key, read-only) | Yes, daily quota |
| Script writing + QC/Analyst judgment | [Groq](https://console.groq.com) | Yes (generous free API) |
| Voiceover | [edge-tts](https://github.com/rany2/edge-tts) | Yes, no key needed |
| B-roll | [Pexels API](https://www.pexels.com/api) | Yes |
| Video rendering | ffmpeg | Yes, local binary |
| YouTube Shorts publish | [YouTube Data API v3](https://console.cloud.google.com) (OAuth) | Yes, daily quota |
| TikTok publish | [Content Posting API](https://developers.tiktok.com) | Yes, developer account |
| Instagram Reels publish | [Graph API](https://developers.facebook.com) | Yes, Business account |

**Nothing here requires a paid key.** Any integration you skip just runs in an
offline/mock mode instead of crashing — the terminal and dashboard say so
explicitly (`off` vs `on`), and Google Trends failures (it's an unofficial
scraper, not a stable API) fall back the same way.

TikTok and Instagram have no free, ToS-compliant trending endpoint for
third-party developers, so Viral Radar doesn't scrape either — Google Trends is
used as the cross-platform proxy signal instead.

## Setup

```bash
pip install -r requirements.txt
sudo apt-get install ffmpeg   # or your platform's equivalent
cp .env.example .env          # fill in whichever free keys you have
```

See `.env.example` for where to get each key. At minimum, nothing is required —
`GROQ_API_KEY`, `PEXELS_API_KEY`, and `YOUTUBE_API_KEY` noticeably improve
quality (real script/analysis instead of heuristics, real stock footage instead
of placeholders, real trending titles instead of an offline fallback); the
publish keys are only needed once you're ready to actually post.

## Running it

Full loop, starting from trend research:

```bash
python -m apex_orchestrator.cli \
  --niche "budget travel" \
  --product "MyTravelApp" \
  --cta "Follow for part 2" \
  --platforms youtube_shorts,tiktok
```

Or skip Radar/Analyst/Strategist with a hand-built brief:

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
  contracts.py             # data contracts for all 8 pipeline stages
  config.py                 # env-driven config, reports which integrations are active
  events.py                  # event bus: rich terminal live view + JSONL log
  llm.py                      # Groq wrapper, raises LLMUnavailable if unconfigured
  pipeline.py                  # top-level orchestrator: run_pipeline() / run_full_pipeline()
  cli.py                        # entrypoint
  dashboard.py                   # FastAPI live dashboard
  viral_radar/                    # Google Trends + YouTube trending signals
  viral_analyst/                   # trend-title analysis -> hook/framework/CTA takeaways
  content_strategist/               # framework selection -> ContentBrief
  ugc_creator/                       # script, voiceover, broll, captions, ffmpeg assembly
  quality_control/                    # hook score, brand safety, disclosure, copyright
  publish/                             # youtube / tiktok / instagram clients
tests/                                  # offline-testable logic (no network/ffmpeg/keys needed)
```

## Notes on the publish stage

- **YouTube**: uses OAuth (installed-app flow); the first run opens a browser for
  one-time consent, then caches a refresh token. Its read-only trending lookup
  in Viral Radar uses a separate, simpler `YOUTUBE_API_KEY` (no OAuth).
- **TikTok**: unaudited developer apps publish to the account's private drafts
  only (`privacy_level: SELF_ONLY` in `publish/tiktok.py`) — flip it once your app
  passes TikTok's review.
- **Instagram**: the Graph API fetches video from a public URL rather than
  accepting a direct upload, so `IG_PUBLIC_VIDEO_BASE_URL` must point somewhere
  the rendered `.mp4` is already reachable.

## Not yet built

`Performance Engine` and `Learning Database` (downstream of Publish, feeding
back into the next Viral Radar pass) are only sketched as a `PerformanceSnapshot`
data contract in `contracts.py`. The natural next step is a poller that pulls
each platform's analytics API on a schedule, and a small store that lets
Content Strategist weight framework choices by what actually performed.

Viral Analyst AI currently reasons over trending *titles*, not full video
content — a deeper version could download and watch top-performing videos
(e.g. with `yt-dlp` + Whisper, similar to this environment's `watch` skill) for
real hook/pacing/editing breakdowns instead of title-pattern inference.
