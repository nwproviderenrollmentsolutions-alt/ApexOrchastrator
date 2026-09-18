import { test } from 'node:test';
import assert from 'node:assert/strict';

import { settings } from '../lib/config.js';
import * as groq from '../lib/groq.js';
import { analyzeSignal } from '../lib/stages/analyst.js';
import { writeScript } from '../lib/stages/scriptWriter.js';
import { ViralRadar } from '../lib/stages/radar.js';
import { chooseStrategy } from '../lib/stages/strategist.js';
import { mockAnalyze } from '../lib/mockAnalyst.js';

function withGroqKey(key, fn) {
  const original = settings.groqApiKey;
  settings.groqApiKey = key;
  return fn().finally(() => {
    settings.groqApiKey = original;
  });
}

function fakeFetch(body, ok = true, status = 200) {
  return async () => ({
    ok,
    status,
    json: async () => body,
    text: async () => JSON.stringify(body),
  });
}

test('groq.isConfigured reflects settings.groqApiKey', async () => {
  await withGroqKey(null, async () => assert.equal(groq.isConfigured(), false));
  await withGroqKey('fake-key', async () => assert.equal(groq.isConfigured(), true));
});

test('groq.complete throws LLMError without a key', async () => {
  await withGroqKey(null, async () => {
    await assert.rejects(() => groq.complete('sys', 'user'), groq.LLMError);
  });
});

test('groq.complete parses the chat completion response', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = fakeFetch({ choices: [{ message: { content: 'hello world' } }] });
  try {
    await withGroqKey('fake-key', async () => {
      const text = await groq.complete('sys', 'user');
      assert.equal(text, 'hello world');
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('groq.completeJson strips markdown fencing', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = fakeFetch({ choices: [{ message: { content: '```json\n{"a":1}\n```' } }] });
  try {
    await withGroqKey('fake-key', async () => {
      const data = await groq.completeJson('sys', 'user');
      assert.deepEqual(data, { a: 1 });
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('analyzeSignal falls back to mock when Groq is configured but fails', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = fakeFetch({ error: 'boom' }, false, 500);
  try {
    await withGroqKey('fake-key', async () => {
      const radar = new ViralRadar();
      const [signal] = await radar.scan(1);
      const analysis = await analyzeSignal(signal);
      assert.ok(analysis.hook);
      assert.equal(typeof analysis.viralityScore, 'number');
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
});

test('writeScript falls back to template when Groq is configured but fails', async () => {
  const originalFetch = globalThis.fetch;
  globalThis.fetch = fakeFetch({ error: 'boom' }, false, 500);
  try {
    await withGroqKey('fake-key', async () => {
      const radar = new ViralRadar();
      const [signal] = await radar.scan(1);
      const analysis = mockAnalyze(signal);
      const strategy = chooseStrategy(signal, analysis, 'Replit');
      const script = await writeScript(strategy);
      assert.ok(script.includes('[HOOK]'));
    });
  } finally {
    globalThis.fetch = originalFetch;
  }
});
