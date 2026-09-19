import { test } from 'node:test';
import assert from 'node:assert/strict';

import { settings } from '../lib/config.js';
import * as renderService from '../lib/renderService.js';

function withRenderUrl(url, fn) {
  const original = settings.renderServiceUrl;
  settings.renderServiceUrl = url;
  return fn().finally(() => {
    settings.renderServiceUrl = original;
  });
}

test('renderService.isConfigured reflects settings.renderServiceUrl', async () => {
  await withRenderUrl(null, async () => assert.equal(renderService.isConfigured(), false));
  await withRenderUrl('http://localhost:8000', async () => assert.equal(renderService.isConfigured(), true));
});

test('renderVideo throws RenderServiceError without a URL configured', async () => {
  await withRenderUrl(null, async () => {
    await assert.rejects(() => renderService.renderVideo({ script: 'hi' }), renderService.RenderServiceError);
  });
});

test('renderVideo throws RenderServiceError when the service is unreachable', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => {
    throw new Error('ECONNREFUSED');
  };
  try {
    await withRenderUrl('http://localhost:9999', async () => {
      await assert.rejects(() => renderService.renderVideo({ script: 'hi' }), renderService.RenderServiceError);
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('renderVideo parses a successful response', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = async () => ({
    ok: true,
    json: async () => ({ videoPath: '/tmp/out.mp4', mock: true, tookSeconds: 0.01 }),
  });
  try {
    await withRenderUrl('http://localhost:8000', async () => {
      const result = await renderService.renderVideo({ script: 'hi', title: 't' });
      assert.equal(result.videoPath, '/tmp/out.mp4');
      assert.equal(result.mock, true);
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
});
