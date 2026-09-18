// Loads settings from a `.env` file (if present) and the environment.
// No dependency needed: Node has global `fetch`; this is the only other
// piece an npm install would otherwise be for.

import { readFileSync, existsSync } from 'node:fs';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const envPath = path.join(__dirname, '..', '.env');

function loadDotenv(filePath) {
  if (!existsSync(filePath)) return;
  const lines = readFileSync(filePath, 'utf8').split('\n');
  for (const rawLine of lines) {
    const line = rawLine.trim();
    if (!line || line.startsWith('#') || !line.includes('=')) continue;
    const idx = line.indexOf('=');
    const key = line.slice(0, idx).trim();
    let value = line.slice(idx + 1).trim();
    value = value.replace(/^['"]|['"]$/g, '');
    if (key && !(key in process.env)) process.env[key] = value;
  }
}

loadDotenv(envPath);

export const settings = {
  youtubeApiKey: process.env.YOUTUBE_API_KEY || null,
  youtubeRegion: process.env.YOUTUBE_REGION || 'US',
  groqApiKey: process.env.GROQ_API_KEY || null,
  groqModel: process.env.GROQ_MODEL || 'llama-3.1-8b-instant',
  port: Number(process.env.PORT) || 3000,
};
