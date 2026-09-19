// VIRAL RADAR: scans TikTok / YouTube Shorts / Instagram for rising content.
//
// YouTube Shorts are pulled live from the free YouTube Data API v3 when
// YOUTUBE_API_KEY is set. TikTok and Instagram have no equivalent free
// public trend API, so those two stay simulated regardless.

import * as youtube from '../youtube.js';

const TOPICS = [
  'morning routine hack',
  'budgeting app walkthrough',
  'AI coding tip',
  'side hustle breakdown',
  'productivity myth debunked',
  'before/after transformation',
  'day in the life',
  'unpopular opinion take',
];

const SOUNDS = ['trending-audio-1', 'trending-audio-2', 'original-sound', 'voiceover-only'];
const MOCK_PLATFORMS = ['tiktok', 'instagram_reels'];

function randInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

export class ViralRadar {
  constructor() {
    this.boostedTopics = [];
  }

  boost(topic) {
    this.boostedTopics.push(topic);
  }

  async scan(limit = 5) {
    let signals = [];

    if (youtube.isConfigured()) {
      try {
        signals = signals.concat(await this.scanYoutubeLive(limit));
      } catch (err) {
        console.warn(`[ViralRadar] YouTube live scan failed, falling back to mock: ${err.message}`);
      }
    }

    const remaining = limit - signals.length;
    if (remaining > 0) {
      signals = signals.concat(this.scanMock(remaining));
    }

    return signals.sort((a, b) => b.velocity - a.velocity).slice(0, limit);
  }

  async scanYoutubeLive(limit) {
    // Always search a topic from our own pool -- never a bare "#shorts",
    // which pulls whatever's globally trending (pranks, sibling content,
    // anything) regardless of relevance to what we're actually promoting.
    const pool = [...this.boostedTopics, ...TOPICS];
    const query = pick(pool);
    const items = await youtube.fetchTrendingShorts({ maxResults: limit, query });
    const now = Date.now();

    return items.map((item) => {
      const snippet = item.snippet || {};
      const stats = item.statistics || {};
      const viewCount = Number(stats.viewCount || 0);
      let hoursLive = 1;
      if (snippet.publishedAt) {
        hoursLive = Math.max(1, (now - new Date(snippet.publishedAt).getTime()) / 3_600_000);
      }
      return {
        id: `yt-${item.id || randInt(1e6, 1e7)}`,
        platform: 'youtube_shorts',
        sourceUrl: `https://youtube.com/shorts/${item.id || ''}`,
        topic: (snippet.title || query).slice(0, 80),
        audioOrSound: 'original-sound',
        viewCount,
        velocity: viewCount / hoursLive,
        detectedAt: new Date().toISOString(),
      };
    });
  }

  scanMock(limit) {
    const topics = [...TOPICS, ...this.boostedTopics, ...this.boostedTopics, ...this.boostedTopics];
    const signals = [];
    for (let i = 0; i < limit; i++) {
      const platform = pick(MOCK_PLATFORMS);
      const views = randInt(50_000, 5_000_000);
      signals.push({
        id: `mock-${Date.now()}-${i}`,
        platform,
        sourceUrl: `https://${platform}.example/post/${randInt(1e6, 1e7)}`,
        topic: pick(topics),
        audioOrSound: pick(SOUNDS),
        viewCount: views,
        velocity: views / randInt(1, 48),
        detectedAt: new Date().toISOString(),
      });
    }
    return signals;
  }
}
