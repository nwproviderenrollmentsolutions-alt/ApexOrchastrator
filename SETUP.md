# Getting free API keys

The pipeline runs fully mocked with zero keys. Add either key below and that
stage switches to live data automatically — no code changes needed. If a live
call fails (rate limit, bad key, network), it logs a warning to stderr and
falls back to mocked data for that item, so a bad key never crashes a run.

## 1. Groq (LLM — powers Viral Analyst + UGC Creator script writing)

Free tier, no credit card required.

1. Go to https://console.groq.com/keys
2. Sign in (Google/GitHub/email) and click **Create API Key**
3. Copy the key (starts with `gsk_...`)

**Free tier limits** (subject to change, check https://console.groq.com/settings/limits
after signing in): generous per-minute/per-day request and token caps on
models like `llama-3.1-8b-instant`. If you hit a rate limit mid-run, the
pipeline just falls back to the mocked analysis/script for that item.

## 2. YouTube Data API v3 (real trending Shorts for Viral Radar)

Free tier, no credit card required for the free quota.

1. Go to https://console.cloud.google.com/apis/library/youtube.googleapis.com
2. Create a project if you don't have one, then click **Enable**
3. Go to https://console.cloud.google.com/apis/credentials
4. Click **Create Credentials → API key**
5. (Recommended) Click **Restrict key** → restrict it to "YouTube Data API v3"
6. Copy the key

**Free tier limits**: 10,000 quota units/day. Each `ViralRadar.scan()` call
costs ~101 units (one `search.list` @ 100 + one `videos.list` @ 1), so you
get ~99 scans/day before hitting the quota. TikTok and Instagram have no
comparable free public trend API, so those two platforms stay mocked
regardless of this key.

## 3. Wire them in

```bash
cp .env.example .env
# then edit .env and paste in GROQ_API_KEY and/or YOUTUBE_API_KEY
```

`.env` is gitignored — your keys never get committed.

## 4. Run it

```bash
python3 main.py --cycles 1 --signals-per-scan 5 --product "your product"
```

Omit `--seed` once you have live keys, since a fixed seed only controls the
mocked RNG paths (QC scoring jitter, avatar pick, mocked platforms, etc.) —
live LLM and YouTube results vary on their own.

Watch stderr for `[ViralRadar] ... falling back to mock` or
`[ViralAnalyst]/[UGCCreator] ... falling back to mock` lines — those tell you
when a live call failed and why (bad key, rate limit, etc.).
