/**
 * BABYLON60 IDE — Main Application Core
 * 2e Cognitive Architecture (ADHD + AACC / Twice-Exceptional)
 *
 * Architecture:
 *   SPINE (56px) | CONTEXT PANE (264px, CMD+B) | FOCUS ZONE (flex:1)
 *   + TACHOMETER (3px ambient top bar)
 *   + COMMAND PALETTE (CMD+K)
 *   + SCRATCHPAD (CMD+Shift+Space)
 *   + AGENT MODAL (body doubling / loop guard)
 *   + STATUS BAR (28px fixed)
 *
 * Routes: canvas | ledger | databases | query | swarm
 * Kernel: Tauri v2 IPC + CortexLedger (Rust) + KINETIC BIND RAW Ontology
 */
import { get, post, connectWebSocket } from './api.js';
import { registerRoute, navigate, getInitialRoute } from './router.js';
import { listVectors, dispatchVector } from './ontology.js';

/* ══════════════════════════════════════════════════════════
   GLOBAL STATE
   ══════════════════════════════════════════════════════════ */
const S = {
  contextPaneOpen: true,
  bifocalMode: 'micro',           // 'micro' | 'macro'
  tachometerState: 'idle',        // 'idle' | 'indexing' | 'working' | 'alert' | 'done'
  paletteOpen: false,
  scratchpadOpen: false,
  scratchpadItems: JSON.parse(localStorage.getItem('b60-scratch') || '[]'),
  databaseList: [],
  ledgerStats: null,
  telemetrySocket: null,
  loopDetector: {
    route: null,
    routeEnteredAt: 0,
    interventionFired: false,
  },
  sessionStart: Date.now(),
  activeRoute: null,
  swarmLog: [],
  canvasOffset: { x: 0, y: 0 },
  canvasScale: 1,
};

/* ══════════════════════════════════════════════════════════
   BOOT
   ══════════════════════════════════════════════════════════ */
document.addEventListener('DOMContentLoaded', async () => {
  setTachometer('indexing');
  setupSpine();
  setupContextPane();
  setupCommandPalette();
  setupScratchpad();
  setupKeyboard();
  setupRouter();
  setupBifocal();
  setupLoopDetector();

  await Promise.all([
    refreshDatabaseList(),
    refreshLedgerStats(),
  ]);

  updateStatusBar();
  setTachometer('done');

  // Context restore banner (simulates remembering last session)
  const lastRoute = localStorage.getItem('b60-route') || 'ledger';
  showRestoreBanner(lastRoute);

  navigate(getInitialRoute());
  setTachometer('idle');
});

/* ══════════════════════════════════════════════════════════
   TACHOMETER — Ambient agent workload indicator
   3px bar at top. No notifications. Just peripheral signal.
   ══════════════════════════════════════════════════════════ */
function setTachometer(state) {
  S.tachometerState = state;
  const el = document.getElementById('tachometer');
  if (!el) return;
  el.className = `tachometer ${state !== 'idle' ? state : ''}`;

  // Update agent status segment in status bar
  const agentSeg = document.getElementById('status-agent-segment');
  if (!agentSeg) return;
  if (state === 'working' || state === 'indexing') {
    agentSeg.style.display = 'flex';
    const txt = document.getElementById('status-agent-text');
    if (txt) txt.textContent = state === 'indexing' ? 'Indexing context...' : 'Agent working...';
  } else {
    agentSeg.style.display = 'none';
  }
}

/* ══════════════════════════════════════════════════════════
   SPINE — Icon-only navigation
   No labels, no sections. Just glyphs.
   ══════════════════════════════════════════════════════════ */
function setupSpine() {
  const spine = document.getElementById('spine');
  const routes = [
    { id: 'canvas',    icon: '⬡', tip: 'Architecture Canvas  ⌘5' },
    { id: 'ledger',    icon: '⧉', tip: 'BFT Ledger  ⌘1' },
    { id: 'databases', icon: '⛁', tip: 'Ontologies  ⌘2' },
    { id: 'query',     icon: '❯_', tip: 'SQL Console  ⌘3' },
    { id: 'swarm',     icon: '⚡', tip: 'Agent Swarm  ⌘4' },
  ];

  // Re-render: canonical single-pass DOM build
  spine.innerHTML = '';
  const logo = document.createElement('div');
  logo.className = 'spine-logo';
  logo.title = 'BABYLON·60';
  logo.innerHTML = '<div class="spine-logo-dot"></div>';
  spine.appendChild(logo);

  routes.forEach((r, i) => {
    if (i === 1) {
      const sep = document.createElement('div');
      sep.className = 'spine-separator';
      spine.appendChild(sep);
    }
    const btn = document.createElement('button');
    btn.className = 'spine-icon';
    btn.dataset.route = r.id;
    btn.dataset.tooltip = r.tip;
    btn.setAttribute('aria-label', r.tip);
    btn.textContent = r.icon;
    btn.addEventListener('click', () => navigate(r.id));
    spine.appendChild(btn);
  });
}

function setActiveSpineIcon(route) {
  document.querySelectorAll('.spine-icon').forEach(el => {
    el.classList.toggle('active', el.dataset.route === route);
  });
}

/* ══════════════════════════════════════════════════════════
   CONTEXT PANE — Semantic map of current project state
   Shows blast radius, ontology tree, agent tasks.
   Collapsible with CMD+B.
   ══════════════════════════════════════════════════════════ */
function setupContextPane() {
  const btnCollapse = document.getElementById('btn-collapse-ctx');
  if (btnCollapse) {
    btnCollapse.addEventListener('click', toggleContextPane);
  }
  renderContextPaneContent();
}

function toggleContextPane() {
  S.contextPaneOpen = !S.contextPaneOpen;
  const pane = document.getElementById('context-pane');
  const btn = document.getElementById('btn-collapse-ctx');
  if (!pane) return;
  pane.classList.toggle('collapsed', !S.contextPaneOpen);
  if (btn) btn.textContent = S.contextPaneOpen ? '⟨' : '⟩';
}

function renderContextPaneContent() {
  const body = document.getElementById('context-pane-body');
  if (!body) return;
  body.innerHTML = `
    <div class="ctx-section">
      <div class="ctx-section-label">Inspector</div>
      <div class="ctx-item active" data-route="canvas">
        <span class="ctx-item-icon">⬡</span>
        <span class="ctx-item-label">Architecture</span>
        <span class="ctx-item-badge verify">live</span>
      </div>
      <div class="ctx-item" data-route="ledger">
        <span class="ctx-item-icon">⧉</span>
        <span class="ctx-item-label">BFT Ledger</span>
        <span class="ctx-item-badge gold" id="ctx-ledger-count">—</span>
      </div>
      <div class="ctx-item" data-route="databases">
        <span class="ctx-item-icon">⛁</span>
        <span class="ctx-item-label">Ontologies</span>
        <span class="ctx-item-badge gold" id="ctx-db-count">—</span>
      </div>
    </div>
    <div class="ctx-section">
      <div class="ctx-section-label">Analysis</div>
      <div class="ctx-item" data-route="query">
        <span class="ctx-item-icon">❯_</span>
        <span class="ctx-item-label">SQL Console</span>
      </div>
      <div class="ctx-item" data-route="swarm">
        <span class="ctx-item-icon">⚡</span>
        <span class="ctx-item-label">Agent Swarm</span>
        <span class="ctx-item-badge lapis" style="color:var(--lapis-bright)">0</span>
      </div>
    </div>
    <div class="ctx-section">
      <div class="ctx-section-label">Scratchpad</div>
      <div id="ctx-scratch-preview" style="padding:4px 12px; font-size:0.65rem; color:var(--dust-faint);">
        ${S.scratchpadItems.length === 0
          ? '<span style="color:var(--dust-ghost)">No notes yet</span>'
          : `<span style="color:var(--dust-dim)">${S.scratchpadItems.length} note${S.scratchpadItems.length > 1 ? 's' : ''}</span>`
        }
      </div>
    </div>
    <div class="ctx-section">
      <div class="ctx-section-label">System</div>
      <div class="ctx-item depth-1">
        <span class="ctx-item-icon" style="font-size:0.6rem">●</span>
        <span class="ctx-item-label" style="font-size:0.65rem">master_ledger.db</span>
        <span class="ctx-item-badge verify">ok</span>
      </div>
      <div class="ctx-item depth-1">
        <span class="ctx-item-icon" style="font-size:0.6rem">●</span>
        <span class="ctx-item-label" style="font-size:0.65rem">cortex_ontology.db</span>
        <span class="ctx-item-badge">RO</span>
      </div>
      <div class="ctx-item depth-1">
        <span class="ctx-item-icon" style="font-size:0.6rem">●</span>
        <span class="ctx-item-label" style="font-size:0.65rem">telemetry.db</span>
        <span class="ctx-item-badge">RO</span>
      </div>
    </div>
  `;

  body.querySelectorAll('.ctx-item[data-route]').forEach(el => {
    el.addEventListener('click', () => navigate(el.dataset.route));
  });
}

function updateContextPaneCounts() {
  const dbCount = document.getElementById('ctx-db-count');
  if (dbCount) dbCount.textContent = S.databaseList.length || '—';
  const ledgerCount = document.getElementById('ctx-ledger-count');
  if (ledgerCount && S.ledgerStats) ledgerCount.textContent = S.ledgerStats.total_entries || '—';
}

function setActiveContextItem(route) {
  document.querySelectorAll('.ctx-item[data-route]').forEach(el => {
    el.classList.toggle('active', el.dataset.route === route);
  });
}

/* ══════════════════════════════════════════════════════════
   STATUS BAR — Single line of truth
   ══════════════════════════════════════════════════════════ */
function updateStatusBar() {
  const connDot = document.getElementById('status-conn-dot');
  const connText = document.getElementById('status-conn-text');
  const dbCount = document.getElementById('status-db-count');
  const ledgerEntries = document.getElementById('status-ledger-entries');
  const lamport = document.getElementById('status-lamport');

  if (connDot) connDot.className = 'status-dot';
  if (connText) connText.textContent = 'CONNECTED';
  if (dbCount) dbCount.textContent = S.databaseList.length || '—';
  if (ledgerEntries) ledgerEntries.textContent = S.ledgerStats?.total_entries || '—';
  if (lamport) lamport.textContent = S.ledgerStats?.latest_lamport_t != null
    ? `L:${S.ledgerStats.latest_lamport_t}`
    : '—';
}

/* ══════════════════════════════════════════════════════════
   BIFOCAL TOGGLE — Macro ↔ Micro
   CMD+M: switches between system view and tunnel view.
   AACC rationale: system thinkers need the WHOLE first.
   ══════════════════════════════════════════════════════════ */
function setupBifocal() {
  const btn = document.getElementById('btn-bifocal');
  if (btn) btn.addEventListener('click', toggleBifocal);
}

function toggleBifocal() {
  S.bifocalMode = S.bifocalMode === 'micro' ? 'macro' : 'micro';
  document.body.classList.toggle('macro-mode', S.bifocalMode === 'macro');
  document.body.classList.toggle('micro-mode', S.bifocalMode === 'micro');
  const btn = document.getElementById('btn-bifocal');
  if (btn) btn.textContent = S.bifocalMode === 'macro' ? 'MACRO ⊞' : 'MICRO ⊞';

  if (S.bifocalMode === 'macro') {
    navigate('canvas');
  }
}

/* ══════════════════════════════════════════════════════════
   COMMAND PALETTE — CMD+K
   Fuzzy navigation + action dispatcher.
   Zero clicks. Keyboard-first.
   ══════════════════════════════════════════════════════════ */
const PALETTE_COMMANDS = [
  { icon: '⬡', label: 'Architecture Canvas', desc: 'Macro system view', shortcut: '⌘5', action: () => navigate('canvas') },
  { icon: '⧉', label: 'BFT Ledger',          desc: 'Hash-chain inspector', shortcut: '⌘1', action: () => navigate('ledger') },
  { icon: '⛁', label: 'Ontologies',           desc: 'SQLite database explorer', shortcut: '⌘2', action: () => navigate('databases') },
  { icon: '❯_', label: 'SQL Console',         desc: 'Read-only query interface', shortcut: '⌘3', action: () => navigate('query') },
  { icon: '⚡', label: 'Agent Swarm',          desc: 'Active agent telemetry', shortcut: '⌘4', action: () => navigate('swarm') },
  { icon: '⬡', label: 'Verify Chain Integrity', desc: 'Run BFT hash-chain verification', shortcut: '', action: () => { navigate('ledger'); setTimeout(() => document.getElementById('btn-verify-chain')?.click(), 400); } },
  { icon: '⟨', label: 'Toggle Context Pane',  desc: 'Show / hide semantic map', shortcut: '⌘B', action: toggleContextPane },
  { icon: '⊞', label: 'Toggle Macro / Micro', desc: 'Switch bifocal view mode', shortcut: '⌘M', action: toggleBifocal },
  { icon: '◎', label: 'Open Scratchpad',      desc: 'Dump a thought (no focus loss)', shortcut: '⌘⇧Space', action: () => toggleScratchpad(true) },
  { icon: '↺', label: 'Restore Session',      desc: 'Return to last known context', shortcut: '', action: () => showRestoreBanner(localStorage.getItem('b60-route') || 'ledger') },
];

let paletteSelected = 0;
let paletteFiltered = [...PALETTE_COMMANDS];

function setupCommandPalette() {
  const overlay = document.getElementById('palette-overlay');
  const input = document.getElementById('palette-input');
  if (!overlay || !input) return;

  overlay.addEventListener('click', e => { if (e.target === overlay) closePalette(); });
  input.addEventListener('input', () => filterPalette(input.value));
  input.addEventListener('keydown', handlePaletteKey);
}

function openPalette() {
  S.paletteOpen = true;
  const overlay = document.getElementById('palette-overlay');
  const input = document.getElementById('palette-input');
  if (!overlay || !input) return;
  overlay.classList.add('visible');
  overlay.setAttribute('aria-hidden', 'false');
  input.value = '';
  paletteSelected = 0;
  paletteFiltered = [...PALETTE_COMMANDS];
  renderPaletteResults();
  setTimeout(() => input.focus(), 50);
}

function closePalette() {
  S.paletteOpen = false;
  const overlay = document.getElementById('palette-overlay');
  if (overlay) { overlay.classList.remove('visible'); overlay.setAttribute('aria-hidden', 'true'); }
}

function filterPalette(query) {
  const q = query.toLowerCase().trim();
  paletteSelected = 0;
  if (!q) {
    paletteFiltered = [...PALETTE_COMMANDS];
  } else {
    paletteFiltered = PALETTE_COMMANDS.filter(c =>
      c.label.toLowerCase().includes(q) || c.desc.toLowerCase().includes(q)
    );
  }
  renderPaletteResults(q);
}

function renderPaletteResults(query = '') {
  const container = document.getElementById('palette-results');
  if (!container) return;

  if (paletteFiltered.length === 0) {
    container.innerHTML = `<div class="palette-empty">No commands match "<strong>${query}</strong>"</div>`;
    return;
  }

  container.innerHTML = `
    <div class="palette-section-label">Commands</div>
    ${paletteFiltered.map((cmd, i) => {
      const labelHighlighted = query
        ? cmd.label.replace(new RegExp(`(${query})`, 'gi'), '<span class="palette-match">$1</span>')
        : cmd.label;
      return `
        <div class="palette-item ${i === paletteSelected ? 'selected' : ''}" data-index="${i}">
          <span class="palette-item-icon">${cmd.icon}</span>
          <span class="palette-item-label">${labelHighlighted}</span>
          <span class="palette-item-desc">${cmd.desc}</span>
          ${cmd.shortcut ? `<span class="palette-item-shortcut">${cmd.shortcut}</span>` : ''}
        </div>
      `;
    }).join('')}
  `;

  container.querySelectorAll('.palette-item').forEach(el => {
    el.addEventListener('click', () => {
      const idx = parseInt(el.dataset.index);
      if (paletteFiltered[idx]) { paletteFiltered[idx].action(); closePalette(); }
    });
    el.addEventListener('mouseenter', () => {
      paletteSelected = parseInt(el.dataset.index);
      container.querySelectorAll('.palette-item').forEach((e, i) => e.classList.toggle('selected', i === paletteSelected));
    });
  });
}

function handlePaletteKey(e) {
  if (e.key === 'Escape') { closePalette(); return; }
  if (e.key === 'ArrowDown') {
    e.preventDefault();
    paletteSelected = Math.min(paletteSelected + 1, paletteFiltered.length - 1);
    renderPaletteResults(document.getElementById('palette-input')?.value || '');
  }
  if (e.key === 'ArrowUp') {
    e.preventDefault();
    paletteSelected = Math.max(paletteSelected - 1, 0);
    renderPaletteResults(document.getElementById('palette-input')?.value || '');
  }
  if (e.key === 'Enter') {
    e.preventDefault();
    if (paletteFiltered[paletteSelected]) {
      paletteFiltered[paletteSelected].action();
      closePalette();
    }
  }
}

/* ══════════════════════════════════════════════════════════
   SCRATCHPAD — Mental dump modal (CMD+Shift+Space)
   Captures "thought bursts" without breaking flow.
   Saves to localStorage. Agent can read and schedule.
   ══════════════════════════════════════════════════════════ */
function setupScratchpad() {
  const modal = document.getElementById('scratchpad-modal');
  const input = document.getElementById('scratchpad-input');
  const saveBtn = document.getElementById('scratchpad-save');
  const closeBtn = document.getElementById('scratchpad-close');
  if (!modal || !input) return;

  saveBtn?.addEventListener('click', saveScratchpadItem);
  closeBtn?.addEventListener('click', () => toggleScratchpad(false));

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); saveScratchpadItem(); }
    if (e.key === 'Escape') toggleScratchpad(false);
  });

  renderScratchpadItems();
}

function toggleScratchpad(force) {
  const modal = document.getElementById('scratchpad-modal');
  const input = document.getElementById('scratchpad-input');
  if (!modal) return;
  S.scratchpadOpen = force !== undefined ? force : !S.scratchpadOpen;
  modal.classList.toggle('visible', S.scratchpadOpen);
  modal.setAttribute('aria-hidden', String(!S.scratchpadOpen));
  if (S.scratchpadOpen && input) { setTimeout(() => input.focus(), 60); }
}

function saveScratchpadItem() {
  const input = document.getElementById('scratchpad-input');
  if (!input || !input.value.trim()) return;
  const item = {
    id: Date.now(),
    text: input.value.trim(),
    time: new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' }),
  };
  S.scratchpadItems.unshift(item);
  if (S.scratchpadItems.length > 20) S.scratchpadItems.pop();
  localStorage.setItem('b60-scratch', JSON.stringify(S.scratchpadItems));
  input.value = '';
  renderScratchpadItems();
  renderContextPaneContent();

  // Micro-reward: brief tachometer flash
  setTachometer('done');
  setTimeout(() => setTachometer('idle'), 2000);
}

function renderScratchpadItems() {
  const container = document.getElementById('scratchpad-items');
  if (!container) return;
  if (S.scratchpadItems.length === 0) {
    container.innerHTML = '';
    return;
  }
  container.innerHTML = S.scratchpadItems.map(item => `
    <div class="scratchpad-item" data-id="${item.id}">
      <span class="scratchpad-item-time">${item.time}</span>
      <span class="scratchpad-item-text">${item.text}</span>
      <span class="scratchpad-item-del" data-del="${item.id}" title="Remove">✕</span>
    </div>
  `).join('');

  container.querySelectorAll('[data-del]').forEach(el => {
    el.addEventListener('click', e => {
      e.stopPropagation();
      const id = parseInt(el.dataset.del);
      S.scratchpadItems = S.scratchpadItems.filter(i => i.id !== id);
      localStorage.setItem('b60-scratch', JSON.stringify(S.scratchpadItems));
      renderScratchpadItems();
      renderContextPaneContent();
    });
  });
}

/* ══════════════════════════════════════════════════════════
   AGENT MODAL — Body Doubling / Loop Guard / Approvals
   Drops from top edge. Disappears after action.
   TDAH rationale: breaks dopamine loops, offers perspective.
   ══════════════════════════════════════════════════════════ */
function showAgentModal({ icon = '⬡', message, actions = [] }) {
  const modal = document.getElementById('agent-modal');
  const iconEl = document.getElementById('agent-modal-icon');
  const msgEl = document.getElementById('agent-modal-msg');
  const actionsEl = document.getElementById('agent-modal-actions');
  if (!modal || !msgEl || !actionsEl) return;

  if (iconEl) iconEl.textContent = icon;
  msgEl.textContent = message;

  const defaultActions = [
    { label: 'Got it', fn: hideAgentModal, primary: true },
    { label: 'Dismiss', fn: hideAgentModal },
  ];
  const finalActions = actions.length > 0 ? actions : defaultActions;

  actionsEl.innerHTML = finalActions.map((a, i) =>
    `<button class="btn ${a.primary ? 'btn-primary' : ''}" style="font-size:0.65rem" data-action-idx="${i}">${a.label}</button>`
  ).join('');

  actionsEl.querySelectorAll('button').forEach(btn => {
    btn.addEventListener('click', () => {
      finalActions[parseInt(btn.dataset.actionIdx)]?.fn?.();
    });
  });

  modal.classList.add('visible');
  modal.setAttribute('aria-hidden', 'false');
  setTachometer('alert');
}

function hideAgentModal() {
  const modal = document.getElementById('agent-modal');
  if (modal) { modal.classList.remove('visible'); modal.setAttribute('aria-hidden', 'true'); }
  setTachometer('idle');
}

/* ══════════════════════════════════════════════════════════
   LOOP DETECTOR — Cognitive Hand Brake
   If same route for >25 minutes without navigation change,
   fires a gentle body-doubling intervention.
   ══════════════════════════════════════════════════════════ */
function setupLoopDetector() {
  // Check every 2 minutes
  setInterval(() => {
    if (!S.loopDetector.route) return;
    if (S.loopDetector.interventionFired) return;
    const elapsed = Date.now() - S.loopDetector.routeEnteredAt;
    if (elapsed > 25 * 60 * 1000) { // 25 minutes
      S.loopDetector.interventionFired = true;
      const route = S.loopDetector.route;
      showAgentModal({
        icon: '⏱',
        message: `You've been in ${route.toUpperCase()} for over 25 minutes. Deep focus is good — but want to step back and see the whole system?`,
        actions: [
          { label: 'Show Architecture', primary: true, fn: () => { hideAgentModal(); navigate('canvas'); } },
          { label: 'Keep Going', fn: hideAgentModal },
          { label: 'Dump a thought →', fn: () => { hideAgentModal(); toggleScratchpad(true); } },
        ],
      });
    }
  }, 2 * 60 * 1000);
}

/* ══════════════════════════════════════════════════════════
   CONTEXT RESTORE BANNER
   Shows on boot. Reminds user where they were.
   TDAH rationale: eliminates startup friction / blank slate panic.
   ══════════════════════════════════════════════════════════ */
function showRestoreBanner(lastRoute) {
  const banner = document.getElementById('restore-banner');
  const msg = document.getElementById('restore-msg');
  const points = document.getElementById('restore-points');
  const dismiss = document.getElementById('restore-dismiss');
  if (!banner || !msg) return;

  const routeLabels = {
    ledger: 'BFT Ledger', databases: 'Ontologies', query: 'SQL Console',
    swarm: 'Agent Swarm', canvas: 'Architecture Canvas',
  };

  const bullets = [
    `Last active: ${routeLabels[lastRoute] || lastRoute}`,
    `${S.databaseList.length || '—'} databases available`,
    S.ledgerStats?.total_entries
      ? `${S.ledgerStats.total_entries} ledger entries — chain intact`
      : 'Ledger loading...',
  ];

  msg.textContent = 'Session restored · ';
  if (points) {
    points.innerHTML = bullets.map(b =>
      `<span class="restore-point">${b}</span>`
    ).join('');
  }

  banner.style.display = 'flex';
  dismiss?.addEventListener('click', () => { banner.style.display = 'none'; });
  setTimeout(() => { banner.style.display = 'none'; }, 12000);
}

/* ══════════════════════════════════════════════════════════
   KEYBOARD SHORTCUTS — Global
   ══════════════════════════════════════════════════════════ */
function setupKeyboard() {
  const routeKeys = { '1': 'ledger', '2': 'databases', '3': 'query', '4': 'swarm', '5': 'canvas' };

  window.addEventListener('keydown', e => {
    const mod = e.metaKey || e.ctrlKey;

    // CMD+K → Command Palette
    if (mod && e.key === 'k' && !e.shiftKey) { e.preventDefault(); S.paletteOpen ? closePalette() : openPalette(); return; }

    // CMD+Shift+Space → Scratchpad
    if (mod && e.shiftKey && e.code === 'Space') { e.preventDefault(); toggleScratchpad(); return; }

    // CMD+B → Toggle context pane
    if (mod && e.key === 'b' && !e.shiftKey) { e.preventDefault(); toggleContextPane(); return; }

    // CMD+M → Bifocal toggle
    if (mod && e.key === 'm' && !e.shiftKey) { e.preventDefault(); toggleBifocal(); return; }

    // CMD+1..5 → Route navigation
    if (mod && routeKeys[e.key]) { e.preventDefault(); navigate(routeKeys[e.key]); return; }

    // ESC → Close modals
    if (e.key === 'Escape') {
      if (S.paletteOpen) { closePalette(); return; }
      if (S.scratchpadOpen) { toggleScratchpad(false); return; }
    }
  });
}

/* ══════════════════════════════════════════════════════════
   ROUTER — wires routes to render functions
   ══════════════════════════════════════════════════════════ */
function setupRouter() {
  registerRoute('canvas',    renderCanvasPage);
  registerRoute('ledger',    renderLedgerPage);
  registerRoute('databases', renderDatabasesPage);
  registerRoute('query',     renderQueryPage);
  registerRoute('swarm',     renderSwarmPage);

  window.addEventListener('hashchange', () => {
    const hash = window.location.hash.replace('#', '');
    if (hash) navigate(hash);
  });
}

/* ══════════════════════════════════════════════════════════
   DATA FETCHING
   ══════════════════════════════════════════════════════════ */
async function refreshDatabaseList() {
  try {
    S.databaseList = await get('/api/databases');
    updateContextPaneCounts();
  } catch { /* offline */ }
}

async function refreshLedgerStats() {
  try {
    S.ledgerStats = await get('/api/ledger/stats');
    updateContextPaneCounts();
    updateStatusBar();
  } catch { /* offline */ }
}

/* ══════════════════════════════════════════════════════════
   FOCUS ZONE HELPERS
   ══════════════════════════════════════════════════════════ */
function setFocusHeader({ breadcrumb = '', badge = null, actions = '' } = {}) {
  const bc = document.getElementById('focus-breadcrumb');
  const fa = document.getElementById('focus-actions');
  if (bc) bc.innerHTML = breadcrumb;
  if (fa) fa.innerHTML = actions;
}

function setBreadcrumb(...parts) {
  return parts.map((p, i) =>
    i < parts.length - 1
      ? `<span class="breadcrumb-item">${p}</span><span class="breadcrumb-sep"> › </span>`
      : `<span class="breadcrumb-item current">${p}</span>`
  ).join('');
}

function onRouteEnter(routeName) {
  S.activeRoute = routeName;
  localStorage.setItem('b60-route', routeName);
  setActiveSpineIcon(routeName);
  setActiveContextItem(routeName);

  // Loop detector reset
  if (S.loopDetector.route !== routeName) {
    S.loopDetector.route = routeName;
    S.loopDetector.routeEnteredAt = Date.now();
    S.loopDetector.interventionFired = false;
  }
}

/* ══════════════════════════════════════════════════════════
   ROUTE: CANVAS — Macro Architecture Graph
   AACC rationale: system thinkers need the whole map first.
   ══════════════════════════════════════════════════════════ */
async function renderCanvasPage(container) {
  onRouteEnter('canvas');
  setFocusHeader({
    breadcrumb: setBreadcrumb('BABYLON·60', 'Architecture'),
    actions: `
      <span style="font-size:0.6rem;color:var(--dust-faint)">Scroll to zoom · Drag to pan</span>
      <button class="btn btn-icon" id="canvas-fit" title="Fit to screen" style="margin-left:8px">⊞</button>
    `,
  });

  const nodes = [
    { id: 'tauri',    x: 140, y: 80,  type: 'KERNEL',      name: 'Tauri v2 + Rust',   meta: 'CortexLedger · IPC',    status: 'ok' },
    { id: 'fastapi',  x: 300, y: 120, type: 'BACKEND',     name: 'FastAPI',            meta: '8 routes · ASGI',       status: 'ok' },
    { id: 'ledger',   x: 620, y: 80,  type: 'PERSISTENCE', name: 'Master Ledger DB',  meta: 'SHA256 · BFT chain',    status: 'ok' },
    { id: 'ontology', x: 620, y: 220, type: 'PERSISTENCE', name: 'Cortex Ontology',   meta: '1000 vectors · WAL',    status: 'ok' },
    { id: 'telemetry',x: 620, y: 360, type: 'STREAM',      name: 'Telemetry Stream',  meta: 'WebSocket · Live',      status: 'warn' },
    { id: 'swarm',    x: 140, y: 260, type: 'AGENT',       name: 'Swarm Workers',     meta: '0 active',              status: 'idle' },
    { id: 'frontend', x: 300, y: 350, type: 'FRONTEND',    name: 'BABYLON60 IDE',     meta: 'Vite · Vanilla JS',     status: 'ok' },
  ];

  const edges = [
    { from: 'frontend', to: 'tauri' },
    { from: 'frontend', to: 'fastapi' },
    { from: 'tauri',    to: 'ledger' },
    { from: 'tauri',    to: 'ontology' },
    { from: 'fastapi',  to: 'ledger' },
    { from: 'fastapi',  to: 'ontology' },
    { from: 'fastapi',  to: 'telemetry' },
    { from: 'swarm',    to: 'fastapi' },
    { from: 'swarm',    to: 'ledger' },
  ];

  const colors = {
    ok: 'var(--verify)', warn: 'var(--gold)', err: 'var(--break)', idle: 'var(--dust-ghost)',
  };

  container.innerHTML = `
    <div class="canvas-container" id="canvas-main">
      <svg class="canvas-svg" id="canvas-svg">
        <defs>
          <marker id="arrow" markerWidth="8" markerHeight="8" refX="6" refY="3" orient="auto">
            <path d="M0,0 L0,6 L8,3 z" fill="var(--edge)" />
          </marker>
        </defs>
        <g id="canvas-edges"></g>
        <g id="canvas-nodes"></g>
      </svg>
      <div class="canvas-controls">
        <button class="btn btn-icon" id="canvas-zoom-in" title="Zoom in">+</button>
        <button class="btn btn-icon" id="canvas-zoom-out" title="Zoom out">−</button>
        <button class="btn btn-icon" id="canvas-fit-btn" title="Fit all">⊞</button>
      </div>
    </div>
  `;

  const svg = document.getElementById('canvas-svg');
  const edgesG = document.getElementById('canvas-edges');
  const nodesG = document.getElementById('canvas-nodes');
  const canvasEl = document.getElementById('canvas-main');
  if (!svg || !edgesG || !nodesG) return;

  // Draw edges
  edges.forEach(({ from, to }) => {
    const n1 = nodes.find(n => n.id === from);
    const n2 = nodes.find(n => n.id === to);
    if (!n1 || !n2) return;
    const x1 = n1.x + 90, y1 = n1.y + 35;
    const x2 = n2.x, y2 = n2.y + 35;
    const line = document.createElementNS('http://www.w3.org/2000/svg', 'path');
    const mx = (x1 + x2) / 2;
    line.setAttribute('d', `M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`);
    line.setAttribute('stroke', 'var(--edge)');
    line.setAttribute('stroke-width', '1.5');
    line.setAttribute('fill', 'none');
    line.setAttribute('opacity', '0.5');
    line.setAttribute('marker-end', 'url(#arrow)');
    edgesG.appendChild(line);
  });

  // Draw nodes as foreignObjects
  nodes.forEach(node => {
    const fo = document.createElementNS('http://www.w3.org/2000/svg', 'foreignObject');
    fo.setAttribute('x', node.x);
    fo.setAttribute('y', node.y);
    fo.setAttribute('width', '180');
    fo.setAttribute('height', '70');

    const div = document.createElement('div');
    div.className = 'canvas-node-card';
    div.style.position = 'relative';
    div.innerHTML = `
      <div class="canvas-node-type">${node.type}</div>
      <div class="canvas-node-name">${node.name}</div>
      <div class="canvas-node-meta">${node.meta}</div>
      <div class="canvas-node-status" style="background:${colors[node.status] || colors.idle};box-shadow:0 0 5px ${colors[node.status] || colors.idle}"></div>
    `;
    div.addEventListener('click', () => {
      // Micro-tunnel: zoom into this node's view
      if (node.id === 'ledger') navigate('ledger');
      else if (node.id === 'ontology') navigate('databases');
      else if (node.id === 'swarm') navigate('swarm');
      else if (node.id === 'fastapi') navigate('query');
    });
    fo.appendChild(div);
    nodesG.appendChild(fo);
  });

  // Fit button
  document.getElementById('canvas-fit-btn')?.addEventListener('click', () => {
    svg.setAttribute('viewBox', '80 50 700 380');
  });
  svg.setAttribute('viewBox', '80 50 700 380');
}

/* ══════════════════════════════════════════════════════════
   ROUTE: LEDGER — BFT Hash-Chain Inspector
   ══════════════════════════════════════════════════════════ */
let ledgerPage = 1;
const LEDGER_PAGE_SIZE = 50;

async function renderLedgerPage(container) {
  onRouteEnter('ledger');
  setFocusHeader({
    breadcrumb: setBreadcrumb('BABYLON·60', 'BFT Ledger'),
    actions: `<button class="btn btn-verify" id="btn-verify-chain">⚿ Verify Chain</button>`,
  });

  container.innerHTML = `
    <div class="stats-grid slide-in" id="ledger-stats-grid">
      <div class="stat-card">
        <div class="stat-label">Ledger File</div>
        <div class="stat-value lapis" id="stat-db-name" style="font-size:0.85rem">—</div>
        <div class="stat-sub">SQLite WAL</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Entries</div>
        <div class="stat-value gold" id="stat-total-entries">0</div>
        <div class="stat-sub" id="stat-latest-time">—</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Consensus</div>
        <div class="stat-value verify" id="stat-integrity">UNKNOWN</div>
        <div class="stat-sub" id="stat-latest-lamport">Lamport: —</div>
      </div>
    </div>

    <div class="card fade-in" style="margin-bottom:16px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <div class="card-title">Hash Chain Verification</div>
      </div>
      <div class="verify-progress" id="verify-progress-wrap" style="display:none">
        <div class="verify-progress-bar" id="verify-progress-bar"></div>
      </div>
      <div id="chain-visual-grid" class="chain-container">
        <div class="empty-state" style="padding:20px 0">
          <div class="icon">⚿</div>
          <div class="desc">Click "Verify Chain" to map blocks and assert BFT consensus.</div>
        </div>
      </div>
    </div>

    <div class="card fade-in">
      <div class="card-title" style="margin-bottom:10px">Ledger Sequence</div>
      <div style="overflow-x:auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>Seq</th><th>Stream</th><th>Event Type</th>
              <th>Lamport T</th><th>Taint</th><th>Timestamp</th><th>Hash</th>
            </tr>
          </thead>
          <tbody id="ledger-table-body">
            <tr><td colspan="7" class="empty-state" style="text-align:center">Loading...</td></tr>
          </tbody>
        </table>
      </div>
      <div class="pagination">
        <button class="btn" id="btn-ledger-prev" disabled>◀ Prev</button>
        <span style="font-family:var(--font-mono);font-size:0.72rem" id="ledger-page-info">Page 1</span>
        <button class="btn" id="btn-ledger-next" disabled>Next ▶</button>
      </div>
    </div>

    <div id="entry-detail-panel" class="card" style="display:none;position:fixed;top:43px;right:0;width:440px;height:calc(100vh - 71px);border-radius:0;border-left:1px solid var(--edge);z-index:10;flex-direction:column;background:var(--kiln);transform:translateX(100%);transition:transform var(--t-slow)"></div>
  `;

  // Load stats
  try {
    const stats = await get('/api/ledger/stats');
    S.ledgerStats = stats;
    document.getElementById('stat-db-name')?.let?.(el => el.textContent = stats.db_path?.split('/').pop() || 'master_ledger.db');
    const dbNameEl = document.getElementById('stat-db-name');
    if (dbNameEl) dbNameEl.textContent = stats.db_path?.split('/').pop() || 'master_ledger.db';
    const totalEl = document.getElementById('stat-total-entries');
    if (totalEl) totalEl.textContent = stats.total_entries ?? 0;
    const lamportEl = document.getElementById('stat-latest-lamport');
    if (lamportEl) lamportEl.textContent = `Lamport: ${stats.latest_lamport_t ?? '—'}`;
    const timeEl = document.getElementById('stat-latest-time');
    if (timeEl && stats.latest_ts) timeEl.textContent = stats.latest_ts.slice(0, 19);
    updateStatusBar();
  } catch { /* offline */ }

  // Load entries
  await loadLedgerPage(1);

  // Verify chain button — single wired listener
  document.getElementById('btn-verify-chain')?.addEventListener('click', runChainVerification);

  // Pagination
  document.getElementById('btn-ledger-prev')?.addEventListener('click', () => loadLedgerPage(ledgerPage - 1));
  document.getElementById('btn-ledger-next')?.addEventListener('click', () => loadLedgerPage(ledgerPage + 1));
}

async function loadLedgerPage(page) {
  ledgerPage = page;
  const tbody = document.getElementById('ledger-table-body');
  if (!tbody) return;
  try {
    const data = await get(`/api/ledger/entries?page=${page}&page_size=${LEDGER_PAGE_SIZE}`);
    const entries = Array.isArray(data) ? data : (data.entries || []);
    if (entries.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;padding:20px;color:var(--dust-ghost)">No entries</td></tr>`;
      return;
    }
    tbody.innerHTML = entries.map(e => `
      <tr class="${e.is_valid ? 'row-valid' : 'row-invalid'}" data-id="${e.id}" style="cursor:pointer">
        <td class="seq-cell">${e.id}</td>
        <td class="stream-cell">${e.stream_id ?? '—'}</td>
        <td>${e.event_type ?? '—'}</td>
        <td style="color:var(--dust-dim)">${e.lamport_t ?? '—'}</td>
        <td class="hash-cell" style="font-size:0.58rem">${(e.cortex_taint ?? '—').slice(0, 16)}…</td>
        <td class="time-cell">${(e.ts ?? '').slice(0, 19)}</td>
        <td class="hash-cell">${(e.curr_hash ?? '—').slice(0, 12)}…</td>
      </tr>
    `).join('');

    document.getElementById('ledger-page-info').textContent = `Page ${page}`;
    document.getElementById('btn-ledger-prev').disabled = page <= 1;
    document.getElementById('btn-ledger-next').disabled = entries.length < LEDGER_PAGE_SIZE;
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="7" style="text-align:center;color:var(--break)">Error: ${err.message}</td></tr>`;
  }
}

async function runChainVerification() {
  const btn = document.getElementById('btn-verify-chain');
  const grid = document.getElementById('chain-visual-grid');
  const progressWrap = document.getElementById('verify-progress-wrap');
  const progressBar = document.getElementById('verify-progress-bar');
  const integrityEl = document.getElementById('stat-integrity');
  if (!grid) return;

  if (btn) { btn.disabled = true; btn.textContent = '⚙ Verifying...'; }
  if (progressWrap) progressWrap.style.display = 'block';
  setTachometer('working');

  let progress = 0;
  const ticker = setInterval(() => {
    progress = Math.min(progress + 8, 90);
    if (progressBar) progressBar.style.width = `${progress}%`;
  }, 120);

  try {
    const result = await get('/api/ledger/verify');
    clearInterval(ticker);
    if (progressBar) progressBar.style.width = '100%';

    const total = result.total_checked ?? 0;
    const valid = result.valid_count ?? 0;
    const broken = total - valid;
    const ratio = total > 0 ? valid / total : 1;

    grid.innerHTML = '';
    for (let i = 0; i < Math.min(total, 200); i++) {
      const block = document.createElement('div');
      block.className = `chain-block ${i < valid ? '' : 'invalid'}`;
      block.title = `Block ${i + 1}: ${i < valid ? 'VALID' : 'BROKEN'}`;
      grid.appendChild(block);
    }

    if (integrityEl) {
      integrityEl.textContent = ratio === 1 ? 'VERIFIED' : `BROKEN (${broken})`;
      integrityEl.className = `stat-value ${ratio === 1 ? 'verify' : 'break'}`;
    }

    if (ratio === 1) {
      setTachometer('done');
      container.classList.add('reward-active');
      setTimeout(() => container.classList.remove('reward-active'), 1500);
    } else {
      setTachometer('alert');
    }
    setTimeout(() => setTachometer('idle'), 3000);
  } catch (err) {
    clearInterval(ticker);
    grid.innerHTML = `<div style="color:var(--break);font-size:0.72rem;padding:10px">Verification failed: ${err.message}</div>`;
    setTachometer('idle');
  }
  if (btn) { btn.disabled = false; btn.textContent = '⚿ Verify Chain'; }
  if (progressWrap) setTimeout(() => progressWrap.style.display = 'none', 1500);
}

/* ══════════════════════════════════════════════════════════
   ROUTE: DATABASES — Ontology Explorer
   ══════════════════════════════════════════════════════════ */
async function renderDatabasesPage(container) {
  onRouteEnter('databases');
  setFocusHeader({ breadcrumb: setBreadcrumb('BABYLON·60', 'Ontologies') });

  container.innerHTML = `
    <div class="stats-grid slide-in">
      <div class="stat-card">
        <div class="stat-label">SQLite Files</div>
        <div class="stat-value gold" id="db-total-count">${S.databaseList.length || '—'}</div>
        <div class="stat-sub">Discovered</div>
      </div>
    </div>
    <div class="card fade-in">
      <div class="card-title" style="margin-bottom:10px">Ontology Databases</div>
      <table class="data-table">
        <thead><tr><th>Database</th><th>Size</th><th>Type</th><th>Path</th></tr></thead>
        <tbody id="db-table-body"><tr><td colspan="4" style="text-align:center">Loading...</td></tr></tbody>
      </table>
    </div>
    <div class="card fade-in" style="margin-top:14px" id="db-schema-panel" style="display:none">
      <div class="card-title" id="db-schema-title">Schema</div>
      <div id="db-schema-body" style="font-family:var(--font-mono);font-size:0.7rem;color:var(--dust-dim)"></div>
    </div>
  `;

  try {
    const dbs = S.databaseList.length > 0 ? S.databaseList : await get('/api/databases');
    S.databaseList = dbs;
    const tbody = document.getElementById('db-table-body');
    const totalEl = document.getElementById('db-total-count');
    if (totalEl) totalEl.textContent = dbs.length;

    const formatSize = s => s > 1e6 ? `${(s/1e6).toFixed(1)}MB` : `${(s/1024).toFixed(0)}KB`;
    const typeOf = name => {
      if (name.includes('ledger')) return 'LEDGER';
      if (name.includes('ontology')) return 'ONTOLOGY';
      if (name.includes('memory') || name.includes('cortex')) return 'CORTEX';
      if (name.includes('telemetry')) return 'TELEMETRY';
      return 'GENERAL';
    };

    if (tbody) tbody.innerHTML = dbs.map(db => `
      <tr style="cursor:pointer" data-path="${db.path}">
        <td class="stream-cell">${db.name}</td>
        <td class="time-cell">${db.size_bytes ? formatSize(db.size_bytes) : '—'}</td>
        <td><span style="font-size:0.58rem;padding:1px 5px;border-radius:2px;background:var(--tablet-2);color:var(--dust-faint)">${typeOf(db.name)}</span></td>
        <td class="hash-cell" style="font-size:0.6rem;max-width:320px">${db.path}</td>
      </tr>
    `).join('');

    tbody?.querySelectorAll('tr[data-path]').forEach(row => {
      row.addEventListener('click', () => loadDbSchema(row.dataset.path, row.querySelector('.stream-cell')?.textContent));
    });
  } catch (err) {
    const tbody = document.getElementById('db-table-body');
    if (tbody) tbody.innerHTML = `<tr><td colspan="4" style="color:var(--break);text-align:center">${err.message}</td></tr>`;
  }
}

async function loadDbSchema(dbPath, dbName) {
  const panel = document.getElementById('db-schema-panel');
  const title = document.getElementById('db-schema-title');
  const body = document.getElementById('db-schema-body');
  if (!panel || !body) return;
  panel.style.display = 'block';
  if (title) title.textContent = `Schema — ${dbName}`;
  body.textContent = 'Loading schema...';
  try {
    const data = await post('/api/databases/schema', { path: dbPath });
    if (data.tables?.length > 0) {
      body.innerHTML = data.tables.map(t => `
        <div style="margin-bottom:12px">
          <div style="color:var(--lapis-bright);font-weight:700;margin-bottom:4px">▸ ${t.name}</div>
          ${(t.columns || []).map(c => `<div style="padding-left:14px;color:var(--dust-faint)">${c.name} <span style="color:var(--dust-ghost)">${c.type}</span></div>`).join('')}
        </div>
      `).join('');
    } else {
      body.textContent = 'No tables found.';
    }
  } catch (err) {
    body.innerHTML = `<span style="color:var(--break)">${err.message}</span>`;
  }
}

/* ══════════════════════════════════════════════════════════
   ROUTE: QUERY — SQL Console (read-only)
   ══════════════════════════════════════════════════════════ */
async function renderQueryPage(container) {
  onRouteEnter('query');
  setFocusHeader({ breadcrumb: setBreadcrumb('BABYLON·60', 'SQL Console') });

  const defaultDb = S.databaseList[0]?.path || '';
  container.innerHTML = `
    <div class="card slide-in" style="margin-bottom:14px">
      <div style="display:flex;gap:10px;align-items:center;margin-bottom:10px">
        <select class="select" id="query-db-select" style="flex:1">
          ${S.databaseList.map(db =>
            `<option value="${db.path}">${db.name}</option>`
          ).join('')}
        </select>
        <button class="btn btn-primary" id="btn-run-query">▶ Run</button>
        <button class="btn" id="btn-clear-query">Clear</button>
      </div>
      <div class="code-editor">
        <textarea id="query-input" placeholder="SELECT * FROM ledger_entries LIMIT 20;" spellcheck="false"></textarea>
        <div class="code-editor-toolbar">
          <span style="font-size:0.58rem;color:var(--dust-ghost)">Read-only · No DDL/DML</span>
          <span style="font-size:0.58rem;color:var(--dust-ghost)">Shift+Enter to run</span>
        </div>
      </div>
    </div>
    <div id="query-result-card" class="card fade-in" style="display:none">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <div class="card-title" id="query-result-title">Results</div>
        <span id="query-result-meta" style="font-size:0.6rem;color:var(--dust-ghost)"></span>
      </div>
      <div id="query-result-body" style="overflow-x:auto"></div>
    </div>
  `;

  const runQuery = async () => {
    const sql = document.getElementById('query-input')?.value?.trim();
    const dbPath = document.getElementById('query-db-select')?.value;
    if (!sql || !dbPath) return;
    setTachometer('working');
    const resultCard = document.getElementById('query-result-card');
    const resultBody = document.getElementById('query-result-body');
    const resultMeta = document.getElementById('query-result-meta');
    if (resultCard) resultCard.style.display = 'block';
    if (resultBody) resultBody.innerHTML = `<div style="color:var(--dust-faint);padding:10px">Running...</div>`;
    try {
      const t0 = Date.now();
      const result = await post('/api/query', { db_path: dbPath, sql });
      const elapsed = Date.now() - t0;
      const rows = result.rows || [];
      const cols = result.columns || [];
      if (resultMeta) resultMeta.textContent = `${rows.length} rows · ${elapsed}ms`;
      if (resultBody) {
        if (rows.length === 0) {
          resultBody.innerHTML = `<div style="color:var(--dust-faint);padding:10px">No results</div>`;
        } else {
          resultBody.innerHTML = `
            <table class="data-table">
              <thead><tr>${cols.map(c => `<th>${c}</th>`).join('')}</tr></thead>
              <tbody>${rows.map(row =>
                `<tr>${cols.map(c => `<td>${row[c] ?? ''}</td>`).join('')}</tr>`
              ).join('')}</tbody>
            </table>
          `;
        }
      }
      setTachometer('done');
      setTimeout(() => setTachometer('idle'), 2000);
    } catch (err) {
      if (resultBody) resultBody.innerHTML = `<div style="color:var(--break);padding:10px">Error: ${err.message}</div>`;
      setTachometer('idle');
    }
  };

  document.getElementById('btn-run-query')?.addEventListener('click', runQuery);
  document.getElementById('btn-clear-query')?.addEventListener('click', () => {
    const input = document.getElementById('query-input');
    if (input) input.value = '';
    document.getElementById('query-result-card')?.style?.setProperty('display', 'none');
  });
  document.getElementById('query-input')?.addEventListener('keydown', e => {
    if (e.shiftKey && e.key === 'Enter') { e.preventDefault(); runQuery(); }
  });
}

/* ══════════════════════════════════════════════════════════
   ROUTE: SWARM — Agent Telemetry (Devin-style split pane)
   ══════════════════════════════════════════════════════════ */
async function renderSwarmPage(container) {
  onRouteEnter('swarm');
  setFocusHeader({
    breadcrumb: setBreadcrumb('BABYLON·60', 'Agent Swarm'),
    actions: `<span class="focus-badge live">LIVE</span>`,
  });

  const mockAgents = [
    { name: 'MOSKV-1 APEX', status: 'idle', task: 'Awaiting directive', progress: 0 },
    { name: 'BFT Verifier', status: 'done', task: 'Chain verified: 100%', progress: 100 },
    { name: 'Context Indexer', status: 'idle', task: 'Index up to date', progress: 100 },
  ];

  container.innerHTML = `
    <div class="swarm-layout">
      <div class="swarm-terminal">
        <div class="swarm-terminal-header">
          <div class="status-dot" style="width:5px;height:5px;border-radius:50%;background:var(--verify)"></div>
          Agentic Log
        </div>
        <div class="swarm-terminal-body" id="swarm-log-body">
          <div class="swarm-log-line"><span class="swarm-log-time">—:—</span><span class="swarm-log-agent">SYSTEM</span><span class="swarm-log-msg">Waiting for WebSocket stream...</span></div>
        </div>
      </div>
      <div class="swarm-inspector">
        <div class="swarm-inspector-header">Agent State</div>
        <div class="swarm-inspector-body">
          ${mockAgents.map(a => `
            <div class="agent-card">
              <div class="agent-card-header">
                <span class="agent-name">${a.name}</span>
                <span class="agent-status-pill ${a.status}">${a.status.toUpperCase()}</span>
              </div>
              <div class="agent-task">${a.task}</div>
              <div class="agent-progress">
                <div class="agent-progress-fill ${a.status === 'done' ? 'done' : ''}" style="width:${a.progress}%"></div>
              </div>
            </div>
          `).join('')}
        </div>
      </div>
    </div>
  `;

  // Connect to telemetry WebSocket
  if (S.telemetrySocket) { S.telemetrySocket.close?.(); }
  setTachometer('indexing');
  S.telemetrySocket = connectWebSocket('/ws/telemetry', (msg) => {
    appendSwarmLog(msg);
  }, () => {
    setTachometer('idle');
  });
}

function appendSwarmLog(msg) {
  const body = document.getElementById('swarm-log-body');
  if (!body) return;
  const now = new Date().toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  const line = document.createElement('div');
  line.className = 'swarm-log-line';
  const level = msg.level || 'info';
  line.innerHTML = `
    <span class="swarm-log-time">${now}</span>
    <span class="swarm-log-agent">${msg.agent || 'SYSTEM'}</span>
    <span class="swarm-log-msg ${level}">${msg.message || JSON.stringify(msg)}</span>
  `;
  body.appendChild(line);
  body.scrollTop = body.scrollHeight;
  S.swarmLog.push({ time: now, ...msg });
}
