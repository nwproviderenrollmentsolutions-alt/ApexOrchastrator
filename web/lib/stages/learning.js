// LEARNING DATABASE: stores every cycle's outcome and feeds winners back to
// the Viral Radar. In-memory for now — swap for a real DB (Postgres/Supabase)
// once this needs to persist across server restarts.

import { engagementRate } from './performance.js';

const WORKED_ENGAGEMENT_THRESHOLD = 0.03;

export class LearningDatabase {
  constructor() {
    this.records = [];
  }

  record(metrics) {
    const rate = engagementRate(metrics);
    const worked = rate >= WORKED_ENGAGEMENT_THRESHOLD;
    const topic = metrics.publishResult.qcResult.package.strategy.signal.topic;
    const platform = metrics.publishResult.platform;
    const notes = `topic='${topic}' platform=${platform} engagement_rate=${rate.toFixed(4)} retention=${metrics.retentionPct}% -> ${worked ? 'worked' : 'underperformed'}`;

    const rec = { metrics, worked, notes, topic, platform, recordedAt: new Date().toISOString() };
    this.records.push(rec);
    return rec;
  }

  winningTopics() {
    return this.records.filter((r) => r.worked).map((r) => r.topic);
  }
}
