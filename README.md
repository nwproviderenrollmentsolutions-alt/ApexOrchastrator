# ApexOrchastrator

[![tests](https://github.com/nwproviderenrollmentsolutions-alt/ApexOrchastrator/actions/workflows/tests.yml/badge.svg)](https://github.com/nwproviderenrollmentsolutions-alt/ApexOrchastrator/actions/workflows/tests.yml)

Faceless short-form content automation, built entirely on free-tier services —
the full loop, all 8 stages:

Viral Radar → Viral Analyst AI → Content Strategist → UGC Creator AI → Quality
Control → Publish → Performance Engine → Learning Database → *(back into the
next Content Strategist run)*

## What it does

Given a niche (e.g. `"budget travel"`):

1. **Viral Radar** — pulls a trend velocity signal from Google Trends (free,
   no key) and, if configured, real trending-video titles from YouTube's free
   public API, for that niche. Given *several* candidate niches instead of
   one, it ranks them by blending fresh trend velocity with the Learning
   Database's historical performance for each, and only the winner proceeds
   — the Learning Database → Viral Radar feedback loop, deciding *what to
   research* rather than just how to frame it (see **Running it**).
2. **Viral Analyst AI** — turns those titles into a concrete take: dominant
   hook pattern, content framework (listicle / myth-vs-fact / tutorial /
   storytime / before-after / problem-agitate-solve), editing notes, CTA
   style, predicted comment themes.
3. **Content Strategist** — picks the framework (deferring to the Learning
   Database's judgment once it has enough history for this niche — see step 8)
   and builds a `ContentBrief` (topic, angle, CTA, claims, target platforms,
   product tie-in).
4. **UGC Creator AI** — writes a script, synthesizes a faceless voiceover,
   sources 9:16 B-roll, builds animated captions, and renders a final MP4.
5. **Quality Control** — scores the hook, scans for brand-unsafe language,
   checks FTC-style disclosure requirements, verifies every clip's license.
   Failing QC blocks Publish.
6. **Publish** — posts to YouTube Shorts, TikTok, and/or Instagram Reels via
   each platform's official free API.
7. **Performance Engine** — *(run separately, later — see below)* pulls real
   views/watch-time/shares/saves/comments from each platform's free analytics
   endpoint for a post that already published.
8. **Learning Database** — records every run and its performance in a local
   SQLite database. It feeds back into the pipeline two ways: once a
   framework has enough data points for a niche, Content Strategist starts
   preferring it over the Analyst's title-pattern guess (step 3); and when
   Viral Radar is given multiple candidate niches, their historical average
   views factor directly into which one gets researched next (step 1).

You can also skip straight to step 4 with a hand-written brief (see
**Running it** below) if you don't want automated trend research.

Every stage reports through a shared event bus, visible live in the terminal and
in a local browser dashboard.

## Why Performance Engine is a separate step

Steps 1–6 run as one pipeline invocation. Step 7 doesn't, on purpose: platform
analytics for a just-published post aren't populated for hours, so collecting
performance is a second command you run later (see **Running it**), not
something bolted onto the end of publish.

## Free services used

| Purpose | Service | Free tier |
|---|---|---|
| Trend velocity | [Google Trends](https://trends.google.com) via `pytrends` | Yes, no key (unofficial, best-effort) |
| Trending video titles | [YouTube Data API v3](https://console.cloud.google.com) (API key, read-only) | Yes, daily quota |
| Script writing + QC/Analyst judgment | [Groq](https://console.groq.com) | Yes (generous free API) |
| Voiceover | [edge-tts](https://github.com/rany2/edge-tts) | Yes, no key needed |
| B-roll | [Pexels API](https://www.pexels.com/api) | Yes |
| Video rendering | ffmpeg | Yes, local binary |
| YouTube Shorts publish + analytics | [YouTube Data/Analytics API v3](https://console.cloud.google.com) (OAuth) | Yes, daily quota |
| TikTok publish + analytics | [Content Posting API](https://developers.tiktok.com) | Yes, developer account |
| Instagram Reels publish + insights | [Graph API](https://developers.facebook.com) | Yes, Business account |
| Learning Database | SQLite (Python stdlib) | Yes, no service at all |

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

Then check your setup before spending any API calls:

```bash
python -m apex_orchestrator.cli --doctor
```

This validates required packages, ffmpeg, and a writable `runs/` directory,
and reports which integrations are configured — all with zero network calls.

## Running it

Full loop, starting from trend research:

```bash
python -m apex_orchestrator.cli \
  --niche "budget travel" \
  --product "MyTravelApp" \
  --cta "Follow for part 2" \
  --platforms youtube_shorts,tiktok
```

Or let Viral Radar pick which of several candidate niches is worth researching,
weighing fresh trend velocity against each niche's track record in the Learning
Database (a niche with no history yet still gets a fair shot — see
`viral_radar/pipeline.py`'s `rank_niches`):

```bash
python -m apex_orchestrator.cli \
  --niches "budget travel,personal finance,productivity hacks" \
  --cta "Follow for part 2" \
  --platforms youtube_shorts,tiktok
```

This prints the full ranking (score, trend velocity, historical views per
candidate) before proceeding with the winner, and records it in that run's
`summary.json`.

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
`events.jsonl` (the full event log), and `summary.json` (niche, framework, QC,
and publish results).

Once a published post has had time to accumulate real analytics (hours/days
later), close the loop:

```bash
python -m apex_orchestrator.cli --collect-performance <run_id>
```

This runs Performance Engine (pulls views/shares/saves/comments from whichever
platforms actually published) and Learning Database (records the run +
performance to `runs/learning.db`). Run this after enough `--niche` runs in the
same niche, and Content Strategist starts choosing the framework the data
actually supports instead of the Analyst's title-pattern guess.

### Watching it run

- **Terminal**: a live `rich` table updates in place as each stage runs — no setup.
- **Browser**: `python -m apex_orchestrator.dashboard`, then open
  `http://127.0.0.1:8765` and pick a run from the dropdown. It polls the same
  event log, so it works for runs in progress or already finished, and a later
  `--collect-performance` run for the same run_id appends to the same log.

## Project layout

```
apex_orchestrator/
  contracts.py             # data contracts for all 8 pipeline stages
  config.py                 # env-driven config, reports which integrations are active
  events.py                  # event bus: rich terminal live view + JSONL log
  llm.py                      # Groq wrapper, raises LLMUnavailable if unconfigured
  google_auth.py               # shared YouTube OAuth (upload + analytics scopes)
  pipeline.py                   # top-level orchestrator: run_pipeline() / run_full_pipeline() / collect_performance_for_run()
  cli.py                         # entrypoint
  doctor.py                       # `--doctor`: local setup validation, zero network calls
  dashboard.py                     # FastAPI live dashboard
  viral_radar/                      # Google Trends + YouTube trending signals
  viral_analyst/                     # trend-title analysis -> hook/framework/CTA takeaways
  content_strategist/                 # framework selection (Analyst take, or Learning DB override) -> ContentBrief
  ugc_creator/                         # script, voiceover, broll, captions, ffmpeg assembly
  quality_control/                      # hook score, brand safety, disclosure, copyright
  publish/                               # youtube / tiktok / instagram clients
  performance_engine/                     # youtube / tiktok / instagram analytics fetchers
  learning_database/                       # SQLite store + framework leaderboard
tests/                                      # all offline: mocked HTTP, no real network/ffmpeg/keys needed
.github/workflows/tests.yml                  # CI: runs the full test suite on every push/PR
```

## Notes on the publish stage

- **YouTube**: uses OAuth (installed-app flow, scopes cover both upload and
  read-only analytics); the first run opens a browser for one-time consent,
  then caches a refresh token. Viral Radar's trending-video lookup uses a
  separate, simpler `YOUTUBE_API_KEY` (no OAuth).
- **TikTok**: unaudited developer apps publish to the account's private drafts
  only (`privacy_level: SELF_ONLY` in `publish/tiktok.py`) — flip it once your app
  passes TikTok's review. Performance Engine's `video/query/` call targets the
  documented v2 shape as of writing; TikTok's API has shifted before, so verify
  against current docs if it starts failing.
- **Instagram**: the Graph API fetches video from a public URL rather than
  accepting a direct upload, so `IG_PUBLIC_VIDEO_BASE_URL` must point somewhere
  the rendered `.mp4` is already reachable.

## Not yet built

Viral Analyst AI currently reasons over trending *titles*, not full video
content — a deeper version could download and watch top-performing videos
(e.g. with `yt-dlp` + Whisper, similar to this environment's `watch` skill) for
real hook/pacing/editing breakdowns instead of title-pattern inference.

Niche ranking (`rank_niches`) only uses raw average views as the historical
signal. It doesn't yet weight by recency (a niche that performed well two
months ago is treated the same as one that performed well yesterday) or by
sample size beyond the framework leaderboard's own `min_samples` gate --
both are natural next refinements once there's enough real run history to
make them meaningful.
