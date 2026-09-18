// CONTENT STRATEGIST: picks a content framework and a brand/product angle.
// Deterministic/rule-based — no LLM needed for this step.
//
// Carries `signal` and `analysis` forward on the returned strategy (mirroring
// the nested-dataclass chain in the Python pipeline) so later stages can
// still see the original trend data without re-fetching it.

const FRAMEWORKS = [
  'problem-agitate-solve',
  'listicle',
  'before/after case study',
  'myth vs reality',
  'day-in-the-life demo',
];

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

export function chooseStrategy(signal, analysis, productContext = 'our product') {
  const framework = pick(FRAMEWORKS);
  return {
    signal,
    analysis,
    framework,
    productAngle: `${productContext} solves the pain point behind '${signal.topic}'`,
    targetPlatform: signal.platform,
    workingTitle: `${analysis.hook} (${signal.topic})`,
  };
}
