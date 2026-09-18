# Getting set up

There are two runnable surfaces in this repo:

- **`web/`** — a Node/Express dashboard. AI (analysis + script writing) runs
  via **Puter.js in the browser — no API key at all**, just a free Puter.com
  account (created automatically on first use). This is the one to run if
  you want a live, clickable project today.
- **root (`main.py`)** — the original Python CLI, using Groq for AI.

Both share the same free YouTube Data API key for real trend data.

## 1. Run the web dashboard (no keys required)

```bash
cd web
npm install
npm start
```

Open http://localhost:3000, click **Run cycle**. The first AI call pops up a
Puter.com login/signup (free, no credit card) — after that it just works.
Everything else (radar, strategy, QC, publish, performance, learning loop)
runs on the local server with zero setup.

If Puter.js is blocked, offline, or the viewer declines the popup, that
stage falls back to a local mocked analysis/script automatically — the
dashboard never breaks, it just stops being "live" for that step.

## 2. (Optional) Add real YouTube Shorts trend data

Free tier, no credit card required for the free quota. Powers the Viral
Radar in **both** the web dashboard and the Python CLI.

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

Wire it in:

```bash
cd web
cp .env.example .env
# edit .env, paste in YOUTUBE_API_KEY
npm start
```

`.env` is gitignored — your key never gets committed.

## 3. (Optional) Run the original Python CLI instead

Uses Groq (free tier) for AI instead of Puter.js, and the same YouTube key.

1. Go to https://console.groq.com/keys, sign in, click **Create API Key**
   (starts with `gsk_...`). Free tier, no credit card.
2. From the repo root:
   ```bash
   cp .env.example .env
   # edit .env, paste in GROQ_API_KEY and/or YOUTUBE_API_KEY
   python3 main.py --cycles 1 --signals-per-scan 5 --product "your product"
   ```

If a live call fails (rate limit, bad key, network), it logs a warning to
stderr/console and falls back to mocked data for that item — a bad key
never crashes a run, in either surface.
