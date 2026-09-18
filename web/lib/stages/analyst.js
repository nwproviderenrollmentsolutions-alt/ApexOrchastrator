// VIRAL ANALYST AI: breaks a trending post into hook / pattern / story / editing / CTA / comments.
// Uses Groq (free tier, see SETUP.md) when GROQ_API_KEY is set; falls back
// to deterministic mock heuristics on any LLM error or when unconfigured.

import * as groq from '../groq.js';
import { mockAnalyze } from '../mockAnalyst.js';

const SYSTEM_PROMPT =
  'You are a short-form video virality analyst. Given a trending post\'s metadata, ' +
  'break down why it works. Reply with ONLY a JSON object with keys: ' +
  "hook (string), pattern (string, e.g. '3-act reveal'), story_structure (string), " +
  'editing_notes (string), cta (string), top_comments_themes (array of 2-4 short strings), ' +
  'virality_score (number 0-100). No prose, no markdown fencing.';

export async function analyzeSignal(signal) {
  if (!groq.isConfigured()) return mockAnalyze(signal);

  const userPrompt = `Platform: ${signal.platform}
Topic: ${signal.topic}
Views: ${signal.viewCount}
Velocity (views/hour): ${Math.round(signal.velocity)}
Audio/sound: ${signal.audioOrSound}`;

  try {
    const data = await groq.completeJson(SYSTEM_PROMPT, userPrompt);
    return {
      hook: String(data.hook),
      pattern: String(data.pattern),
      storyStructure: String(data.story_structure),
      editingNotes: String(data.editing_notes),
      cta: String(data.cta),
      topCommentsThemes: Array.isArray(data.top_comments_themes) ? data.top_comments_themes.map(String) : [],
      viralityScore: Number(data.virality_score) || 50,
    };
  } catch (err) {
    console.warn(`[ViralAnalyst] Groq analysis failed, falling back to mock: ${err.message}`);
    return mockAnalyze(signal);
  }
}
