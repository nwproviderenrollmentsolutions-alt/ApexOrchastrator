// Thin client for the free-tier YouTube Data API v3.
// Get a free key at https://console.cloud.google.com/apis/credentials
// (enable "YouTube Data API v3" first) and put it in web/.env as
// YOUTUBE_API_KEY=... See SETUP.md.
//
// Free quota is 10,000 units/day; one scan here costs ~101 units
// (1 search.list @ 100 + 1 videos.list @ 1).

import { settings } from './config.js';

const SEARCH_URL = 'https://www.googleapis.com/youtube/v3/search';
const VIDEOS_URL = 'https://www.googleapis.com/youtube/v3/videos';

export class YouTubeError extends Error {}

export function isConfigured() {
  return Boolean(settings.youtubeApiKey);
}

async function get(url, params) {
  const query = new URLSearchParams({ ...params, key: settings.youtubeApiKey });
  const response = await fetch(`${url}?${query}`);
  if (!response.ok) {
    const detail = (await response.text()).slice(0, 300);
    throw new YouTubeError(`YouTube API returned ${response.status}: ${detail}`);
  }
  return response.json();
}

export async function fetchTrendingShorts({ maxResults = 10, query = '#shorts' } = {}) {
  if (!settings.youtubeApiKey) throw new YouTubeError('YOUTUBE_API_KEY is not set');

  const searchPayload = await get(SEARCH_URL, {
    part: 'snippet',
    q: query,
    type: 'video',
    order: 'viewCount',
    videoDuration: 'short',
    regionCode: settings.youtubeRegion,
    maxResults: String(maxResults),
  });

  const videoIds = (searchPayload.items || [])
    .map((item) => item.id && item.id.videoId)
    .filter(Boolean);
  if (videoIds.length === 0) return [];

  const statsPayload = await get(VIDEOS_URL, { part: 'snippet,statistics', id: videoIds.join(',') });
  return statsPayload.items || [];
}
