// Client for the self-hosted render service (render/app.py) that turns an
// approved script into a talking-head video in your cloned voice/face. See
// render/README.md for setup. Runs on your own GPU machine -- possibly a
// different machine than this dashboard, hence RENDER_SERVICE_URL rather
// than a local import.

import { settings } from './config.js';

export class RenderServiceError extends Error {}

export function isConfigured() {
  return Boolean(settings.renderServiceUrl);
}

export async function renderVideo({ script, title }) {
  if (!settings.renderServiceUrl) {
    throw new RenderServiceError('RENDER_SERVICE_URL is not set (see render/README.md)');
  }

  let response;
  try {
    response = await fetch(`${settings.renderServiceUrl.replace(/\/$/, '')}/render`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ script, title }),
      signal: AbortSignal.timeout(1_800_000), // real SadTalker renders can take minutes
    });
  } catch (err) {
    throw new RenderServiceError(`Render service unreachable: ${err.message}`);
  }

  if (!response.ok) {
    const detail = (await response.text()).slice(0, 300);
    throw new RenderServiceError(`Render service returned ${response.status}: ${detail}`);
  }

  return response.json(); // { videoPath, mock, tookSeconds }
}
