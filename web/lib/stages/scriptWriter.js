// UGC CREATOR AI's script-writing half. Uses Groq (free tier, see SETUP.md)
// when GROQ_API_KEY is set; falls back to a templated script on any LLM
// error or when unconfigured.

import * as groq from '../groq.js';
import { mockScript } from '../mockAnalyst.js';

const SYSTEM_PROMPT =
  'You write short, punchy UGC-style scripts for TikTok/Shorts/Reels (30-45 seconds spoken). ' +
  'Structure the script with these labeled beats on separate lines: [HOOK], [SETUP], [STORY], ' +
  '[EDITING] (camera/editing direction, not spoken), [CTA]. Keep spoken lines conversational, ' +
  'first-person, no hashtags. Reply with ONLY the script text, no extra commentary.';

export async function writeScript(strategy) {
  if (!groq.isConfigured()) return mockScript(strategy);

  const a = strategy.analysis;
  const userPrompt = `Framework: ${strategy.framework}
Working title: ${strategy.workingTitle}
Hook to riff on: ${a.hook}
Story structure: ${a.storyStructure}
Product/angle to weave in: ${strategy.productAngle}
Editing notes to include: ${a.editingNotes}
CTA: ${a.cta}`;

  try {
    return await groq.complete(SYSTEM_PROMPT, userPrompt);
  } catch (err) {
    console.warn(`[UGCCreator] Groq script generation failed, falling back to template: ${err.message}`);
    return mockScript(strategy);
  }
}
