// Fallback heuristics used when Puter.js is unavailable, blocked, or the
// viewer declines the auth popup — keeps the pipeline runnable with zero
// external dependencies, same role as apex/stages/viral_analyst.py's mock path.

const HOOKS = [
  'POV: you just found out...',
  'Nobody is talking about this, but...',
  'I tried this for 30 days and...',
  'Stop doing X, do this instead',
];
const PATTERNS = ['3-act reveal', 'listicle countdown', 'problem-agitate-solve', 'before/after'];
const STORY_STRUCTURES = ['cold open + payoff', 'relatable setup + twist', 'tutorial + result'];
const EDITING_NOTES = [
  'fast cuts every 1-2s, captions burned in, jump cuts on filler words',
  'single continuous take, subtle zoom for emphasis',
  'text overlays synced to voiceover beats',
];
const CTAS = ['follow for part 2', 'comment your result', 'link in bio', 'save this for later'];
const COMMENT_THEMES = [
  ['asking for source', 'tagging friends', 'disagreement in replies'],
  ['asking for a tutorial', 'sharing their own results', 'requesting a discount code'],
  ['relating personal story', 'asking follow-up questions'],
];

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

export function mockAnalyze(signal) {
  const viralityScore = Math.min(100, (signal.velocity / 50_000) * 100);
  return {
    hook: pick(HOOKS),
    pattern: pick(PATTERNS),
    storyStructure: pick(STORY_STRUCTURES),
    editingNotes: pick(EDITING_NOTES),
    cta: pick(CTAS),
    topCommentsThemes: pick(COMMENT_THEMES),
    viralityScore: Math.round(viralityScore * 10) / 10,
  };
}

export function mockScript(strategy) {
  const a = strategy.analysis;
  return (
    `[HOOK] ${a.hook}\n` +
    `[SETUP - ${strategy.framework}] ${strategy.productAngle}\n` +
    `[STORY - ${a.storyStructure}] Walk through the pain point, then the moment it clicked.\n` +
    `[EDITING] ${a.editingNotes}\n` +
    `[CTA] ${a.cta}`
  );
}
