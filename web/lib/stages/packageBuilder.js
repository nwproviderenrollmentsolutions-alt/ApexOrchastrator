// Assembles the final UGC package from a strategy + a script. Captions stay
// template-based here so the `#ad` disclosure tag Quality Control checks
// for is always present.
//
// Avatar/voice is always your own cloned avatar (rendered by render/app.py,
// see render/README.md) -- no random avatar picker here.

export function buildPackage(strategy, script) {
  const captions = `${strategy.workingTitle}\n\n${strategy.analysis.cta} \u{1F447}\n\n#ad`;
  return {
    strategy,
    script,
    avatarOrVoice: 'cloned-avatar',
    bRollPlan: [
      'screen recording of product in use',
      'close-up reaction shot',
      'text-on-screen stat callout',
    ],
    captions,
  };
}
