// Assembles the final UGC package from a strategy + a script (the script's
// text comes from Puter.js in the browser, or a template fallback there).
// Captions stay template-based here so the `#ad` disclosure tag Quality
// Control checks for is always present.

const AVATARS = ['ai-avatar-jordan', 'ai-avatar-mia', 'voiceover-only-female', 'voiceover-only-male'];

function pick(arr) {
  return arr[Math.floor(Math.random() * arr.length)];
}

export function buildPackage(strategy, script) {
  const captions = `${strategy.workingTitle}\n\n${strategy.analysis.cta} \u{1F447}\n\n#ad`;
  return {
    strategy,
    script,
    avatarOrVoice: pick(AVATARS),
    bRollPlan: [
      'screen recording of product in use',
      'close-up reaction shot',
      'text-on-screen stat callout',
    ],
    captions,
  };
}
