// PERFORMANCE ENGINE: pulls post-publish metrics.
// Simulated, biased by QC's hook_score — swap for real platform analytics
// APIs (TikTok Business API, YouTube Analytics API, IG Graph API) once you
// have real published posts and the OAuth access to read their stats.

function randInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function randFloat(min, max) {
  return Math.random() * (max - min) + min;
}

export function measure(publishResult) {
  const quality = publishResult.qcResult.hookScore / 100;
  const views = Math.round(randInt(1_000, 200_000) * (0.5 + quality));

  return {
    publishResult,
    views,
    watchTimeSeconds: Math.round(views * randFloat(3, 25) * 10) / 10,
    retentionPct: Math.round(Math.min(100, 30 + quality * 50 + randFloat(-10, 10)) * 10) / 10,
    shares: Math.round(views * randFloat(0.001, 0.02)),
    saves: Math.round(views * randFloat(0.001, 0.03)),
    comments: Math.round(views * randFloat(0.0005, 0.01)),
    clicks: Math.round(views * randFloat(0.001, 0.015)),
  };
}

export function engagementRate(metrics) {
  if (metrics.views === 0) return 0;
  return (metrics.shares + metrics.saves + metrics.comments) / metrics.views;
}
