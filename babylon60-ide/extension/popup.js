/**
 * BABYLON·60 Alcove — popup controller.
 * Live, local-first panel over the BABYLON·60 backend (localhost:8060):
 * repo lineage (recalcado siempre), consensus verify, real delegation
 * (commit executes; push/deploy → causal crash), and BM25 ledger search.
 */
const BASE = 'http://localhost:8060';
const ALT = 'http://127.0.0.1:8060';

const $ = (id) => document.getElementById(id);
const esc = (s) => String(s ?? '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;').replace(/"/g, '&quot;');

let HOST = BASE;

async function api(path, opts) {
  for (const host of [HOST, HOST === BASE ? ALT : BASE]) {
    try {
      const res = await fetch(`${host}${path}`, { cache: 'no-store', ...opts });
      if (res.ok) { HOST = host; return await res.json(); }
      // surface backend causal errors (e.g. 423 P0 block)
      const body = await res.json().catch(() => ({}));
      const err = new Error(body.detail || res.statusText);
      err.status = res.status;
      throw err;
    } catch (e) {
      if (e.status) throw e; // real HTTP error → propagate, don't retry other host
    }
  }
  throw new Error('backend offline (localhost:8060)');
}
const get = (p) => api(p);
const post = (p, b) => api(p, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(b || {}) });

/* ── Cognitive mode (extension-local) ── */
function applyMode(m) {
  document.body.classList.toggle('mode-nt', m === 'nt');
  document.body.classList.toggle('mode-2e', m !== 'nt');
  $('mode').textContent = m === 'nt' ? '○ NT' : '◐ 2E';
  try { chrome.storage?.local.set({ 'b60-ext-mode': m }); } catch { /* noop */ }
}
function initMode() {
  try {
    chrome.storage.local.get('b60-ext-mode', (r) => applyMode(r?.['b60-ext-mode'] || '2e'));
  } catch { applyMode('2e'); }
  $('mode').addEventListener('click', () => {
    const next = document.body.classList.contains('mode-nt') ? '2e' : 'nt';
    applyMode(next);
  });
}

/* ── Sentinel + stats ── */
async function loadHead() {
  try {
    const [stats, sentinel] = await Promise.all([get('/api/ledger/stats'), get('/api/sentinel/status')]);
    $('conn').classList.remove('off');
    $('entries').textContent = stats?.entries ?? '—';
    $('lamport').textContent = stats?.latest?.lamport_t != null ? `L:${stats.latest.lamport_t}` : '';
    if (sentinel) {
      $('repo').textContent = sentinel.repo_name + (sentinel.branch ? ` @${sentinel.branch}` : '');
      $('repo-head').textContent = sentinel.head || '';
      const reds = (sentinel.warnings || []).filter((w) => w.level === 'red');
      const ambers = (sentinel.warnings || []).filter((w) => w.level === 'amber');
      const wl = [...reds, ...ambers];
      $('warnings').innerHTML = wl.length
        ? wl.map((w) => `<div class="warn ${w.level}"><span class="d"></span><span>${esc(w.msg)}</span></div>`).join('')
        : `<div class="warn amber" style="background:rgba(134,199,154,.12);color:var(--verify)"><span class="d"></span><span>Linaje canónico verificado</span></div>`;
    }
  } catch (e) {
    $('conn').classList.add('off');
    $('repo').textContent = 'backend offline';
    $('warnings').innerHTML = `<div class="warn red"><span class="d"></span><span>${esc(e.message)}</span></div>`;
  }
}

/* ── Verify consensus ── */
$('verify').addEventListener('click', async () => {
  const m = $('verify-msg');
  m.style.color = 'var(--dust-faint)'; m.textContent = 'Recomputando SHA3-256…';
  try {
    const r = await post('/api/ledger/verify', {});
    if (r.valid) { m.style.color = 'var(--verify)'; m.textContent = `✓ VERIFIED · ${r.verified_entries}/${r.total_entries} · cadena intacta`; }
    else { m.style.color = 'var(--break)'; m.textContent = `✗ ROTA en seq ${r.broken_at} (${r.verified_entries}/${r.total_entries})`; }
  } catch (e) { m.style.color = 'var(--break)'; m.textContent = e.message; }
});

/* ── Delegation ── */
async function loadDelegations() {
  try {
    const d = await get('/api/delegation');
    const CLOUD = new Set(['push', 'merge', 'ship', 'deploy']);
    const COL = { QUEUED: 'var(--gold)', EXECUTED: 'var(--verify)', BLOCKED: 'var(--break)', FAILED: 'var(--break)', CANCELLED: 'var(--dust-ghost)' };
    $('deleg-list').innerHTML = (d.delegations || []).slice(0, 5).map((x) => `
      <div class="deleg">
        <span class="st" style="color:${COL[x.state] || 'var(--dust-dim)'}">${x.state}</span>
        <span class="k">${esc(x.kind)}${CLOUD.has(x.kind) ? ' ⛔' : ''}</span>
        <span class="t">${esc(x.directive)}</span>
        ${x.state === 'QUEUED' ? `<button class="btn" data-x="${x.delegation_id}" style="padding:2px 6px;font-size:9px">▶</button>` : ''}
      </div>`).join('');
    $('deleg-list').querySelectorAll('[data-x]').forEach((b) => b.addEventListener('click', () => execDeleg(b.dataset.x)));
  } catch { /* offline handled by head */ }
}
async function execDeleg(id) {
  const m = $('deleg-msg');
  try {
    const r = await post(`/api/delegation/${id}/execute`, {});
    m.style.color = 'var(--verify)'; m.textContent = `✓ ${r.result || 'ejecutado'}`;
  } catch (e) {
    m.style.color = 'var(--break)'; m.textContent = `⛔ ${e.message}`;
  }
  loadDelegations();
}
$('dg').addEventListener('click', async () => {
  const directive = $('di').value.trim();
  const kind = $('dk').value;
  if (!directive) return;
  const m = $('deleg-msg');
  try {
    const r = await post('/api/delegation', { directive, kind });
    $('di').value = '';
    m.style.color = r.cloud_blocked ? 'var(--gold)' : 'var(--verify)';
    m.textContent = r.cloud_blocked ? `⛔ '${kind}' encolado — bloqueado por P0` : `✓ '${kind}' encolado`;
    loadDelegations();
  } catch (e) { m.style.color = 'var(--break)'; m.textContent = e.message; }
});

/* ── BM25 search ── */
$('qb').addEventListener('click', runSearch);
$('q').addEventListener('keydown', (e) => { if (e.key === 'Enter') runSearch(); });
async function runSearch() {
  const q = $('q').value.trim();
  const el = $('q-res');
  if (!q) { el.innerHTML = ''; return; }
  el.innerHTML = `<div style="color:var(--dust-faint);font-size:10px;margin-top:4px">Rankeando…</div>`;
  try {
    const d = await get(`/api/ledger/search?q=${encodeURIComponent(q)}&limit=6`);
    el.innerHTML = d.results.length
      ? d.results.map((r) => `<div class="hit"><span class="sc">${r.score.toFixed(2)}</span><span class="x">#${r.seq} ${esc(r.event_type)} · ${esc(r.snippet).slice(0, 60)}</span></div>`).join('')
      : `<div style="color:var(--dust-ghost);font-size:10px;margin-top:4px">Sin coincidencias en ${d.corpus_size} eventos</div>`;
  } catch (e) { el.innerHTML = `<div style="color:var(--break);font-size:10px;margin-top:4px">${esc(e.message)}</div>`; }
}

/* ── Boot ── */
initMode();
loadHead();
loadDelegations();
try { chrome.runtime?.sendMessage({ type: 'b60-refresh' }, () => void chrome.runtime?.lastError); } catch { /* noop */ }
