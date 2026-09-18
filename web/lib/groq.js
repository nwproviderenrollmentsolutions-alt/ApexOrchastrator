// Thin client for Groq's free-tier, OpenAI-compatible chat completions API.
// Get a free key (no credit card required) at https://console.groq.com/keys
// and put it in web/.env as GROQ_API_KEY=... See SETUP.md.
//
// Runs server-side (unlike Puter.js) so a plain fetch + API key is enough —
// no browser auth popup needed.

import { settings } from './config.js';

const GROQ_CHAT_URL = 'https://api.groq.com/openai/v1/chat/completions';

export class LLMError extends Error {}

export function isConfigured() {
  return Boolean(settings.groqApiKey);
}

export async function complete(systemPrompt, userPrompt, { temperature = 0.8, maxTokens = 600 } = {}) {
  if (!settings.groqApiKey) throw new LLMError('GROQ_API_KEY is not set');

  const response = await fetch(GROQ_CHAT_URL, {
    method: 'POST',
    headers: {
      Authorization: `Bearer ${settings.groqApiKey}`,
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      model: settings.groqModel,
      messages: [
        { role: 'system', content: systemPrompt },
        { role: 'user', content: userPrompt },
      ],
      temperature,
      max_tokens: maxTokens,
    }),
  });

  if (!response.ok) {
    const detail = (await response.text()).slice(0, 300);
    throw new LLMError(`Groq API returned ${response.status}: ${detail}`);
  }

  const payload = await response.json();
  const content = payload?.choices?.[0]?.message?.content;
  if (content === undefined) throw new LLMError(`Unexpected Groq API response shape: ${JSON.stringify(payload)}`);
  return content;
}

export async function completeJson(systemPrompt, userPrompt, options) {
  let text = (await complete(systemPrompt, userPrompt, options)).trim();
  if (text.startsWith('```')) {
    text = text.replace(/^```json/i, '').replace(/^```/, '').replace(/```$/, '').trim();
  }
  try {
    return JSON.parse(text);
  } catch (err) {
    throw new LLMError(`Groq reply was not valid JSON: ${text.slice(0, 300)}`);
  }
}
