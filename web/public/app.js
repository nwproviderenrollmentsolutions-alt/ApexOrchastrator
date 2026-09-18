// Client-side orchestration. Puter.js (loaded via <script> in index.html)
// must run in the browser — it authenticates against the viewer's free
// Puter account, so the Analyst + Script stages happen here, not on the
// server. Everything deterministic (radar, strategist, QC, publish,
// performance, learning) is a fetch to this app's own API.

const state = {
  published: 0,
  rejected: 0,
  hookScores: [],
  platformViews: { tiktok: 0, youtube_shorts: 0, instagram_reels: 0 },
  items: [],
};

const els = {
  runBtn: document.getElementById('run-btn'),
  runState: document.getElementById('run-state'),
  product: document.getElementById('product-input'),
  limit: document.getElementById('limit-input'),
  log: document.getElementById('log'),
  itemsBody: document.getElementById('items-body'),
  tilePublished: document.getElementById('tile-published'),
  tileRejected: document.getElementById('tile-rejected'),
  tileHookscore: document.getElementById('tile-hookscore'),
  tileWinning: document.getElementById('tile-winning'),
  pillYoutube: document.getElementById('pill-youtube'),
  pillPuter: document.getElementById('pill-puter'),
  chart: document.getElementById('platform-chart'),
};

function log(message, kind = '') {
  const line = document.createElement('div');
  line.className = `entry ${kind}`;
  line.textContent = message;
  els.log.appendChild(line);
  els.log.scrollTop = els.log.scrollHeight;
}

async function api(path, body) {
  const res = await fetch(path, {
    method: body === undefined ? 'GET' : 'POST',
    headers: body === undefined ? undefined : { 'Content-Type': 'application/json' },
    body: body === undefined ? undefined : JSON.stringify(body),
  });
  const data = await res.json().catch(() => ({}));
  if (!res.ok) throw new Error(data.error || `${path} failed (${res.status})`);
  return data;
}

// --- Puter.js AI calls, each with a mocked fallback -----------------------

const HOOKS = ['POV: you just found out...', 'Nobody is talking about this, but...', 'I tried this for 30 days and...', 'Stop doing X, do this instead'];
const PATTERNS = ['3-act reveal', 'listicle countdown', 'problem-agitate-solve', 'before/after'];
const STORY_STRUCTURES = ['cold open + payoff', 'relatable setup + twist', 'tutorial + result'];
const EDITING_NOTES = ['fast cuts every 1-2s, captions burned in, jump cuts on filler words', 'single continuous take, subtle zoom for emphasis', 'text overlays synced to voiceover beats'];
const CTAS = ['follow for part 2', 'comment your result', 'link in bio', 'save this for later'];
const COMMENT_THEMES = [['asking for source', 'tagging friends'], ['asking for a tutorial', 'sharing their own results'], ['relating personal story', 'asking follow-up questions']];

function pick(arr) { return arr[Math.floor(Math.random() * arr.length)]; }

function mockAnalyze(signal) {
  const viralityScore = Math.min(100, (signal.velocity / 50_000) * 100);
  return {
    hook: pick(HOOKS), pattern: pick(PATTERNS), storyStructure: pick(STORY_STRUCTURES),
    editingNotes: pick(EDITING_NOTES), cta: pick(CTAS), topCommentsThemes: pick(COMMENT_THEMES),
    viralityScore: Math.round(viralityScore * 10) / 10,
  };
}

function mockScript(strategy) {
  const a = strategy.analysis;
  return `[HOOK] ${a.hook}\n[SETUP - ${strategy.framework}] ${strategy.productAngle}\n[STORY - ${a.storyStructure}] Walk through the pain point, then the moment it clicked.\n[EDITING] ${a.editingNotes}\n[CTA] ${a.cta}`;
}

async function puterChatText(prompt) {
  const res = await window.puter.ai.chat(prompt);
  if (typeof res === 'string') return res;
  if (res?.message?.content) return res.message.content;
  if (res?.text) return res.text;
  return String(res);
}

function parseJsonReply(text) {
  let cleaned = text.trim();
  if (cleaned.startsWith('```')) {
    cleaned = cleaned.replace(/^```json/i, '').replace(/^```/, '').replace(/```$/, '').trim();
  }
  return JSON.parse(cleaned);
}

async function analyzeSignal(signal) {
  if (!window.puter?.ai?.chat) return mockAnalyze(signal);
  const prompt = `You are a short-form video virality analyst. Given this trending post's metadata, break down why it works. Reply with ONLY a JSON object with keys: hook (string), pattern (string), story_structure (string), editing_notes (string), cta (string), top_comments_themes (array of 2-4 short strings), virality_score (number 0-100). No prose, no markdown fencing.

Platform: ${signal.platform}
Topic: ${signal.topic}
Views: ${signal.viewCount}
Velocity (views/hour): ${Math.round(signal.velocity)}
Audio/sound: ${signal.audioOrSound}`;
  try {
    const text = await puterChatText(prompt);
    const data = parseJsonReply(text);
    return {
      hook: String(data.hook), pattern: String(data.pattern), storyStructure: String(data.story_structure),
      editingNotes: String(data.editing_notes), cta: String(data.cta),
      topCommentsThemes: Array.isArray(data.top_comments_themes) ? data.top_comments_themes.map(String) : [],
      viralityScore: Number(data.virality_score) || 50,
    };
  } catch (err) {
    log(`Puter analysis failed, using mock: ${err.message}`, 'warn');
    return mockAnalyze(signal);
  }
}

async function writeScript(strategy) {
  if (!window.puter?.ai?.chat) return mockScript(strategy);
  const a = strategy.analysis;
  const prompt = `You write short, punchy UGC-style scripts for TikTok/Shorts/Reels (30-45 seconds spoken). Structure the script with labeled beats on separate lines: [HOOK], [SETUP], [STORY], [EDITING] (camera/editing direction, not spoken), [CTA]. Keep spoken lines conversational, first-person, no hashtags. Reply with ONLY the script text.

Framework: ${strategy.framework}
Working title: ${strategy.workingTitle}
Hook to riff on: ${a.hook}
Story structure: ${a.storyStructure}
Product/angle to weave in: ${strategy.productAngle}
Editing notes to include: ${a.editingNotes}
CTA: ${a.cta}`;
  try {
    return await puterChatText(prompt);
  } catch (err) {
    log(`Puter script generation failed, using template: ${err.message}`, 'warn');
    return mockScript(strategy);
  }
}

// --- Chart + tiles ----------------------------------------------------------

function renderChart() {
  const platforms = [
    { key: 'tiktok', label: 'TikTok', color: 'var(--series-tiktok)' },
    { key: 'youtube_shorts', label: 'YouTube Shorts', color: 'var(--series-youtube)' },
    { key: 'instagram_reels', label: 'Instagram Reels', color: 'var(--series-instagram)' },
  ];
  const max = Math.max(1, ...platforms.map((p) => state.platformViews[p.key]));
  const rowH = 36;
  const chartW = 560;
  const labelW = 130;
  const barMaxW = chartW - labelW - 60;

  let svg = `<line class="axis-line" x1="${labelW}" y1="4" x2="${labelW}" y2="${platforms.length * rowH}" />`;
  platforms.forEach((p, i) => {
    const y = i * rowH + rowH / 2;
    const value = state.platformViews[p.key];
    const w = Math.round((value / max) * barMaxW);
    svg += `<text x="${labelW - 10}" y="${y + 4}" text-anchor="end">${p.label}</text>`;
    svg += `<rect x="${labelW}" y="${y - 10}" width="${Math.max(w, 2)}" height="20" rx="4" fill="${p.color}" />`;
    svg += `<text class="value-label" x="${labelW + w + 8}" y="${y + 4}">${value.toLocaleString()}</text>`;
  });
  els.chart.setAttribute('viewBox', `0 0 ${chartW} ${platforms.length * rowH + 8}`);
  els.chart.innerHTML = svg;
}

function renderTiles() {
  els.tilePublished.textContent = state.published;
  els.tileRejected.textContent = state.rejected;
  const avgHook = state.hookScores.length
    ? (state.hookScores.reduce((a, b) => a + b, 0) / state.hookScores.length).toFixed(1)
    : '—';
  els.tileHookscore.textContent = avgHook;
}

function addItemRow(item) {
  state.items.unshift(item);
  state.items = state.items.slice(0, 25);
  els.itemsBody.innerHTML = state.items
    .map(
      (it) => `<tr>
        <td>${escapeHtml(it.title)}</td>
        <td>${it.platform || '—'}</td>
        <td class="status-${it.status}">${it.status}</td>
        <td>${it.hookScore ?? '—'}</td>
        <td>${it.engagement != null ? (it.engagement * 100).toFixed(2) + '%' : '—'}</td>
      </tr>`
    )
    .join('');
}

function escapeHtml(str) {
  return String(str).replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
}

// --- Pipeline cycle ----------------------------------------------------------

async function processSignal(signal, productContext) {
  log(`Analyzing "${signal.topic}" (${signal.platform})…`);
  const analysis = await analyzeSignal(signal);

  const { strategy } = await api('/api/strategize', { signal, analysis, productContext });
  log(`Strategy: ${strategy.framework} — "${strategy.workingTitle}"`);

  const script = await writeScript(strategy);
  const { package: pkg } = await api('/api/package', { strategy, script });

  const qcResult = await api('/api/qc', { package: pkg });
  if (!qcResult.approved) {
    const reasons = [];
    if (qcResult.hookScore < 60) reasons.push(`hook_score ${qcResult.hookScore} < 60`);
    if (!qcResult.brandSafetyPass) reasons.push('brand safety failed');
    if (!qcResult.disclosurePass) reasons.push('missing disclosure');
    if (!qcResult.copyrightPass) reasons.push('copyright risk');
    log(`REJECTED: "${strategy.workingTitle}" — ${reasons.join('; ')}`, 'bad');
    state.rejected += 1;
    addItemRow({ title: strategy.workingTitle, status: 'rejected' });
    renderTiles();
    return;
  }

  state.published += 1;
  state.hookScores.push(qcResult.hookScore);
  log(`PUBLISHED: "${strategy.workingTitle}" (hook ${qcResult.hookScore})`, 'good');

  const { publishResults } = await api('/api/publish', { qcResult });
  for (const publishResult of publishResults) {
    const { metrics, engagementRate } = await api('/api/performance', { publishResult });
    state.platformViews[publishResult.platform] = (state.platformViews[publishResult.platform] || 0) + metrics.views;
    const { record } = await api('/api/learn', { metrics });
    log(`  ${publishResult.platform}: ${record.notes}`, record.worked ? 'good' : '');
    addItemRow({
      title: strategy.workingTitle,
      platform: publishResult.platform,
      status: 'published',
      hookScore: qcResult.hookScore,
      engagement: engagementRate,
    });
  }
  renderTiles();
  renderChart();
}

async function runCycle() {
  els.runBtn.disabled = true;
  els.runState.textContent = 'Scanning…';
  const limit = Math.max(1, Math.min(10, Number(els.limit.value) || 4));
  const productContext = els.product.value || 'our product';

  try {
    const { signals } = await api('/api/scan', { limit });
    log(`Scanned ${signals.length} trending signal(s).`);
    for (const signal of signals) {
      els.runState.textContent = `Processing "${signal.topic}"…`;
      await processSignal(signal, productContext);
    }
    const { winningTopics } = await api('/api/state');
    els.tileWinning.textContent = new Set(winningTopics).size;
    els.runState.textContent = 'Done.';
  } catch (err) {
    log(`Cycle failed: ${err.message}`, 'bad');
    els.runState.textContent = 'Error — see log.';
  } finally {
    els.runBtn.disabled = false;
  }
}

// --- Boot ---------------------------------------------------------------

async function boot() {
  try {
    const cfg = await api('/api/config');
    els.pillYoutube.textContent = cfg.youtubeLive ? 'YouTube: live' : 'YouTube: mocked';
    els.pillYoutube.classList.add(cfg.youtubeLive ? 'on' : 'off');
  } catch {
    els.pillYoutube.textContent = 'YouTube: unknown';
  }

  if (window.puter?.ai?.chat) {
    els.pillPuter.textContent = 'Puter.js: ready';
    els.pillPuter.classList.add('on');
  } else {
    els.pillPuter.textContent = 'Puter.js: unavailable (using mock)';
    els.pillPuter.classList.add('off');
  }

  renderChart();
  renderTiles();
  els.runBtn.addEventListener('click', runCycle);
}

boot();
