// Publishing fan-out: pushes an approved QC result to TikTok/Reels and
// YouTube Shorts. Simulated — swap for real platform upload APIs (TikTok
// Content Posting API, YouTube Data API) once you have app review access;
// those require OAuth app approval, not just a free API key.

function randInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

export function publish(qcResult, platforms) {
  if (!qcResult.approved) {
    throw new Error('Refusing to publish a package that failed Quality Control');
  }
  const defaultTargets = ['tiktok', 'youtube_shorts', qcResult.package.strategy.targetPlatform];
  const uniqueTargets = [...new Set(platforms && platforms.length ? platforms : defaultTargets)];

  return uniqueTargets.map((platform) => ({
    qcResult,
    platform,
    postUrl: `https://${platform}.example/post/${randInt(1e8, 1e9)}`,
    publishedAt: new Date().toISOString(),
  }));
}
