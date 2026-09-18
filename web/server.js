import express from 'express';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

import { settings } from './lib/config.js';
import { ViralRadar } from './lib/stages/radar.js';
import { chooseStrategy } from './lib/stages/strategist.js';
import { buildPackage } from './lib/stages/packageBuilder.js';
import { reviewPackage } from './lib/stages/qc.js';
import { publish } from './lib/stages/publisher.js';
import { measure, engagementRate } from './lib/stages/performance.js';
import { LearningDatabase } from './lib/stages/learning.js';
import * as youtube from './lib/youtube.js';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

const app = express();
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));

// Single shared pipeline state for this server process (in-memory, resets on restart).
const radar = new ViralRadar();
const learningDb = new LearningDatabase();

app.get('/api/config', (req, res) => {
  res.json({ youtubeLive: youtube.isConfigured() });
});

app.post('/api/scan', async (req, res) => {
  const limit = Math.max(1, Math.min(10, Number(req.body?.limit) || 5));
  try {
    const signals = await radar.scan(limit);
    res.json({ signals });
  } catch (err) {
    res.status(500).json({ error: err.message });
  }
});

app.post('/api/strategize', (req, res) => {
  const { signal, analysis, productContext } = req.body || {};
  if (!signal || !analysis) return res.status(400).json({ error: 'signal and analysis are required' });
  res.json({ strategy: chooseStrategy(signal, analysis, productContext) });
});

app.post('/api/package', (req, res) => {
  const { strategy, script } = req.body || {};
  if (!strategy || !script) return res.status(400).json({ error: 'strategy and script are required' });
  res.json({ package: buildPackage(strategy, script) });
});

app.post('/api/qc', (req, res) => {
  const { package: pkg } = req.body || {};
  if (!pkg) return res.status(400).json({ error: 'package is required' });
  res.json(reviewPackage(pkg));
});

app.post('/api/publish', (req, res) => {
  const { qcResult, platforms } = req.body || {};
  if (!qcResult) return res.status(400).json({ error: 'qcResult is required' });
  try {
    res.json({ publishResults: publish(qcResult, platforms) });
  } catch (err) {
    res.status(422).json({ error: err.message });
  }
});

app.post('/api/performance', (req, res) => {
  const { publishResult } = req.body || {};
  if (!publishResult) return res.status(400).json({ error: 'publishResult is required' });
  const metrics = measure(publishResult);
  res.json({ metrics, engagementRate: engagementRate(metrics) });
});

app.post('/api/learn', (req, res) => {
  const { metrics } = req.body || {};
  if (!metrics) return res.status(400).json({ error: 'metrics is required' });
  const record = learningDb.record(metrics);
  if (record.worked) radar.boost(record.topic);
  res.json({ record, boostedTopics: radar.boostedTopics, winningTopics: learningDb.winningTopics() });
});

app.get('/api/state', (req, res) => {
  res.json({
    boostedTopics: radar.boostedTopics,
    winningTopics: learningDb.winningTopics(),
    recordCount: learningDb.records.length,
    records: learningDb.records.slice(-50),
  });
});

app.listen(settings.port, () => {
  console.log(`ApexOrchastrator dashboard running at http://localhost:${settings.port}`);
  console.log(`YouTube live trends: ${youtube.isConfigured() ? 'ON' : 'off (set YOUTUBE_API_KEY in web/.env)'}`);
});
