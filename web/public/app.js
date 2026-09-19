// Client-side orchestration. All AI calls (Groq) and pipeline logic run
// server-side now — this just drives the API in sequence and renders the
// results.

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
  pillGroq: document.getElementById('pill-groq'),
  pillRender: document.getElementById('pill-render'),
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
        <td>${escapeHtml(it.video || '—')}</td>
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
  const { analysis } = await api('/api/analyze', { signal });

  const { strategy } = await api('/api/strategize', { signal, analysis, productContext });
  log(`Strategy: ${strategy.framework} — "${strategy.workingTitle}"`);

  const { script } = await api('/api/script', { strategy });
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

  const renderResult = await api('/api/render', { script, title: strategy.workingTitle });
  let videoLabel;
  if (renderResult.rendered) {
    videoLabel = renderResult.mock ? `mock: ${renderResult.videoPath}` : renderResult.videoPath;
    log(`  video rendered${renderResult.mock ? ' (mock)' : ''}: ${renderResult.videoPath}`, 'good');
  } else if (renderResult.reason === 'not_configured') {
    videoLabel = 'script-ready (no render service)';
  } else {
    videoLabel = 'render failed — script-ready';
    log(`  video render failed, script still ready: ${renderResult.reason}`, 'warn');
  }

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
      video: videoLabel,
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
    els.pillGroq.textContent = cfg.groqLive ? 'Groq: live' : 'Groq: mocked (set GROQ_API_KEY)';
    els.pillGroq.classList.add(cfg.groqLive ? 'on' : 'off');
    els.pillRender.textContent = cfg.renderConfigured ? 'Render: connected' : 'Render: not set up';
    els.pillRender.classList.add(cfg.renderConfigured ? 'on' : 'off');
  } catch {
    els.pillYoutube.textContent = 'YouTube: unknown';
    els.pillGroq.textContent = 'Groq: unknown';
    els.pillRender.textContent = 'Render: unknown';
  }

  renderChart();
  renderTiles();
  els.runBtn.addEventListener('click', runCycle);
}

boot();
