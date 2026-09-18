// QUALITY CONTROL: gates a package before it's allowed to publish.
// Checks hook strength, brand safety, disclosure, and copyright risk.

const BANNED_TERMS = ['guaranteed', 'cure', 'get rich quick'];

export function reviewPackage(pkg) {
  const hookScore = scoreHook(pkg);
  const brandSafetyPass = checkBrandSafety(pkg);
  const disclosurePass = pkg.captions.toLowerCase().includes('#ad');
  const copyrightPass = pkg.strategy.signal.audioOrSound !== 'unlicensed-track';
  const approved = brandSafetyPass && disclosurePass && copyrightPass && hookScore >= 60;

  return { package: pkg, hookScore, brandSafetyPass, disclosurePass, copyrightPass, approved };
}

function scoreHook(pkg) {
  const base = pkg.strategy.analysis.viralityScore ?? 50;
  const jitter = Math.random() * 20 - 10;
  return Math.round(Math.max(0, Math.min(100, base + jitter)) * 10) / 10;
}

function checkBrandSafety(pkg) {
  const text = `${pkg.script} ${pkg.captions}`.toLowerCase();
  return !BANNED_TERMS.some((term) => text.includes(term));
}
