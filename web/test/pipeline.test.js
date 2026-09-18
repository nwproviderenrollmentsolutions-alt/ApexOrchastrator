import { test } from 'node:test';
import assert from 'node:assert/strict';

import { ViralRadar } from '../lib/stages/radar.js';
import { chooseStrategy } from '../lib/stages/strategist.js';
import { buildPackage } from '../lib/stages/packageBuilder.js';
import { reviewPackage } from '../lib/stages/qc.js';
import { publish } from '../lib/stages/publisher.js';
import { measure, engagementRate } from '../lib/stages/performance.js';
import { LearningDatabase } from '../lib/stages/learning.js';
import { mockAnalyze, mockScript } from '../lib/mockAnalyst.js';

test('radar mock scan returns requested signal count', async () => {
  const radar = new ViralRadar();
  const signals = await radar.scan(3);
  assert.equal(signals.length, 3);
  for (const s of signals) {
    assert.ok(['tiktok', 'youtube_shorts', 'instagram_reels'].includes(s.platform));
  }
});

test('radar boost tracks topics for future scans', async () => {
  const radar = new ViralRadar();
  radar.boost('my favorite topic');
  assert.deepEqual(radar.boostedTopics, ['my favorite topic']);
});

test('full stage chain produces an approvable-or-rejectable QC result', async () => {
  const radar = new ViralRadar();
  const [signal] = await radar.scan(1);
  const analysis = mockAnalyze(signal);
  const strategy = chooseStrategy(signal, analysis, 'Replit');
  const script = mockScript(strategy);
  const pkg = buildPackage(strategy, script);
  const qcResult = reviewPackage(pkg);

  assert.equal(qcResult.package, pkg);
  assert.ok(qcResult.hookScore >= 0 && qcResult.hookScore <= 100);
  assert.equal(typeof qcResult.approved, 'boolean');
  assert.ok(pkg.captions.includes('#ad'));
});

test('publisher refuses an unapproved package', async () => {
  const radar = new ViralRadar();
  const [signal] = await radar.scan(1);
  const analysis = mockAnalyze(signal);
  const strategy = chooseStrategy(signal, analysis, 'Replit');
  const pkg = buildPackage(strategy, mockScript(strategy));
  const qcResult = reviewPackage(pkg);
  qcResult.approved = false;

  assert.throws(() => publish(qcResult), /Quality Control/);
});

test('publisher fans out to tiktok + youtube_shorts + target platform', async () => {
  const radar = new ViralRadar();
  const [signal] = await radar.scan(1);
  const analysis = mockAnalyze(signal);
  const strategy = chooseStrategy(signal, analysis, 'Replit');
  const pkg = buildPackage(strategy, mockScript(strategy));
  const qcResult = reviewPackage(pkg);
  qcResult.approved = true;
  qcResult.hookScore = 90;

  const results = publish(qcResult);
  const platforms = new Set(results.map((r) => r.platform));
  assert.ok(platforms.has('tiktok'));
  assert.ok(platforms.has('youtube_shorts'));
});

test('learning database flags worked vs underperformed and feeds engagementRate', async () => {
  const radar = new ViralRadar();
  const [signal] = await radar.scan(1);
  const analysis = mockAnalyze(signal);
  const strategy = chooseStrategy(signal, analysis, 'Replit');
  const pkg = buildPackage(strategy, mockScript(strategy));
  const qcResult = reviewPackage(pkg);
  qcResult.approved = true;
  qcResult.hookScore = 90;

  const learningDb = new LearningDatabase();
  const [publishResult] = publish(qcResult, ['tiktok']);
  const metrics = measure(publishResult);
  const record = learningDb.record(metrics);

  assert.equal(typeof record.worked, 'boolean');
  assert.equal(record.worked, engagementRate(metrics) >= 0.03);
  assert.equal(learningDb.records.length, 1);
});
