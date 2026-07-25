import { get, post, connectWebSocket } from "./api.js";
import {
  registerRoute,
  navigate,
  rerender,
  getInitialRoute,
} from "./router.js";
const MODES = {
  "2e": {
    key: "2e",
    label: "2E ◐",
    name: "Doble Excepcionalidad (TDAH + AACC)",
    tachometer: true,
    loopGuard: true,
    restoreBanner: true,
    rewards: true,
    spineLabels: false,
  },
  nt: {
    key: "nt",
    label: "NT ○",
    name: "Neurotípico",
    tachometer: false,
    loopGuard: false,
    restoreBanner: false,
    rewards: false,
    spineLabels: true,
  },
};
function mode() {
  return MODES[S.cognitiveMode] || MODES["2e"];
}
function safeParseArray(raw) {
  try {
    const v = JSON.parse(raw || "[]");
    return Array.isArray(v) ? v : [];
  } catch {
    return [];
  }
}
const S = {
  cognitiveMode: localStorage.getItem("b60-cogmode") || "2e",
  contextPaneOpen: true,
  bifocalMode: "micro",
  tachometerState: "idle",
  paletteOpen: false,
  scratchpadOpen: false,
  scratchpadItems: [],
  scratchpadOffline: safeParseArray(
    localStorage.getItem("b60-scratch-offline"),
  ),
  delegationQueue: safeParseArray(localStorage.getItem("b60-delegation")),
  databaseList: [],
  ledgerStats: null,
  lastVerify: null,
  sentinel: null,
  sentinelModalShown: false,
  telemetrySnapshot: null,
  telemetrySocket: null,
  loopDetector: { route: null, routeEnteredAt: 0, interventionFired: false },
  sessionStart: Date.now(),
  activeRoute: null,
  swarmLog: [],
  canvasVB: { x: 80, y: 40, w: 720, h: 400 },
  canvasAbort: null,
};
document.addEventListener("DOMContentLoaded", async () => {
  applyCognitiveMode(S.cognitiveMode, { silent: true });
  setTachometer("indexing");
  setupSpine();
  setupContextPane();
  setupCommandPalette();
  setupScratchpad();
  setupKeyboard();
  setupRouter();
  setupBifocal();
  setupCogModeButton();
  setupLoopDetector();
  await Promise.all([
    refreshDatabaseList(),
    refreshLedgerStats(),
    refreshSentinel(),
    refreshNotes(),
  ]);
  updateStatusBar();
  renderContextPaneContent();
  setTachometer("done");
  if (mode().restoreBanner) {
    showRestoreBanner(localStorage.getItem("b60-route") || "ledger");
  }
  navigate(getInitialRoute());
  setTachometer("idle");
});
function applyCognitiveMode(key, { silent = false } = {}) {
  S.cognitiveMode = MODES[key] ? key : "2e";
  localStorage.setItem("b60-cogmode", S.cognitiveMode);
  document.body.classList.toggle("mode-2e", S.cognitiveMode === "2e");
  document.body.classList.toggle("mode-nt", S.cognitiveMode === "nt");
  const btn = document.getElementById("btn-cogmode");
  if (btn) {
    btn.textContent = mode().label;
    btn.title = `Modo cognitivo: ${mode().name} — click o ⌘⇧E para alternar`;
  }
  if (!silent) {
    setupSpine();
    rerender();
    showAgentModal({
      icon: mode().key === "2e" ? "◐" : "○",
      message: `Modo cognitivo: ${mode().name}. ${
        mode().key === "2e"
          ? "Tacómetro ambiental (carga del agente en visión periférica), loop-guard (freno de hiperfoco) y micro-recompensas activos."
          : "Interfaz estándar: navegación etiquetada, sin intervenciones ni señales ambientales."
      }`,
    });
    setTimeout(hideAgentModal, 3000);
  }
}
function toggleCognitiveMode() {
  applyCognitiveMode(S.cognitiveMode === "2e" ? "nt" : "2e");
}
function setupCogModeButton() {
  let btn = document.getElementById("btn-cogmode");
  if (!btn) {
    const bifocalSeg = document.getElementById("btn-bifocal")?.parentElement;
    if (bifocalSeg) {
      const seg = document.createElement("div");
      seg.className = "status-segment";
      seg.innerHTML = `<button class="status-bifocal" id="btn-cogmode"></button>`;
      bifocalSeg.parentElement.insertBefore(seg, bifocalSeg);
      btn = seg.querySelector("#btn-cogmode");
    }
  }
  if (btn) {
    btn.textContent = mode().label;
    btn.title = `Modo cognitivo: ${mode().name} — click o ⌘⇧E para alternar`;
    btn.addEventListener("click", toggleCognitiveMode);
  }
}
function setTachometer(state) {
  S.tachometerState = state;
  const el = document.getElementById("tachometer");
  if (el) el.className = `tachometer ${state !== "idle" ? state : ""}`;
  const agentSeg = document.getElementById("status-agent-segment");
  if (!agentSeg) return;
  if (state === "working" || state === "indexing") {
    agentSeg.style.display = "flex";
    const txt = document.getElementById("status-agent-text");
    if (txt)
      txt.textContent =
        state === "indexing" ? "Indexing context..." : "Agent working...";
  } else {
    agentSeg.style.display = "none";
  }
}
const SPINE_ROUTES = [
  {
    id: "canvas",
    icon: "⬡",
    label: "Canvas",
    tip: "Architecture Canvas — ABSTRAER  ⌘5",
  },
  {
    id: "ledger",
    icon: "⧉",
    label: "Ledger",
    tip: "BFT Ledger — DETERMINAR  ⌘1",
  },
  {
    id: "databases",
    icon: "⛁",
    label: "Ontologies",
    tip: "Ontologies (explorador SQLite)  ⌘2",
  },
  {
    id: "query",
    icon: "❯_",
    label: "SQL",
    tip: "SQL Console (solo lectura)  ⌘3",
  },
  {
    id: "swarm",
    icon: "⚡",
    label: "Swarm",
    tip: "Agent Swarm (telemetría en vivo)  ⌘4",
  },
  {
    id: "analytics",
    icon: "∿",
    label: "Analytics",
    tip: "Ledger Analytics — DETERMINAR (agregación + BM25)  ⌘7",
  },
  {
    id: "sentinel",
    icon: "⎇",
    label: "Sentinel",
    tip: "Git Sentinel (identidad de repo + delegación real)  ⌘6",
  },
];
function setupSpine() {
  const spine = document.getElementById("spine");
  if (!spine) return;
  spine.innerHTML = "";
  const logo = document.createElement("div");
  logo.className = "spine-logo";
  logo.title = "BABYLON·60 v1.4.0";
  logo.innerHTML = '<div class="spine-logo-dot"></div>';
  spine.appendChild(logo);
  const withLabels = mode().spineLabels;
  SPINE_ROUTES.forEach((r, i) => {
    if (i === 1) {
      const sep = document.createElement("div");
      sep.className = "spine-separator";
      spine.appendChild(sep);
    }
    const btn = document.createElement("button");
    btn.className = "spine-icon";
    btn.dataset.route = r.id;
    if (!withLabels) btn.dataset.tooltip = r.tip;
    btn.setAttribute("aria-label", r.tip);
    btn.innerHTML = withLabels
      ? `<span class="spine-glyph">${escapeHtml(r.icon)}</span><span class="spine-label">${escapeHtml(r.label)}</span>`
      : escapeHtml(r.icon);
    btn.addEventListener("click", () => navigate(r.id));
    spine.appendChild(btn);
  });
  setActiveSpineIcon(S.activeRoute);
}
function setActiveSpineIcon(route) {
  document.querySelectorAll(".spine-icon").forEach((el) => {
    el.classList.toggle("active", el.dataset.route === route);
  });
}
function setupContextPane() {
  document
    .getElementById("btn-collapse-ctx")
    ?.addEventListener("click", toggleContextPane);
  renderContextPaneContent();
}
function toggleContextPane() {
  S.contextPaneOpen = !S.contextPaneOpen;
  const pane = document.getElementById("context-pane");
  const btn = document.getElementById("btn-collapse-ctx");
  if (!pane) return;
  pane.classList.toggle("collapsed", !S.contextPaneOpen);
  if (btn) btn.textContent = S.contextPaneOpen ? "⟨" : "⟩";
}
function renderContextPaneContent() {
  const body = document.getElementById("context-pane-body");
  if (!body) return;
  const dbItems = S.databaseList
    .slice(0, 5)
    .map(
      (db) => `
    <div class="ctx-item depth-1" data-goto-db="${escapeHtml(db.name)}">
      <span class="ctx-item-icon" style="font-size:0.6rem">●</span>
      <span class="ctx-item-label" style="font-size:0.65rem">${escapeHtml(db.name)}</span>
      <span class="ctx-item-badge">RO</span>
    </div>
  `,
    )
    .join("");
  const sentinelBadge = S.sentinel?.warnings?.some((w) => w.level === "red")
    ? '<span class="ctx-item-badge break">!</span>'
    : S.sentinel?.warnings?.length
      ? '<span class="ctx-item-badge gold">△</span>'
      : '<span class="ctx-item-badge verify">ok</span>';
  body.innerHTML = `
    <div class="ctx-section">
      <div class="ctx-section-label">Inspector</div>
      <div class="ctx-item" data-route="canvas">
        <span class="ctx-item-icon">⬡</span>
        <span class="ctx-item-label">Architecture</span>
        <span class="ctx-item-badge verify">live</span>
      </div>
      <div class="ctx-item" data-route="ledger">
        <span class="ctx-item-icon">⧉</span>
        <span class="ctx-item-label">BFT Ledger</span>
        <span class="ctx-item-badge gold" id="ctx-ledger-count">${S.ledgerStats?.entries ?? "—"}</span>
      </div>
      <div class="ctx-item" data-route="databases">
        <span class="ctx-item-icon">⛁</span>
        <span class="ctx-item-label">Ontologies</span>
        <span class="ctx-item-badge gold" id="ctx-db-count">${S.databaseList.length || "—"}</span>
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
        <span class="ctx-item-badge lapis" style="color:var(--lapis-bright)">ws</span>
      </div>
      <div class="ctx-item" data-route="sentinel">
        <span class="ctx-item-icon">⎇</span>
        <span class="ctx-item-label">Git Sentinel</span>
        ${sentinelBadge}
      </div>
    </div>
    <div class="ctx-section">
      <div class="ctx-section-label">Scratchpad</div>
      <div id="ctx-scratch-preview" style="padding:4px 12px; font-size:0.65rem; color:var(--dust-faint);">
        ${
          S.scratchpadItems.length + S.scratchpadOffline.length === 0
            ? '<span style="color:var(--dust-ghost)">No notes yet</span>'
            : `<span style="color:var(--dust-dim)">${S.scratchpadItems.length + S.scratchpadOffline.length} nota${S.scratchpadItems.length + S.scratchpadOffline.length !== 1 ? "s" : ""} en el ledger${S.scratchpadOffline.length ? ` <span style="color:var(--gold)">(${S.scratchpadOffline.length} offline)</span>` : ""}</span>`
        }
      </div>
    </div>
    <div class="ctx-section">
      <div class="ctx-section-label">Databases</div>
      ${dbItems || '<div style="padding:4px 12px;font-size:0.62rem;color:var(--dust-ghost)">No .db discovered</div>'}
    </div>
  `;
  body.querySelectorAll(".ctx-item[data-route]").forEach((el) => {
    el.addEventListener("click", () => navigate(el.dataset.route));
  });
  body.querySelectorAll(".ctx-item[data-goto-db]").forEach((el) => {
    el.addEventListener("click", () => navigate("databases"));
  });
}
function updateContextPaneCounts() {
  const dbCount = document.getElementById("ctx-db-count");
  if (dbCount) dbCount.textContent = S.databaseList.length || "—";
  const ledgerCount = document.getElementById("ctx-ledger-count");
  if (ledgerCount) ledgerCount.textContent = S.ledgerStats?.entries ?? "—";
}
function setActiveContextItem(route) {
  document.querySelectorAll(".ctx-item[data-route]").forEach((el) => {
    el.classList.toggle("active", el.dataset.route === route);
  });
}
function updateStatusBar() {
  const connDot = document.getElementById("status-conn-dot");
  const connText = document.getElementById("status-conn-text");
  const dbCount = document.getElementById("status-db-count");
  const ledgerEntries = document.getElementById("status-ledger-entries");
  const lamport = document.getElementById("status-lamport");
  const online = S.ledgerStats !== null || S.databaseList.length > 0;
  if (connDot) connDot.className = online ? "status-dot" : "status-dot error";
  if (connText) connText.textContent = online ? "CONNECTED" : "OFFLINE";
  if (dbCount) dbCount.textContent = S.databaseList.length || "—";
  if (ledgerEntries) ledgerEntries.textContent = S.ledgerStats?.entries ?? "—";
  if (lamport)
    lamport.textContent =
      S.ledgerStats?.latest?.lamport_t != null
        ? `L:${S.ledgerStats.latest.lamport_t}`
        : "—";
  updateRepoSegment();
}
function updateRepoSegment() {
  let seg = document.getElementById("status-repo-segment");
  if (!seg) {
    const bar = document.getElementById("status-bar");
    const firstSeg = bar?.querySelector(".status-segment");
    if (!bar || !firstSeg) return;
    seg = document.createElement("div");
    seg.className = "status-segment";
    seg.id = "status-repo-segment";
    seg.style.cursor = "pointer";
    seg.innerHTML = `<span style="color:var(--dust-ghost)">REPO</span><span class="status-value" id="status-repo-text">—</span>`;
    firstSeg.after(seg);
    seg.addEventListener("click", () => navigate("sentinel"));
  }
  const txt = document.getElementById("status-repo-text");
  if (!txt) return;
  const s = S.sentinel;
  if (!s) {
    txt.textContent = "—";
    return;
  }
  const red = s.warnings?.some((w) => w.level === "red");
  const amber = !red && s.warnings?.length > 0;
  txt.textContent = `${s.repo_name}${s.branch ? " @" + s.branch : ""}${s.head ? " · " + s.head : ""}${red ? " ⚠" : amber ? " △" : " ✓"}`;
  txt.style.color = red
    ? "var(--break)"
    : amber
      ? "var(--gold)"
      : "var(--verify)";
  seg.title = red
    ? "LINAJE NO CANÓNICO — abre Git Sentinel"
    : amber
      ? "Avisos de linaje — abre Git Sentinel"
      : `Linaje canónico verificado (${s.commit_count ?? "—"} commits)`;
}
async function refreshSentinel() {
  try {
    S.sentinel = await get("/api/sentinel/status");
    updateRepoSegment();
    const reds = S.sentinel.warnings?.filter((w) => w.level === "red") || [];
    if (reds.length > 0 && !S.sentinelModalShown) {
      S.sentinelModalShown = true;
      showAgentModal({
        icon: "⚠",
        message: `GIT SENTINEL: ${reds[0].msg}`,
        actions: [
          {
            label: "Abrir Sentinel",
            primary: true,
            fn: () => {
              hideAgentModal();
              navigate("sentinel");
            },
          },
          { label: "Entendido", fn: hideAgentModal },
        ],
      });
    }
  } catch {}
}
function setupBifocal() {
  document
    .getElementById("btn-bifocal")
    ?.addEventListener("click", toggleBifocal);
}
function toggleBifocal() {
  S.bifocalMode = S.bifocalMode === "micro" ? "macro" : "micro";
  document.body.classList.toggle("macro-mode", S.bifocalMode === "macro");
  document.body.classList.toggle("micro-mode", S.bifocalMode === "micro");
  const btn = document.getElementById("btn-bifocal");
  if (btn) btn.textContent = S.bifocalMode === "macro" ? "MACRO ⊞" : "MICRO ⊞";
  if (S.bifocalMode === "macro") navigate("canvas");
}
const PALETTE_COMMANDS = [
  {
    icon: "⬡",
    label: "Architecture Canvas",
    desc: "ABSTRAER: ver el sistema completo",
    shortcut: "⌘5",
    action: () => navigate("canvas"),
  },
  {
    icon: "⧉",
    label: "BFT Ledger",
    desc: "DETERMINAR: inspector de cadena de hashes",
    shortcut: "⌘1",
    action: () => navigate("ledger"),
  },
  {
    icon: "⛁",
    label: "Ontologies",
    desc: "Explorador SQLite (solo lectura)",
    shortcut: "⌘2",
    action: () => navigate("databases"),
  },
  {
    icon: "❯_",
    label: "SQL Console",
    desc: "Consultas read-only contra cualquier .db",
    shortcut: "⌘3",
    action: () => navigate("query"),
  },
  {
    icon: "⚡",
    label: "Agent Swarm",
    desc: "Telemetría en vivo (push WS, sin polling)",
    shortcut: "⌘4",
    action: () => navigate("swarm"),
  },
  {
    icon: "∿",
    label: "Ledger Analytics",
    desc: "DETERMINAR: agregación + búsqueda BM25 del ledger",
    shortcut: "⌘7",
    action: () => navigate("analytics"),
  },
  {
    icon: "⎇",
    label: "Git Sentinel",
    desc: "Identidad de repo + delegación real (commit/push)",
    shortcut: "⌘6",
    action: () => navigate("sentinel"),
  },
  {
    icon: "⌕",
    label: "Search Ledger",
    desc: "BM25 léxico sobre payloads y taints",
    shortcut: "",
    action: () => {
      navigate("analytics");
      setTimeout(
        () => document.getElementById("ledger-search-input")?.focus(),
        300,
      );
    },
  },
  {
    icon: "⚿",
    label: "Verify Chain Integrity",
    desc: "Recomputar SHA3-256 de toda la cadena",
    shortcut: "",
    action: () => {
      navigate("ledger");
      setTimeout(
        () => document.getElementById("btn-verify-chain")?.click(),
        400,
      );
    },
  },
  {
    icon: "◐",
    label: "Toggle Cognitive Mode",
    desc: "Neurotípico ○ ↔ Doble Excepcionalidad ◐ (TDAH+AACC)",
    shortcut: "⌘⇧E",
    action: toggleCognitiveMode,
  },
  {
    icon: "⟨",
    label: "Toggle Context Pane",
    desc: "Mostrar / ocultar mapa semántico",
    shortcut: "⌘B",
    action: toggleContextPane,
  },
  {
    icon: "⊞",
    label: "Toggle Macro / Micro",
    desc: "Alternar vista bifocal",
    shortcut: "⌘M",
    action: toggleBifocal,
  },
  {
    icon: "◎",
    label: "Open Scratchpad",
    desc: "Volcar un pensamiento sin perder foco",
    shortcut: "⌘⇧Space",
    action: () => toggleScratchpad(true),
  },
];
let paletteSelected = 0;
let paletteFiltered = [...PALETTE_COMMANDS];
function setupCommandPalette() {
  const overlay = document.getElementById("palette-overlay");
  const input = document.getElementById("palette-input");
  if (!overlay || !input) return;
  overlay.addEventListener("click", (e) => {
    if (e.target === overlay) closePalette();
  });
  input.addEventListener("input", () => filterPalette(input.value));
  input.addEventListener("keydown", handlePaletteKey);
}
function openPalette() {
  S.paletteOpen = true;
  const overlay = document.getElementById("palette-overlay");
  const input = document.getElementById("palette-input");
  if (!overlay || !input) return;
  overlay.classList.add("visible");
  overlay.setAttribute("aria-hidden", "false");
  input.value = "";
  paletteSelected = 0;
  paletteFiltered = [...PALETTE_COMMANDS];
  renderPaletteResults();
  setTimeout(() => input.focus(), 50);
}
function closePalette() {
  S.paletteOpen = false;
  const overlay = document.getElementById("palette-overlay");
  if (overlay) {
    overlay.classList.remove("visible");
    overlay.setAttribute("aria-hidden", "true");
  }
}
function filterPalette(query) {
  const q = query.toLowerCase().trim();
  paletteSelected = 0;
  paletteFiltered = !q
    ? [...PALETTE_COMMANDS]
    : PALETTE_COMMANDS.filter(
        (c) =>
          c.label.toLowerCase().includes(q) || c.desc.toLowerCase().includes(q),
      );
  renderPaletteResults(q);
}
function escapeRegExp(s) {
  return s.replace(/[.*+?^${}()|[\]\\]/g, "\\$&");
}
function renderPaletteResults(query = "") {
  const container = document.getElementById("palette-results");
  if (!container) return;
  if (paletteFiltered.length === 0) {
    container.innerHTML = `<div class="palette-empty">No commands match "<strong>${escapeHtml(query)}</strong>"</div>`;
    return;
  }
  container.innerHTML = `
    <div class="palette-section-label">Commands</div>
    ${paletteFiltered
      .map((cmd, i) => {
        const safeLabel = escapeHtml(cmd.label);
        const safeDesc = escapeHtml(cmd.desc);
        const safeShortcut = escapeHtml(cmd.shortcut);
        const labelHighlighted = query
          ? safeLabel.replace(
              new RegExp(`(${escapeRegExp(escapeHtml(query))})`, "gi"),
              '<span class="palette-match">$1</span>',
            )
          : safeLabel;
        return `
        <div class="palette-item ${i === paletteSelected ? "selected" : ""}" data-index="${i}">
          <span class="palette-item-icon">${escapeHtml(cmd.icon)}</span>
          <span class="palette-item-label">${labelHighlighted}</span>
          <span class="palette-item-desc">${safeDesc}</span>
          ${cmd.shortcut ? `<span class="palette-item-shortcut">${safeShortcut}</span>` : ""}
        </div>
      `;
      })
      .join("")}
  `;
  container.querySelectorAll(".palette-item").forEach((el) => {
    el.addEventListener("click", () => {
      const idx = parseInt(el.dataset.index);
      if (paletteFiltered[idx]) {
        paletteFiltered[idx].action();
        closePalette();
      }
    });
    el.addEventListener("mouseenter", () => {
      paletteSelected = parseInt(el.dataset.index);
      container
        .querySelectorAll(".palette-item")
        .forEach((e, i) =>
          e.classList.toggle("selected", i === paletteSelected),
        );
    });
  });
}
function handlePaletteKey(e) {
  if (e.key === "Escape") {
    closePalette();
    return;
  }
  if (e.key === "ArrowDown") {
    e.preventDefault();
    paletteSelected = Math.min(paletteSelected + 1, paletteFiltered.length - 1);
    renderPaletteResults(document.getElementById("palette-input")?.value || "");
  }
  if (e.key === "ArrowUp") {
    e.preventDefault();
    paletteSelected = Math.max(paletteSelected - 1, 0);
    renderPaletteResults(document.getElementById("palette-input")?.value || "");
  }
  if (e.key === "Enter") {
    e.preventDefault();
    if (paletteFiltered[paletteSelected]) {
      paletteFiltered[paletteSelected].action();
      closePalette();
    }
  }
}
function setupScratchpad() {
  const modal = document.getElementById("scratchpad-modal");
  const input = document.getElementById("scratchpad-input");
  if (!modal || !input) return;
  document
    .getElementById("scratchpad-save")
    ?.addEventListener("click", saveScratchpadItem);
  document
    .getElementById("scratchpad-close")
    ?.addEventListener("click", () => toggleScratchpad(false));
  input.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      saveScratchpadItem();
    }
    if (e.key === "Escape") toggleScratchpad(false);
  });
  renderScratchpadItems();
}
function toggleScratchpad(force) {
  const modal = document.getElementById("scratchpad-modal");
  const input = document.getElementById("scratchpad-input");
  if (!modal) return;
  S.scratchpadOpen = force !== undefined ? force : !S.scratchpadOpen;
  modal.classList.toggle("visible", S.scratchpadOpen);
  modal.setAttribute("aria-hidden", String(!S.scratchpadOpen));
  if (S.scratchpadOpen && input) setTimeout(() => input.focus(), 60);
}
async function refreshNotes() {
  const pending = [...S.scratchpadOffline];
  for (const item of pending) {
    try {
      await post("/api/cortex/notes", {
        text: item.text,
        route: item.route || "",
      });
      S.scratchpadOffline = S.scratchpadOffline.filter((i) => i.id !== item.id);
    } catch {
      break;
    }
  }
  localStorage.setItem(
    "b60-scratch-offline",
    JSON.stringify(S.scratchpadOffline),
  );
  try {
    const data = await get("/api/cortex/notes?limit=50");
    S.scratchpadItems = data.notes || [];
  } catch {}
  renderScratchpadItems();
  renderContextPaneContent();
}
async function saveScratchpadItem() {
  const input = document.getElementById("scratchpad-input");
  if (!input || !input.value.trim()) return;
  const text = input.value.trim();
  input.value = "";
  try {
    await post("/api/cortex/notes", { text, route: S.activeRoute || "" });
    await refreshNotes();
  } catch {
    S.scratchpadOffline.unshift({
      id: Date.now(),
      text,
      route: S.activeRoute || "",
      offline: true,
    });
    if (S.scratchpadOffline.length > 30) S.scratchpadOffline.pop();
    localStorage.setItem(
      "b60-scratch-offline",
      JSON.stringify(S.scratchpadOffline),
    );
    renderScratchpadItems();
    renderContextPaneContent();
  }
  if (mode().rewards) {
    setTachometer("done");
    setTimeout(() => setTachometer("idle"), 2000);
  }
}
function renderScratchpadItems() {
  const container = document.getElementById("scratchpad-items");
  if (!container) return;
  const off = S.scratchpadOffline;
  const srv = S.scratchpadItems;
  if (off.length === 0 && srv.length === 0) {
    container.innerHTML = "";
    return;
  }
  const fmtTime = (ms) =>
    new Date(ms).toLocaleTimeString("en-GB", {
      hour: "2-digit",
      minute: "2-digit",
    });
  container.innerHTML = [
    ...off.map(
      (item) => `
      <div class="scratchpad-item">
        <span class="scratchpad-item-time" style="color:var(--gold)" title="pendiente de sellar en el ledger">⚡off</span>
        <span class="scratchpad-item-text">${escapeHtml(item.text)}</span>
        <span class="scratchpad-item-del" data-del-off="${item.id}" title="Descartar (aún no sellada)">✕</span>
      </div>`,
    ),
    ...srv.map(
      (item) => `
      <div class="scratchpad-item">
        <span class="scratchpad-item-time" title="sellada en CortexLedger · ${escapeHtml(item.hash || "")}${item.route ? " · nació en " + escapeHtml(item.route) : ""}">${fmtTime(item.created_at)}</span>
        <span class="scratchpad-item-text">${escapeHtml(item.text)}</span>
        <span class="scratchpad-item-del" data-del-ev="${escapeHtml(item.event_id)}" title="Tombstone (el ledger no olvida; la vista sí)">✕</span>
      </div>`,
    ),
  ].join("");
  container.querySelectorAll("[data-del-off]").forEach((el) => {
    el.addEventListener("click", (e) => {
      e.stopPropagation();
      const id = parseInt(el.dataset.delOff);
      S.scratchpadOffline = S.scratchpadOffline.filter((i) => i.id !== id);
      localStorage.setItem(
        "b60-scratch-offline",
        JSON.stringify(S.scratchpadOffline),
      );
      renderScratchpadItems();
      renderContextPaneContent();
    });
  });
  container.querySelectorAll("[data-del-ev]").forEach((el) => {
    el.addEventListener("click", async (e) => {
      e.stopPropagation();
      try {
        await post(`/api/cortex/notes/${el.dataset.delEv}/delete`, {});
      } catch {}
      await refreshNotes();
    });
  });
}
function showAgentModal({ icon = "⬡", message, actions = [] }) {
  const modal = document.getElementById("agent-modal");
  const iconEl = document.getElementById("agent-modal-icon");
  const msgEl = document.getElementById("agent-modal-msg");
  const actionsEl = document.getElementById("agent-modal-actions");
  if (!modal || !msgEl || !actionsEl) return;
  if (iconEl) iconEl.textContent = icon;
  msgEl.textContent = message;
  const finalActions =
    actions.length > 0
      ? actions
      : [{ label: "Got it", fn: hideAgentModal, primary: true }];
  actionsEl.innerHTML = finalActions
    .map(
      (a, i) =>
        `<button class="btn ${a.primary ? "btn-primary" : ""}" style="font-size:0.65rem" data-action-idx="${i}">${escapeHtml(a.label)}</button>`,
    )
    .join("");
  actionsEl.querySelectorAll("button").forEach((btn) => {
    btn.addEventListener("click", () =>
      finalActions[parseInt(btn.dataset.actionIdx)]?.fn?.(),
    );
  });
  modal.classList.add("visible");
  modal.setAttribute("aria-hidden", "false");
  if (mode().tachometer) setTachometer("alert");
}
function hideAgentModal() {
  const modal = document.getElementById("agent-modal");
  if (modal) {
    modal.classList.remove("visible");
    modal.setAttribute("aria-hidden", "true");
  }
  setTachometer("idle");
}
function setupLoopDetector() {
  setInterval(
    () => {
      if (!mode().loopGuard) return;
      if (!S.loopDetector.route || S.loopDetector.interventionFired) return;
      const elapsed = Date.now() - S.loopDetector.routeEnteredAt;
      if (elapsed > 25 * 60 * 1000) {
        S.loopDetector.interventionFired = true;
        const route = S.loopDetector.route;
        showAgentModal({
          icon: "⏱",
          message: `Llevas más de 25 minutos en ${route.toUpperCase()}. El foco profundo es bueno — ¿quieres dar un paso atrás y ver el sistema completo?`,
          actions: [
            {
              label: "Ver Arquitectura",
              primary: true,
              fn: () => {
                hideAgentModal();
                navigate("canvas");
              },
            },
            { label: "Sigo aquí", fn: hideAgentModal },
            {
              label: "Volcar idea →",
              fn: () => {
                hideAgentModal();
                toggleScratchpad(true);
              },
            },
          ],
        });
      }
    },
    2 * 60 * 1000,
  );
}
async function showRestoreBanner(lastRoute) {
  const banner = document.getElementById("restore-banner");
  const msg = document.getElementById("restore-msg");
  const points = document.getElementById("restore-points");
  const dismiss = document.getElementById("restore-dismiss");
  if (!banner || !msg) return;
  const routeLabels = {
    ledger: "BFT Ledger",
    databases: "Ontologies",
    query: "SQL Console",
    swarm: "Agent Swarm",
    canvas: "Architecture Canvas",
    sentinel: "Git Sentinel",
    analytics: "Ledger Analytics",
  };
  let bullets = null;
  let jumpRoute = lastRoute;
  try {
    const r = await get("/api/cortex/resume");
    bullets = r.bullets || null;
    if (r.suggested_route && routeLabels[r.suggested_route])
      jumpRoute = r.suggested_route;
    if (bullets)
      bullets.push(`Retomar en ${routeLabels[jumpRoute] || jumpRoute} →`);
  } catch {}
  if (!bullets) {
    bullets = [
      `Last active: ${routeLabels[lastRoute] || lastRoute}`,
      `${S.databaseList.length || "—"} databases available`,
      S.ledgerStats?.entries != null
        ? `${S.ledgerStats.entries} ledger entries`
        : "Ledger loading...",
      S.sentinel
        ? `repo ${S.sentinel.repo_name}@${S.sentinel.branch ?? "—"}`
        : "",
    ].filter(Boolean);
  }
  msg.textContent = "Contexto restaurado · ";
  if (points) {
    points.innerHTML = bullets
      .map(
        (b, i) =>
          `<span class="restore-point" ${i === bullets.length - 1 && routeLabels[jumpRoute] ? `data-jump="${escapeHtml(jumpRoute)}" style="cursor:pointer;color:var(--lapis-bright)"` : ""}>${escapeHtml(b)}</span>`,
      )
      .join("");
    points.querySelector("[data-jump]")?.addEventListener("click", () => {
      navigate(points.querySelector("[data-jump]").dataset.jump);
      banner.style.display = "none";
    });
  }
  banner.style.display = "flex";
  dismiss?.addEventListener("click", () => {
    banner.style.display = "none";
  });
  setTimeout(() => {
    banner.style.display = "none";
  }, 14000);
}
function setupKeyboard() {
  const routeKeys = {
    1: "ledger",
    2: "databases",
    3: "query",
    4: "swarm",
    5: "canvas",
    6: "sentinel",
    7: "analytics",
  };
  window.addEventListener("keydown", (e) => {
    const mod = e.metaKey || e.ctrlKey;
    if (mod && e.key === "k" && !e.shiftKey) {
      e.preventDefault();
      S.paletteOpen ? closePalette() : openPalette();
      return;
    }
    if (mod && e.shiftKey && e.code === "Space") {
      e.preventDefault();
      toggleScratchpad();
      return;
    }
    if (mod && e.shiftKey && (e.key === "e" || e.key === "E")) {
      e.preventDefault();
      toggleCognitiveMode();
      return;
    }
    if (mod && e.key === "b" && !e.shiftKey) {
      e.preventDefault();
      toggleContextPane();
      return;
    }
    if (mod && e.key === "m" && !e.shiftKey) {
      e.preventDefault();
      toggleBifocal();
      return;
    }
    if (mod && routeKeys[e.key]) {
      e.preventDefault();
      navigate(routeKeys[e.key]);
      return;
    }
    if (e.key === "Escape") {
      if (S.paletteOpen) {
        closePalette();
        return;
      }
      if (S.scratchpadOpen) {
        toggleScratchpad(false);
        return;
      }
      closeEntryDetail();
    }
  });
}
function setupRouter() {
  registerRoute("canvas", renderCanvasPage);
  registerRoute("ledger", renderLedgerPage);
  registerRoute("databases", renderDatabasesPage);
  registerRoute("query", renderQueryPage);
  registerRoute("swarm", renderSwarmPage);
  registerRoute("analytics", renderAnalyticsPage);
  registerRoute("sentinel", renderSentinelPage);
  window.addEventListener("hashchange", () => {
    const rawHash = window.location.hash.replace("#", "");
    const hash = rawHash.replace(/[^a-zA-Z0-9_-]/g, "");
    if (hash) navigate(hash);
  });
}
async function refreshDatabaseList() {
  try {
    S.databaseList = await get("/api/databases");
    updateContextPaneCounts();
  } catch {}
}
async function refreshLedgerStats() {
  try {
    S.ledgerStats = await get("/api/ledger/stats");
    updateContextPaneCounts();
    updateStatusBar();
  } catch {}
}
function setFocusHeader({ breadcrumb = "", actions = "" } = {}) {
  const bc = document.getElementById("focus-breadcrumb");
  const fa = document.getElementById("focus-actions");
  if (bc) bc.innerHTML = breadcrumb;
  if (fa) fa.innerHTML = actions;
}
function setBreadcrumb(...parts) {
  return parts
    .map((p, i) =>
      i < parts.length - 1
        ? `<span class="breadcrumb-item">${escapeHtml(p)}</span><span class="breadcrumb-sep"> › </span>`
        : `<span class="breadcrumb-item current">${escapeHtml(p)}</span>`,
    )
    .join("");
}
function onRouteEnter(routeName) {
  S.activeRoute = routeName;
  localStorage.setItem("b60-route", routeName);
  setActiveSpineIcon(routeName);
  setActiveContextItem(routeName);
  closeEntryDetail();
  if (routeName !== "swarm" && S.telemetrySocket) {
    S.telemetrySocket.close();
    S.telemetrySocket = null;
  }
  if (S.loopDetector.route !== routeName) {
    S.loopDetector.route = routeName;
    S.loopDetector.routeEnteredAt = Date.now();
    S.loopDetector.interventionFired = false;
  }
}
function escapeHtml(s) {
  return String(s ?? "")
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;");
}
/* ══════════════════════════════════════════════════════════
   ROUTE: CANVAS — ABSTRAER (macro con métricas reales)
   ══════════════════════════════════════════════════════════ */
async function renderCanvasPage(container) {
  onRouteEnter("canvas");
  setFocusHeader({
    breadcrumb: setBreadcrumb(
      "BABYLON·60",
      "Architecture — ABSTRAER (ver el todo antes que la parte)",
    ),
    actions: `<span style="font-size:0.6rem;color:var(--dust-faint)">Scroll = zoom · Drag = pan</span>`,
  });
  try {
    S.telemetrySnapshot = await get("/api/telemetry/snapshot");
  } catch {
    /* offline */
  }
  const snap = S.telemetrySnapshot;
  const dbCount = S.databaseList.length;
  const ledgerEntries = S.ledgerStats?.entries ?? "—";
  const totalMb =
    snap?.total_db_size_mb != null ? `${snap.total_db_size_mb}MB` : "—";
  const sent = S.sentinel;
  const gitMeta = sent?.is_git
    ? `${sent.repo_name}@${sent.branch ?? "—"} · ${sent.head ?? "—"}`
    : "no git";
  const gitStatus = sent?.warnings?.some((w) => w.level === "red")
    ? "err"
    : sent?.warnings?.length
      ? "warn"
      : "ok";
  const nodes = [
    {
      id: "frontend",
      x: 140,
      y: 350,
      type: "FRONTEND",
      name: "BABYLON60 IDE",
      meta: `Vite · modo ${mode().key.toUpperCase()}`,
      status: "ok",
    },
    {
      id: "fastapi",
      x: 300,
      y: 120,
      type: "BACKEND",
      name: "FastAPI",
      meta: "14 endpoints · ASGI",
      status: "ok",
    },
    {
      id: "ledger",
      x: 620,
      y: 80,
      type: "PERSISTENCE",
      name: "Master Ledger",
      meta: `${ledgerEntries} entries · SHA3-256 (huella criptográfica)`,
      status: S.ledgerStats?.exists ? "ok" : "err",
      goto: "ledger",
    },
    {
      id: "ontology",
      x: 620,
      y: 220,
      type: "PERSISTENCE",
      name: "Ontology DBs",
      meta: `${dbCount} DBs · ${totalMb} · RO`,
      status: dbCount > 0 ? "ok" : "warn",
      goto: "databases",
    },
    {
      id: "telemetry",
      x: 620,
      y: 350,
      type: "STREAM",
      name: "Telemetry Stream",
      meta: snap ? "WS push 2s (sin polling)" : "offline",
      status: snap ? "ok" : "warn",
      goto: "swarm",
    },
    {
      id: "git",
      x: 140,
      y: 240,
      type: "SENTINEL",
      name: "Git Sentinel",
      meta: gitMeta,
      status: gitStatus,
      goto: "sentinel",
    },
  ];
  const edges = [
    { from: "frontend", to: "fastapi" },
    { from: "fastapi", to: "ledger" },
    { from: "fastapi", to: "ontology" },
    { from: "fastapi", to: "telemetry" },
    { from: "git", to: "fastapi" },
  ];
  const colors = {
    ok: "var(--verify)",
    warn: "var(--gold)",
    err: "var(--break)",
    idle: "var(--dust-ghost)",
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
  const svg = document.getElementById("canvas-svg");
  const edgesG = document.getElementById("canvas-edges");
  const nodesG = document.getElementById("canvas-nodes");
  if (!svg || !edgesG || !nodesG) return;
  edges.forEach(({ from, to }) => {
    const n1 = nodes.find((n) => n.id === from);
    const n2 = nodes.find((n) => n.id === to);
    if (!n1 || !n2) return;
    const x1 = n1.x + 90,
      y1 = n1.y + 35;
    const x2 = n2.x,
      y2 = n2.y + 35;
    const line = document.createElementNS("http://www.w3.org/2000/svg", "path");
    const mx = (x1 + x2) / 2;
    line.setAttribute("d", `M${x1},${y1} C${mx},${y1} ${mx},${y2} ${x2},${y2}`);
    line.setAttribute("stroke", "var(--edge)");
    line.setAttribute("stroke-width", "1.5");
    line.setAttribute("fill", "none");
    line.setAttribute("opacity", "0.5");
    line.setAttribute("marker-end", "url(#arrow)");
    edgesG.appendChild(line);
  });
  nodes.forEach((node) => {
    const fo = document.createElementNS(
      "http://www.w3.org/2000/svg",
      "foreignObject",
    );
    fo.setAttribute("x", node.x);
    fo.setAttribute("y", node.y);
    fo.setAttribute("width", "195");
    fo.setAttribute("height", "76");
    const div = document.createElement("div");
    div.className = "canvas-node-card";
    div.style.position = "relative";
    div.innerHTML = `
      <div class="canvas-node-type">${escapeHtml(node.type)}</div>
      <div class="canvas-node-name">${escapeHtml(node.name)}</div>
      <div class="canvas-node-meta">${escapeHtml(node.meta)}</div>
      <div class="canvas-node-status" style="background:${colors[node.status] || colors.idle};box-shadow:0 0 5px ${colors[node.status] || colors.idle}"></div>
    `;
    if (node.goto) div.addEventListener("click", () => navigate(node.goto));
    fo.appendChild(div);
    nodesG.appendChild(fo);
  });
  const applyVB = () =>
    svg.setAttribute(
      "viewBox",
      `${S.canvasVB.x} ${S.canvasVB.y} ${S.canvasVB.w} ${S.canvasVB.h}`,
    );
  const fit = () => {
    S.canvasVB = { x: 80, y: 40, w: 720, h: 400 };
    applyVB();
  };
  fit();
  const zoom = (factor) => {
    const vb = S.canvasVB;
    const cx = vb.x + vb.w / 2,
      cy = vb.y + vb.h / 2;
    vb.w = Math.max(200, Math.min(2000, vb.w * factor));
    vb.h = Math.max(110, Math.min(1100, vb.h * factor));
    vb.x = cx - vb.w / 2;
    vb.y = cy - vb.h / 2;
    applyVB();
  };
  document
    .getElementById("canvas-zoom-in")
    ?.addEventListener("click", () => zoom(1 / 1.2));
  document
    .getElementById("canvas-zoom-out")
    ?.addEventListener("click", () => zoom(1.2));
  document.getElementById("canvas-fit-btn")?.addEventListener("click", fit);
  svg.addEventListener(
    "wheel",
    (e) => {
      e.preventDefault();
      zoom(e.deltaY > 0 ? 1.1 : 1 / 1.1);
    },
    { passive: false },
  );
  if (S.canvasAbort) S.canvasAbort.abort();
  S.canvasAbort = new AbortController();
  const sig = S.canvasAbort.signal;
  let dragging = false,
    lastX = 0,
    lastY = 0;
  svg.addEventListener("pointerdown", (e) => {
    dragging = true;
    lastX = e.clientX;
    lastY = e.clientY;
  });
  window.addEventListener(
    "pointermove",
    (e) => {
      if (!dragging) return;
      const scale = S.canvasVB.w / svg.clientWidth;
      S.canvasVB.x -= (e.clientX - lastX) * scale;
      S.canvasVB.y -= (e.clientY - lastY) * scale;
      lastX = e.clientX;
      lastY = e.clientY;
      applyVB();
    },
    { signal: sig },
  );
  window.addEventListener(
    "pointerup",
    () => {
      dragging = false;
    },
    { signal: sig },
  );
}
/* ══════════════════════════════════════════════════════════
   ROUTE: LEDGER — DETERMINAR (verificación causal al hash)
   ══════════════════════════════════════════════════════════ */
let ledgerPage = 1;
const LEDGER_PAGE_SIZE = 50;
async function renderLedgerPage(container) {
  onRouteEnter("ledger");
  setFocusHeader({
    breadcrumb: setBreadcrumb(
      "BABYLON·60",
      "BFT Ledger — DETERMINAR (verificar hasta el hash)",
    ),
    actions: `<button class="btn btn-verify" id="btn-verify-chain">⚿ Verify Chain</button>`,
  });
  document
    .getElementById("btn-verify-chain")
    ?.addEventListener("click", runChainVerification);
  container.innerHTML = `
    <div class="stats-grid slide-in" id="ledger-stats-grid">
      <div class="stat-card">
        <div class="stat-label">Ledger File</div>
        <div class="stat-value lapis" id="stat-db-name" style="font-size:0.85rem">—</div>
        <div class="stat-sub">SQLite WAL (diario de escritura: nunca corrompe) · RO</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Entries</div>
        <div class="stat-value gold" id="stat-total-entries">0</div>
        <div class="stat-sub" id="stat-latest-time">—</div>
      </div>
      <div class="stat-card">
        <div class="stat-label" title="Cada hash sella al anterior: manipular una entrada rompe la cadena entera">Consensus</div>
        <div class="stat-value verify" id="stat-integrity">UNKNOWN</div>
        <div class="stat-sub" id="stat-latest-lamport">Lamport (reloj lógico causal): —</div>
      </div>
    </div>
    <div class="card fade-in" style="margin-bottom:16px">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:10px">
        <div class="card-title">Hash Chain Verification</div>
        <span id="verify-summary" style="font-size:0.62rem;color:var(--dust-faint)"></span>
      </div>
      <div class="verify-progress" id="verify-progress-wrap" style="display:none">
        <div class="verify-progress-bar" id="verify-progress-bar"></div>
      </div>
      <div id="chain-visual-grid" class="chain-container">
        <div class="empty-state" style="padding:20px 0">
          <div class="icon">⚿</div>
          <div class="desc">Click "Verify Chain" para recomputar SHA3-256 (huella digital de cada evento) y asertar integridad.</div>
        </div>
      </div>
    </div>
    <div class="card fade-in">
      <div class="card-title" style="margin-bottom:10px">Ledger Sequence</div>
      <div style="overflow-x:auto">
        <table class="data-table">
          <thead>
            <tr>
              <th>Seq</th>
              <th>Stream</th>
              <th>Entity</th>
              <th>Event Type</th>
              <th title="Reloj lógico: orden causal sin depender del reloj de pared">Lamport</th>
              <th title="Huella causal: quién escribió, con qué motor y por qué">Taint</th>
              <th>Timestamp</th>
              <th title="SHA3-256: huella digital criptográfica del evento">Hash</th>
            </tr>
          </thead>
          <tbody id="ledger-table-body">
            <tr><td colspan="8" style="text-align:center;padding:16px;color:var(--dust-ghost)">Loading...</td></tr>
          </tbody>
        </table>
      </div>
      <div class="pagination">
        <button class="btn" id="btn-ledger-prev" disabled>◀ Prev</button>
        <span style="font-family:var(--font-mono);font-size:0.72rem" id="ledger-page-info">Page 1</span>
        <button class="btn" id="btn-ledger-next" disabled>Next ▶</button>
      </div>
    </div>
    <div id="entry-detail-panel" class="detail-panel" aria-hidden="true"></div>
  `;
  try {
    const stats = await get("/api/ledger/stats");
    S.ledgerStats = stats;
    const dbNameEl = document.getElementById("stat-db-name");
    if (dbNameEl) dbNameEl.textContent = stats.db_path || "—";
    const totalEl = document.getElementById("stat-total-entries");
    if (totalEl) totalEl.textContent = stats.entries ?? 0;
    const lamportEl = document.getElementById("stat-latest-lamport");
    if (lamportEl)
      lamportEl.textContent = `Lamport (reloj lógico causal): ${stats.latest?.lamport_t ?? "—"}`;
    const timeEl = document.getElementById("stat-latest-time");
    if (timeEl && stats.latest?.created_at)
      timeEl.textContent = String(stats.latest.created_at).slice(0, 19);
    updateStatusBar();
    updateContextPaneCounts();
  } catch {
    /* offline */
  }
  await loadLedgerPage(1);
  document
    .getElementById("btn-ledger-prev")
    ?.addEventListener("click", () => loadLedgerPage(ledgerPage - 1));
  document
    .getElementById("btn-ledger-next")
    ?.addEventListener("click", () => loadLedgerPage(ledgerPage + 1));
}
async function loadLedgerPage(page) {
  if (page < 1) page = 1;
  ledgerPage = page;
  const tbody = document.getElementById("ledger-table-body");
  if (!tbody) return;
  try {
    const offset = (page - 1) * LEDGER_PAGE_SIZE;
    const data = await get(
      `/api/ledger/entries?limit=${LEDGER_PAGE_SIZE}&offset=${offset}`,
    );
    const entries = data.entries || [];
    const total = data.total ?? entries.length;
    if (entries.length === 0) {
      tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;padding:20px;color:var(--dust-ghost)">No entries</td></tr>`;
    } else {
      tbody.innerHTML = entries
        .map(
          (e) => `
        <tr data-seq="${e.seq}" style="cursor:pointer" title="Abrir detalle (micro-túnel)">
          <td class="seq-cell">${e.seq}</td>
          <td class="stream-cell">${escapeHtml(e.stream)}</td>
          <td class="hash-cell" style="font-size:0.6rem;max-width:130px;overflow:hidden;text-overflow:ellipsis">${escapeHtml(e.entity_id)}</td>
          <td>${escapeHtml(e.event_type)}</td>
          <td style="color:var(--dust-dim)">${e.lamport_t}</td>
          <td class="hash-cell" style="font-size:0.58rem;max-width:170px;overflow:hidden;text-overflow:ellipsis" title="${escapeHtml(e.cortex_taint)}">${escapeHtml((e.cortex_taint || "—").slice(0, 26))}${(e.cortex_taint || "").length > 26 ? "…" : ""}</td>
          <td class="time-cell">${String(e.created_at || "").slice(0, 19)}</td>
          <td class="hash-cell" title="${escapeHtml(e.entry_hash)}">${(e.entry_hash || "—").slice(0, 12)}…</td>
        </tr>
      `,
        )
        .join("");
      tbody.querySelectorAll("tr[data-seq]").forEach((row) => {
        row.addEventListener("click", () =>
          openEntryDetail(parseInt(row.dataset.seq)),
        );
      });
    }
    const totalPages = Math.max(1, Math.ceil(total / LEDGER_PAGE_SIZE));
    const info = document.getElementById("ledger-page-info");
    if (info)
      info.textContent = `Page ${page} / ${totalPages} · ${total} entries`;
    const prev = document.getElementById("btn-ledger-prev");
    const next = document.getElementById("btn-ledger-next");
    if (prev) prev.disabled = page <= 1;
    if (next) next.disabled = page >= totalPages;
  } catch (err) {
    tbody.innerHTML = `<tr><td colspan="8" style="text-align:center;color:var(--break);padding:16px">Error: ${escapeHtml(err.message)}</td></tr>`;
  }
}
/* ── Entry detail (micro-túnel: una entrada, causa completa) ── */
async function openEntryDetail(seq) {
  const panel = document.getElementById("entry-detail-panel");
  if (!panel) return;
  panel.classList.add("open");
  panel.setAttribute("aria-hidden", "false");
  panel.innerHTML = `<div class="detail-header"><span class="detail-title">⧉ Entry #${seq}</span>
    <button class="btn btn-icon" id="detail-close" aria-label="Close">✕</button></div>
    <div class="detail-body" style="color:var(--dust-faint)">Loading...</div>`;
  panel
    .querySelector("#detail-close")
    ?.addEventListener("click", closeEntryDetail);
  try {
    const e = await get(`/api/ledger/entry/${seq}`);
    let payloadPretty = e.payload_json || "";
    try {
      payloadPretty = JSON.stringify(JSON.parse(e.payload_json), null, 2);
    } catch {
      /* raw */
    }
    const field = (label, value, cls = "") => `
      <div class="detail-field">
        <div class="detail-field-label">${escapeHtml(label)}</div>
        <div class="detail-field-value ${cls}">${escapeHtml(value ?? "—")}</div>
      </div>`;
    panel.innerHTML = `
      <div class="detail-header">
        <span class="detail-title">⧉ Entry #${e.seq} · ${escapeHtml(e.event_type)}</span>
        <button class="btn btn-icon" id="detail-close" aria-label="Close">✕</button>
      </div>
      <div class="detail-body">
        ${field("Event ID (UUID v5: determinista, mismo input → mismo id)", e.event_id, "mono")}
        ${field("Stream · Entity", `${e.stream} · ${e.entity_id}`)}
        ${field("Lamport T (reloj lógico: orden causal)", e.lamport_t)}
        ${field("Causal Taint (quién/por qué escribió)", e.cortex_taint, "mono")}
        ${field("Source (origen del dato)", `${e.source_db ?? "—"} › ${e.source_table ?? "—"} › ${e.source_pk ?? "—"}`, "mono")}
        ${field("Created At", e.created_at, "mono")}
        ${field("Prev Hash (sello del evento anterior)", e.prev_hash, "mono hash")}
        ${field("Entry Hash (SHA3-256 de todo el sobre)", e.entry_hash, "mono hash")}
        <div class="detail-field">
          <div class="detail-field-label">Payload (contenido del evento)</div>
          <pre class="detail-payload">${escapeHtml(payloadPretty)}</pre>
        </div>
      </div>
    `;
    panel
      .querySelector("#detail-close")
      ?.addEventListener("click", closeEntryDetail);
  } catch (err) {
    const bodyEl = panel.querySelector(".detail-body");
    if (bodyEl)
      bodyEl.innerHTML = `<span style="color:var(--break)">${escapeHtml(err.message)}</span>`;
  }
}
function closeEntryDetail() {
  const panel = document.getElementById("entry-detail-panel");
  if (panel) {
    panel.classList.remove("open");
    panel.setAttribute("aria-hidden", "true");
  }
}
/* ── Chain verification — POST /api/ledger/verify ── */
async function runChainVerification() {
  const btn = document.getElementById("btn-verify-chain");
  const grid = document.getElementById("chain-visual-grid");
  const progressWrap = document.getElementById("verify-progress-wrap");
  const progressBar = document.getElementById("verify-progress-bar");
  const integrityEl = document.getElementById("stat-integrity");
  const summaryEl = document.getElementById("verify-summary");
  if (!grid) return;
  if (btn) {
    btn.disabled = true;
    btn.textContent = "⚙ Verifying...";
  }
  if (progressWrap) progressWrap.style.display = "block";
  setTachometer("working");
  let progress = 0;
  const ticker = setInterval(() => {
    progress = Math.min(progress + 8, 90);
    if (progressBar) progressBar.style.width = `${progress}%`;
  }, 120);
  try {
    const result = await post("/api/ledger/verify", {});
    S.lastVerify = result;
    clearInterval(ticker);
    if (progressBar) progressBar.style.width = "100%";
    const total = result.total_entries ?? 0;
    const valid = result.verified_entries ?? 0;
    const broken = total - valid;
    grid.innerHTML = "";
    (result.entries || []).slice(0, 400).forEach((entry) => {
      const block = document.createElement("div");
      block.className = `chain-block ${entry.valid ? "" : "invalid"}`;
      block.title = `Seq ${entry.seq} · L:${entry.lamport_t} · ${entry.valid ? "VALID" : entry.errors.join(" · ")}`;
      block.addEventListener("click", () => openEntryDetail(entry.seq));
      grid.appendChild(block);
    });
    if (total === 0) {
      grid.innerHTML = `<div style="color:var(--dust-ghost);font-size:0.7rem;padding:8px">Ledger vacío — nada que verificar.</div>`;
    }
    const hasBreakSeq = result.broken_at != null;
    if (integrityEl) {
      integrityEl.textContent = result.valid
        ? "VERIFIED"
        : hasBreakSeq
          ? `BROKEN (${broken})`
          : "ERROR";
      integrityEl.className = `stat-value ${result.valid ? "verify" : "break"}`;
    }
    if (summaryEl) {
      summaryEl.textContent = result.valid
        ? `${valid}/${total} entries · cadena SHA3-256 intacta`
        : hasBreakSeq
          ? `rota en seq ${result.broken_at} · ${valid}/${total} válidas`
          : result.error || "verificación fallida";
    }
    if (!result.valid && result.error && total === 0) {
      grid.innerHTML = `<div style="color:var(--break);font-size:0.7rem;padding:8px">${escapeHtml(result.error)}</div>`;
    }
    if (result.valid) {
      setTachometer("done");
      if (mode().rewards) {
        const focusBody = document.getElementById("main-content");
        focusBody?.classList.add("reward-active");
        setTimeout(() => focusBody?.classList.remove("reward-active"), 1400);
      }
    } else {
      setTachometer("alert");
      showAgentModal({
        icon: "⚠",
        message: hasBreakSeq
          ? `Violación de integridad en seq ${result.broken_at} (la cadena de sellos se rompe ahí: todo lo posterior queda bajo sospecha).`
          : `Verificación fallida: ${result.error || "error desconocido"}.`,
        actions: hasBreakSeq
          ? [
              {
                label: "Inspeccionar entrada",
                primary: true,
                fn: () => {
                  hideAgentModal();
                  openEntryDetail(result.broken_at);
                },
              },
              { label: "Cerrar", fn: hideAgentModal },
            ]
          : [{ label: "Cerrar", primary: true, fn: hideAgentModal }],
      });
    }
    setTimeout(() => setTachometer("idle"), 3000);
  } catch (err) {
    clearInterval(ticker);
    grid.innerHTML = `<div style="color:var(--break);font-size:0.72rem;padding:10px">Verification failed: ${escapeHtml(err.message)}</div>`;
    setTachometer("idle");
  }
  if (btn) {
    btn.disabled = false;
    btn.textContent = "⚿ Verify Chain";
  }
  if (progressWrap)
    setTimeout(() => {
      progressWrap.style.display = "none";
    }, 1500);
}
/* ══════════════════════════════════════════════════════════
   ROUTE: DATABASES — drill-down: db → tablas → schema + filas
   ══════════════════════════════════════════════════════════ */
async function renderDatabasesPage(container) {
  onRouteEnter("databases");
  setFocusHeader({ breadcrumb: setBreadcrumb("BABYLON·60", "Ontologies") });
  container.innerHTML = `
    <div class="stats-grid slide-in">
      <div class="stat-card">
        <div class="stat-label">SQLite Files</div>
        <div class="stat-value gold" id="db-total-count">—</div>
        <div class="stat-sub">Descubiertos en la raíz del proyecto</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Total Size</div>
        <div class="stat-value lapis" id="db-total-size" style="font-size:1.1rem">—</div>
        <div class="stat-sub">Huella en disco</div>
      </div>
    </div>
    <div class="card fade-in">
      <div class="card-title" style="margin-bottom:10px">Ontology Databases <span style="color:var(--dust-ghost);font-weight:400;font-size:0.62rem">(click = ver tablas)</span></div>
      <table class="data-table">
        <thead><tr><th>Database</th><th>Size</th><th>Type</th></tr></thead>
        <tbody id="db-table-body"><tr><td colspan="3" style="text-align:center;padding:14px;color:var(--dust-ghost)">Loading...</td></tr></tbody>
      </table>
    </div>
    <div class="card fade-in" style="margin-top:14px;display:none" id="db-tables-panel">
      <div class="card-title" id="db-tables-title">Tables</div>
      <div id="db-tables-body" style="display:flex;flex-wrap:wrap;gap:6px;margin-top:8px"></div>
    </div>
    <div class="card fade-in" style="margin-top:14px;display:none" id="db-browse-panel">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:8px">
        <div class="card-title" id="db-browse-title">Table</div>
        <span id="db-browse-meta" style="font-size:0.6rem;color:var(--dust-ghost)"></span>
      </div>
      <div id="db-schema-body" style="font-family:var(--font-mono);font-size:0.68rem;color:var(--dust-dim);margin-bottom:10px"></div>
      <div id="db-rows-body" style="overflow-x:auto"></div>
    </div>
  `;
  try {
    const dbs = await get("/api/databases");
    S.databaseList = dbs;
    updateContextPaneCounts();
    const tbody = document.getElementById("db-table-body");
    const totalEl = document.getElementById("db-total-count");
    const sizeEl = document.getElementById("db-total-size");
    if (totalEl) totalEl.textContent = dbs.length;
    if (sizeEl) {
      const totalBytes = dbs.reduce((a, d) => a + (d.size_bytes || 0), 0);
      sizeEl.textContent =
        totalBytes > 1e6
          ? `${(totalBytes / 1e6).toFixed(1)} MB`
          : `${(totalBytes / 1024).toFixed(0)} KB`;
    }
    const typeOf = (name) => {
      if (name.includes("ledger")) return "LEDGER";
      if (name.includes("ontology")) return "ONTOLOGY";
      if (name.includes("memory") || name.includes("cortex")) return "CORTEX";
      if (name.includes("telemetry")) return "TELEMETRY";
      if (name.includes("nexus")) return "NEXUS";
      return "GENERAL";
    };
    if (tbody)
      tbody.innerHTML = dbs
        .map(
          (db) => `
      <tr style="cursor:pointer" data-db="${escapeHtml(db.name)}" title="Browse tables">
        <td class="stream-cell">${escapeHtml(db.name)}</td>
        <td class="time-cell">${escapeHtml(db.size_human || "—")}</td>
        <td><span style="font-size:0.58rem;padding:1px 5px;border-radius:2px;background:var(--tablet-2);color:var(--dust-faint)">${typeOf(db.name)}</span></td>
      </tr>
    `,
        )
        .join("");
    tbody?.querySelectorAll("tr[data-db]").forEach((row) => {
      row.addEventListener("click", () => loadDbTables(row.dataset.db));
    });
  } catch (err) {
    const tbody = document.getElementById("db-table-body");
    if (tbody)
      tbody.innerHTML = `<tr><td colspan="3" style="color:var(--break);text-align:center;padding:14px">${escapeHtml(err.message)}</td></tr>`;
  }
}
async function loadDbTables(dbName) {
  const panel = document.getElementById("db-tables-panel");
  const title = document.getElementById("db-tables-title");
  const body = document.getElementById("db-tables-body");
  const browsePanel = document.getElementById("db-browse-panel");
  if (!panel || !body) return;
  panel.style.display = "block";
  if (browsePanel) browsePanel.style.display = "none";
  if (title) title.textContent = `Tables — ${dbName}`;
  body.innerHTML = `<span style="color:var(--dust-faint);font-size:0.68rem">Loading...</span>`;
  setFocusHeader({
    breadcrumb: setBreadcrumb("BABYLON·60", "Ontologies", dbName),
  });
  try {
    const tables = await get(
      `/api/databases/${encodeURIComponent(dbName)}/tables`,
    );
    if (tables.length === 0) {
      body.innerHTML = `<span style="color:var(--dust-ghost);font-size:0.68rem">No tables.</span>`;
      return;
    }
    body.innerHTML = tables
      .map(
        (t) => `
      <button class="btn" data-table="${escapeHtml(t.name)}" style="font-size:0.62rem">
        ${escapeHtml(t.name)} <span style="color:var(--gold);margin-left:4px">${t.row_count}</span>
      </button>
    `,
      )
      .join("");
    body.querySelectorAll("[data-table]").forEach((btn) => {
      btn.addEventListener("click", () =>
        browseTable(dbName, btn.dataset.table),
      );
    });
  } catch (err) {
    body.innerHTML = `<span style="color:var(--break);font-size:0.68rem">${escapeHtml(err.message)}</span>`;
  }
}
async function browseTable(dbName, table) {
  const panel = document.getElementById("db-browse-panel");
  const title = document.getElementById("db-browse-title");
  const meta = document.getElementById("db-browse-meta");
  const schemaBody = document.getElementById("db-schema-body");
  const rowsBody = document.getElementById("db-rows-body");
  if (!panel || !rowsBody) return;
  panel.style.display = "block";
  if (title) title.textContent = `${dbName} › ${table}`;
  if (schemaBody) schemaBody.textContent = "Loading schema...";
  rowsBody.innerHTML = "";
  setFocusHeader({
    breadcrumb: setBreadcrumb("BABYLON·60", "Ontologies", dbName, table),
  });
  try {
    const [schema, data] = await Promise.all([
      get(
        `/api/databases/${encodeURIComponent(dbName)}/schema/${encodeURIComponent(table)}`,
      ),
      get(
        `/api/databases/${encodeURIComponent(dbName)}/tables/${encodeURIComponent(table)}?limit=25`,
      ),
    ]);
    if (schemaBody)
      schemaBody.innerHTML = schema
        .map(
          (c) =>
            `<span style="margin-right:12px;white-space:nowrap">${c.pk ? "⚿" : "·"} ${escapeHtml(c.name)} <span style="color:var(--dust-ghost)">${escapeHtml(c.type || "")}</span></span>`,
        )
        .join("");
    if (meta)
      meta.textContent = `${data.total} rows total · showing ${data.rows.length}`;
    if (data.rows.length === 0) {
      rowsBody.innerHTML = `<div style="color:var(--dust-ghost);font-size:0.68rem;padding:8px">Empty table.</div>`;
    } else {
      rowsBody.innerHTML = `
        <table class="data-table">
          <thead><tr>${data.columns.map((c) => `<th>${escapeHtml(c)}</th>`).join("")}</tr></thead>
          <tbody>${data.rows
            .map(
              (row) => `
            <tr>${data.columns
              .map((c) => {
                let v = row[c];
                if (v === null || v === undefined) v = "—";
                v = String(v);
                const truncated = v.length > 90 ? v.slice(0, 90) + "…" : v;
                return `<td title="${escapeHtml(v.slice(0, 400))}" style="max-width:260px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(truncated)}</td>`;
              })
              .join("")}</tr>
          `,
            )
            .join("")}</tbody>
        </table>
      `;
    }
  } catch (err) {
    rowsBody.innerHTML = `<div style="color:var(--break);font-size:0.7rem;padding:8px">${escapeHtml(err.message)}</div>`;
  }
}
/* ══════════════════════════════════════════════════════════
   ROUTE: QUERY — SQL Console · POST /api/query {database, sql}
   ══════════════════════════════════════════════════════════ */
async function renderQueryPage(container) {
  onRouteEnter("query");
  setFocusHeader({ breadcrumb: setBreadcrumb("BABYLON·60", "SQL Console") });
  if (S.databaseList.length === 0) await refreshDatabaseList();
  container.innerHTML = `
    <div class="card slide-in" style="margin-bottom:14px">
      <div style="display:flex;gap:10px;align-items:center;margin-bottom:10px">
        <select class="select" id="query-db-select" style="flex:1">
          ${S.databaseList.map((db) => `<option value="${escapeHtml(db.name)}">${escapeHtml(db.name)}</option>`).join("")}
        </select>
        <button class="btn btn-primary" id="btn-run-query">▶ Run</button>
        <button class="btn" id="btn-clear-query">Clear</button>
      </div>
      <div class="code-editor">
        <textarea id="query-input" placeholder="SELECT * FROM ledger_entries LIMIT 20;" spellcheck="false"></textarea>
        <div class="code-editor-toolbar">
          <span style="font-size:0.58rem;color:var(--dust-ghost)">query_only=ON (candado a nivel de motor: imposible mutar) · INSERT/UPDATE/DDL bloqueados</span>
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
    const sql = document.getElementById("query-input")?.value?.trim();
    const database = document.getElementById("query-db-select")?.value;
    if (!sql || !database) return;
    setTachometer("working");
    const resultCard = document.getElementById("query-result-card");
    const resultBody = document.getElementById("query-result-body");
    const resultMeta = document.getElementById("query-result-meta");
    if (resultCard) resultCard.style.display = "block";
    if (resultBody)
      resultBody.innerHTML = `<div style="color:var(--dust-faint);padding:10px">Running...</div>`;
    try {
      const result = await post("/api/query", { database, sql });
      const rows = result.rows || [];
      const cols = result.columns || [];
      if (resultMeta)
        resultMeta.textContent = `${result.row_count ?? rows.length} rows${result.truncated ? " (truncado a 1000 — afina la consulta)" : ""} · ${result.elapsed_ms ?? "—"}ms · ${result.database}`;
      if (resultBody) {
        if (rows.length === 0) {
          resultBody.innerHTML = `<div style="color:var(--dust-faint);padding:10px">No results</div>`;
        } else {
          resultBody.innerHTML = `
            <table class="data-table">
              <thead><tr>${cols.map((c) => `<th>${escapeHtml(c)}</th>`).join("")}</tr></thead>
              <tbody>${rows
                .map(
                  (row) =>
                    `<tr>${cols
                      .map((c) => {
                        let v = row[c];
                        if (v === null || v === undefined) v = "";
                        v = String(v);
                        const truncated =
                          v.length > 120 ? v.slice(0, 120) + "…" : v;
                        return `<td style="max-width:300px;overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escapeHtml(v.slice(0, 400))}">${escapeHtml(truncated)}</td>`;
                      })
                      .join("")}</tr>`,
                )
                .join("")}</tbody>
            </table>
          `;
        }
      }
      setTachometer("done");
      setTimeout(() => setTachometer("idle"), 2000);
    } catch (err) {
      if (resultBody)
        resultBody.innerHTML = `<div style="color:var(--break);padding:10px">Error: ${escapeHtml(err.message)}</div>`;
      setTachometer("idle");
    }
  };
  document.getElementById("btn-run-query")?.addEventListener("click", runQuery);
  document.getElementById("btn-clear-query")?.addEventListener("click", () => {
    const input = document.getElementById("query-input");
    if (input) input.value = "";
    const card = document.getElementById("query-result-card");
    if (card) card.style.display = "none";
  });
  document.getElementById("query-input")?.addEventListener("keydown", (e) => {
    if (e.shiftKey && e.key === "Enter") {
      e.preventDefault();
      runQuery();
    }
  });
}
/* ══════════════════════════════════════════════════════════
   ROUTE: SWARM — telemetría en vivo (push WS, sin polling)
   ══════════════════════════════════════════════════════════ */
async function renderSwarmPage(container) {
  onRouteEnter("swarm");
  setFocusHeader({
    breadcrumb: setBreadcrumb("BABYLON·60", "Agent Swarm"),
    actions: `<span class="focus-badge live">LIVE</span>`,
  });
  container.innerHTML = `
    <div class="swarm-layout">
      <div class="swarm-terminal">
        <div class="swarm-terminal-header">
          <div class="status-dot" style="width:5px;height:5px;border-radius:50%;background:var(--verify)"></div>
          Telemetry Stream · push cada 2s (el servidor empuja: la UI nunca pregunta)
        </div>
        <div class="swarm-terminal-body" id="swarm-log-body">
          <div class="swarm-log-line"><span class="swarm-log-time">—:—</span><span class="swarm-log-agent">SYSTEM</span><span class="swarm-log-msg">Connecting to /ws/telemetry...</span></div>
        </div>
      </div>
      <div class="swarm-inspector">
        <div class="swarm-inspector-header">Agent State</div>
        <div class="swarm-inspector-body" id="swarm-agents"></div>
      </div>
    </div>
  `;
  renderSwarmAgents();
  if (S.telemetrySocket) {
    try {
      S.telemetrySocket.close();
    } catch {
      /* noop */
    }
  }
  setTachometer("indexing");
  S.telemetrySocket = connectWebSocket(
    "/ws/telemetry",
    (snap) => {
      S.telemetrySnapshot = snap;
      appendSwarmSnapshot(snap);
      if (S.tachometerState === "indexing") setTachometer("idle");
    },
    () => {
      if (S.tachometerState === "indexing") setTachometer("idle");
    },
  );
}
function renderSwarmAgents() {
  const el = document.getElementById("swarm-agents");
  if (!el) return;
  const verify = S.lastVerify;
  const sent = S.sentinel;
  const agents = [
    {
      name: "MOSKV-1 APEX",
      status: "idle",
      task: "Meta-orquestador · esperando directiva",
      progress: 0,
    },
    {
      name: "BFT Verifier",
      status: verify ? (verify.valid ? "done" : "error") : "idle",
      task: verify
        ? verify.valid
          ? `Cadena verificada: ${verify.verified_entries}/${verify.total_entries}`
          : `ROTA en seq ${verify.broken_at}`
        : "Sin verificación en esta sesión",
      progress: verify ? 100 : 0,
    },
    {
      name: "Git Sentinel",
      status: sent
        ? sent.warnings?.some((w) => w.level === "red")
          ? "error"
          : "done"
        : "idle",
      task: sent
        ? `${sent.repo_name}@${sent.branch ?? "—"} · ${sent.dirty_files} dirty · delegación 100% al agente`
        : "Sin datos de repo",
      progress: sent ? 100 : 0,
    },
    {
      name: "Telemetry Stream",
      status: "running",
      task: "Empujando snapshots del sistema vía WS",
      progress: 100,
    },
  ];
  el.innerHTML = agents
    .map(
      (a) => `
    <div class="agent-card">
      <div class="agent-card-header">
        <span class="agent-name">${escapeHtml(a.name)}</span>
        <span class="agent-status-pill ${escapeHtml(a.status)}">${escapeHtml(a.status.toUpperCase())}</span>
      </div>
      <div class="agent-task">${escapeHtml(a.task)}</div>
      <div class="agent-progress">
        <div class="agent-progress-fill ${a.status === "done" ? "done" : ""}" style="width:${Math.min(100, Math.max(0, Number(a.progress) || 0))}%"></div>
      </div>
    </div>
  `,
    )
    .join("");
}
function appendSwarmSnapshot(snap) {
  const body = document.getElementById("swarm-log-body");
  if (!body) return;
  const now = new Date().toLocaleTimeString("en-GB", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
  });
  const dbs = snap.databases?.length ?? 0;
  const size =
    snap.total_db_size_mb != null ? `${snap.total_db_size_mb}MB` : "—";
  const wal = snap.wal_files?.length ?? 0;
  const rss =
    snap.process?.max_rss_mb != null ? `${snap.process.max_rss_mb}MB` : "—";
  const head = snap.git?.head
    ? snap.git.head.replace("ref: refs/heads/", "@")
    : "";
  const line = document.createElement("div");
  line.className = "swarm-log-line";
  line.innerHTML = `
    <span class="swarm-log-time">${now}</span>
    <span class="swarm-log-agent">TELEMETRY</span>
    <span class="swarm-log-msg info">⛁ ${dbs} DBs · ${size} · WAL×${wal} · RSS ${rss} ${head ? "· " + escapeHtml(head) : ""}</span>
  `;
  body.appendChild(line);
  while (body.children.length > 200) body.removeChild(body.firstChild);
  body.scrollTop = body.scrollHeight;
  S.swarmLog.push({ time: now, snap });
  if (S.swarmLog.length > 200) S.swarmLog.shift();
}
/* ══════════════════════════════════════════════════════════
   ROUTE: SENTINEL — identidad de repo + delegación 100% al agente
   ══════════════════════════════════════════════════════════ */
async function renderSentinelPage(container) {
  onRouteEnter("sentinel");
  setFocusHeader({
    breadcrumb: setBreadcrumb("BABYLON·60", "Git Sentinel"),
    actions: `<button class="btn" id="btn-sentinel-refresh">↺ Refresh</button>`,
  });
  container.innerHTML = `<div class="empty-state" style="padding:30px 0"><div class="icon">⎇</div><div class="desc">Leyendo identidad del repo...</div></div>`;
  try {
    S.sentinel = await get("/api/sentinel/status");
  } catch (err) {
    container.innerHTML = `<div class="empty-state" style="padding:30px 0"><div class="icon">⚠</div><div class="desc" style="color:var(--break)">${escapeHtml(err.message)}</div></div>`;
    return;
  }
  updateRepoSegment();
  renderContextPaneContent();
  const s = S.sentinel;
  const reds = s.warnings.filter((w) => w.level === "red");
  const ambers = s.warnings.filter((w) => w.level === "amber");
  const lineageOk = reds.length === 0;
  const warningsHtml =
    s.warnings.length === 0
      ? `<div style="color:var(--verify);font-size:0.7rem">✓ Linaje canónico: repo, rama y política de remoto coinciden con STATUS.md</div>`
      : s.warnings
          .map(
            (w) => `
        <div class="sentinel-warning ${w.level}">
          <span class="sentinel-warning-dot"></span>
          <span>${escapeHtml(w.msg)}</span>
        </div>
      `,
          )
          .join("");
  const remotesHtml =
    s.remotes.length === 0
      ? `<div style="color:var(--verify);font-size:0.66rem">✓ Sin remoto configurado (política P0 activa: nada sale a la nube hasta rotar claves)</div>`
      : s.remotes
          .map(
            (r) =>
              `<div style="font-family:var(--font-mono);font-size:0.64rem;color:var(--dust-dim)">${escapeHtml(r.name)} → ${escapeHtml(r.url)}</div>`,
          )
          .join("");
  container.innerHTML = `
    <div class="stats-grid slide-in">
      <div class="stat-card" style="border-left:2px solid ${lineageOk ? "var(--verify)" : "var(--break)"}">
        <div class="stat-label">Repo Actual (recalcado siempre — abajo en la barra de estado también)</div>
        <div class="stat-value ${lineageOk ? "verify" : "break"}" style="font-size:1rem">${escapeHtml(s.repo_name)}</div>
        <div class="stat-sub">@${escapeHtml(s.branch ?? "—")} · HEAD ${escapeHtml(s.head ?? "—")} · ${s.commit_count ?? "—"} commits</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Working Tree (árbol de trabajo: cambios sin commitear)</div>
        <div class="stat-value gold">${s.dirty_files}</div>
        <div class="stat-sub">${s.dirty_files === 0 ? "Limpio — todo sellado en git" : "ficheros sucios pendientes de commit"}</div>
      </div>
      <div class="stat-card">
        <div class="stat-label">Último Commit</div>
        <div class="stat-value lapis" style="font-size:0.78rem">${escapeHtml((s.head_subject || "—").slice(0, 44))}</div>
        <div class="stat-sub">${escapeHtml(String(s.head_time || "—").slice(0, 19))}</div>
      </div>
    </div>
    <div class="card fade-in" style="margin-bottom:14px">
      <div class="card-title" style="margin-bottom:8px">Lineage Guard (intuición de repo incorrecto)</div>
      ${warningsHtml}
      <div style="margin-top:10px;padding-top:8px;border-top:1px solid var(--edge-soft)">
        <div style="font-size:0.6rem;color:var(--dust-ghost);margin-bottom:4px">CANON: ${escapeHtml(s.canonical.repo_name)} @ ${escapeHtml(s.canonical.branch)} · remotos: ${escapeHtml(s.canonical.remote_policy)}</div>
        ${remotesHtml}
      </div>
    </div>
    <div class="card fade-in">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:6px">
        <div class="card-title">Delegación 100% al Agente <span style="color:var(--dust-ghost);font-weight:400;font-size:0.6rem">(sellada en CortexLedger real)</span></div>
        <button class="btn" id="btn-verify-ide-ledger" style="font-size:0.6rem">⚿ Verify IDE Ledger</button>
      </div>
      <div style="font-size:0.66rem;color:var(--dust-dim);margin-bottom:10px">
        Declaras la intención; MOSKV-1 ejecuta con Git Sentinel y la sella en el ledger propio del IDE (append-only, hash-chain SHA-256).
        <code style="color:var(--verify)">commit</code> se ejecuta de verdad (git local); <code style="color:var(--gold)">push/merge/ship/deploy</code> hacen <b>crash causal</b> mientras P0 esté abierto (claves expuestas en el fork remoto).
      </div>
      <div style="display:flex;gap:6px;margin-bottom:10px">
        <select class="select" id="delegation-kind" style="width:120px">
          <option value="commit">commit</option>
          <option value="precommit">precommit</option>
          <option value="status">status</option>
          <option value="push">push ⛔</option>
          <option value="merge">merge ⛔</option>
          <option value="ship">ship ⛔</option>
          <option value="deploy">deploy ⛔</option>
          <option value="custom">custom</option>
        </select>
        <input class="input" id="delegation-input" placeholder="Directiva… ej: 'feat(ide): analytics + delegación real'" style="flex:1">
        <button class="btn btn-primary" id="delegation-add">⚡ Delegar</button>
      </div>
      <div id="delegation-status" style="font-size:0.62rem;margin-bottom:8px;min-height:14px"></div>
      <div id="delegation-list"><div style="color:var(--dust-ghost);font-size:0.64rem">Cargando cola…</div></div>
    </div>
  `;
  document
    .getElementById("btn-sentinel-refresh")
    ?.addEventListener("click", () => rerender());
  document
    .getElementById("delegation-add")
    ?.addEventListener("click", addDelegation);
  document
    .getElementById("delegation-input")
    ?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") addDelegation();
    });
  document
    .getElementById("btn-verify-ide-ledger")
    ?.addEventListener("click", verifyIdeLedger);
  await refreshDelegations();
}
async function refreshDelegations() {
  const el = document.getElementById("delegation-list");
  if (!el) return;
  try {
    const data = await get("/api/delegation");
    renderDelegationList(data.delegations || []);
  } catch (err) {
    el.innerHTML = `<div style="color:var(--break);font-size:0.64rem">${escapeHtml(err.message)}</div>`;
  }
}
async function addDelegation() {
  const input = document.getElementById("delegation-input");
  const kindSel = document.getElementById("delegation-kind");
  const statusEl = document.getElementById("delegation-status");
  if (!input || !input.value.trim()) return;
  const directive = input.value.trim();
  const kind = kindSel?.value || "custom";
  try {
    const res = await post("/api/delegation", { directive, kind });
    input.value = "";
    if (statusEl) {
      statusEl.innerHTML = res.cloud_blocked
        ? `<span style="color:var(--gold)">⛔ '${kind}' encolado pero bloqueado por P0 — ejecútalo para ver el crash causal.</span>`
        : `<span style="color:var(--verify)">✓ '${kind}' encolado (${res.delegation_id}).</span>`;
    }
    if (mode().rewards) {
      setTachometer("done");
      setTimeout(() => setTachometer("idle"), 1500);
    }
    await refreshDelegations();
  } catch (err) {
    if (statusEl)
      statusEl.innerHTML = `<span style="color:var(--break)">${escapeHtml(err.message)}</span>`;
  }
}
async function executeDelegation(id) {
  const statusEl = document.getElementById("delegation-status");
  if (statusEl)
    statusEl.innerHTML = `<span style="color:var(--dust-faint)">Ejecutando ${id}…</span>`;
  try {
    const res = await post(`/api/delegation/${id}/execute`, {});
    if (statusEl)
      statusEl.innerHTML = `<span style="color:var(--verify)">✓ EXECUTED: ${escapeHtml(res.result || "")}</span>`;
    if (mode().rewards) {
      const fb = document.getElementById("main-content");
      fb?.classList.add("reward-active");
      setTimeout(() => fb?.classList.remove("reward-active"), 1400);
    }
  } catch (err) {
    if (statusEl)
      statusEl.innerHTML = `<span style="color:var(--break)">⛔ ${escapeHtml(err.message)}</span>`;
    setTachometer("alert");
    setTimeout(() => setTachometer("idle"), 2500);
  }
  await refreshDelegations();
}
async function cancelDelegation(id) {
  try {
    await post(`/api/delegation/${id}/cancel`, {});
  } catch {
    /* noop */
  }
  await refreshDelegations();
}
async function verifyIdeLedger() {
  const statusEl = document.getElementById("delegation-status");
  try {
    const v = await post("/api/delegation/verify", {});
    if (statusEl)
      statusEl.innerHTML = v.valid
        ? `<span style="color:var(--verify)">⚿ IDE CortexLedger íntegro: ${v.verified_entries}/${v.total_entries} eventos, cadena SHA-256 intacta.</span>`
        : `<span style="color:var(--break)">⚿ Cadena rota en seq ${v.broken_at} (${v.verified_entries}/${v.total_entries}).</span>`;
  } catch (err) {
    if (statusEl)
      statusEl.innerHTML = `<span style="color:var(--break)">${escapeHtml(err.message)}</span>`;
  }
}
const STATE_COLORS = {
  QUEUED: "var(--gold)",
  EXECUTED: "var(--verify)",
  BLOCKED: "var(--break)",
  FAILED: "var(--break)",
  CANCELLED: "var(--dust-ghost)",
};
function renderDelegationList(items) {
  const el = document.getElementById("delegation-list");
  if (!el) return;
  if (!items || items.length === 0) {
    el.innerHTML = `<div style="color:var(--dust-ghost);font-size:0.64rem">Cola vacía. El agente no tiene directivas git pendientes.</div>`;
    return;
  }
  const CLOUD = new Set(["push", "merge", "ship", "deploy"]);
  el.innerHTML = items
    .map((d) => {
      const canExec = d.state === "QUEUED";
      const blocked = CLOUD.has(d.kind);
      return `
    <div class="delegation-item">
      <span class="delegation-state" style="color:${STATE_COLORS[d.state] || "var(--dust-dim)"};background:transparent;border:1px solid currentColor">${escapeHtml(d.state)}</span>
      <span class="delegation-kind-tag" title="${blocked ? "op de nube — bloqueada por P0" : "op local"}">${escapeHtml(d.kind)}${blocked ? " ⛔" : ""}</span>
      <span class="delegation-text">${escapeHtml(d.directive)}${d.result ? ` <span style="color:var(--dust-faint)">— ${escapeHtml(String(d.result).slice(0, 80))}</span>` : ""}</span>
      ${canExec ? `<button class="btn delegation-exec" data-exec="${escapeHtml(d.delegation_id)}" style="font-size:0.56rem;padding:2px 7px">▶ EJECUTAR</button>` : ""}
      ${canExec ? `<span class="delegation-del" data-del="${escapeHtml(d.delegation_id)}" title="Cancelar">✕</span>` : ""}
    </div>`;
    })
    .join("");
  el.querySelectorAll("[data-exec]").forEach((b) =>
    b.addEventListener("click", () => executeDelegation(b.dataset.exec)),
  );
  el.querySelectorAll("[data-del]").forEach((b) =>
    b.addEventListener("click", () => cancelDelegation(b.dataset.del)),
  );
}
/* ══════════════════════════════════════════════════════════
   ROUTE: ANALYTICS — DETERMINAR (agregación + búsqueda BM25)
   ══════════════════════════════════════════════════════════ */
async function renderAnalyticsPage(container) {
  onRouteEnter("analytics");
  setFocusHeader({
    breadcrumb: setBreadcrumb("BABYLON·60", "Ledger Analytics — DETERMINAR"),
    actions: `<button class="btn" id="btn-analytics-refresh" style="font-size:0.62rem">↺ Refresh</button>`,
  });
  container.innerHTML = `
    <div class="card slide-in" style="margin-bottom:14px">
      <div class="card-title" style="margin-bottom:8px">Búsqueda semántico-léxica <span style="color:var(--dust-ghost);font-weight:400;font-size:0.6rem">(Okapi BM25 sobre payload+taint — el "por qué macro")</span></div>
      <div style="display:flex;gap:8px">
        <input class="input" id="ledger-search-input" placeholder="Buscar en el ledger… ej: 'amendment risk', 'autopoietic', 'enrollment'" style="flex:1">
        <button class="btn btn-primary" id="ledger-search-btn">⌕ Buscar</button>
      </div>
      <div id="ledger-search-results" style="margin-top:10px"></div>
    </div>
    <div id="analytics-body">
      <div class="empty-state" style="padding:20px 0"><div class="icon">∿</div><div class="desc">Cargando agregación del ledger…</div></div>
    </div>
    <div id="entry-detail-panel" class="detail-panel" aria-hidden="true"></div>
  `;
  document
    .getElementById("btn-analytics-refresh")
    ?.addEventListener("click", () => rerender());
  const doSearch = () =>
    runLedgerSearch(
      document.getElementById("ledger-search-input")?.value || "",
    );
  document
    .getElementById("ledger-search-btn")
    ?.addEventListener("click", doSearch);
  document
    .getElementById("ledger-search-input")
    ?.addEventListener("keydown", (e) => {
      if (e.key === "Enter") doSearch();
    });
  const body = document.getElementById("analytics-body");
  try {
    const a = await get("/api/ledger/analytics");
    const bar = (rows, key, valKey, color) => {
      const max = Math.max(...rows.map((r) => r[valKey]), 1);
      return rows
        .map(
          (r) => `
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:4px">
          <span style="width:150px;font-size:0.64rem;color:var(--dust-dim);overflow:hidden;text-overflow:ellipsis;white-space:nowrap" title="${escapeHtml(String(r[key]))}">${escapeHtml(String(r[key]))}</span>
          <div style="flex:1;background:var(--tablet);border-radius:2px;height:14px;position:relative">
            <div style="width:${((r[valKey] / max) * 100).toFixed(1)}%;background:${color};height:100%;border-radius:2px;opacity:0.75"></div>
          </div>
          <span style="width:40px;text-align:right;font-size:0.62rem;color:var(--gold)">${r[valKey]}</span>
        </div>`,
        )
        .join("");
    };
    const lam = a.lamport;
    body.innerHTML = `
      <div class="stats-grid" style="margin-bottom:14px">
        <div class="stat-card"><div class="stat-label">Total Eventos</div><div class="stat-value gold">${a.total_entries}</div><div class="stat-sub">${escapeHtml(a.db_path)}</div></div>
        <div class="stat-card"><div class="stat-label" title="Reloj lógico: sin huecos = orden causal total reconstruible">Continuidad Lamport</div><div class="stat-value ${lam.contiguous ? "verify" : "break"}">${lam.contiguous ? "CONTIGUA" : `${lam.gaps} HUECOS`}</div><div class="stat-sub">L:${lam.min}–${lam.max} · ${lam.distinct} distintos</div></div>
        <div class="stat-card"><div class="stat-label">Span Temporal</div><div class="stat-value lapis" style="font-size:0.8rem">${String(a.time_span.first || "—").slice(0, 10)}</div><div class="stat-sub">→ ${String(a.time_span.last || "—").slice(0, 10)}</div></div>
      </div>
      <div class="card" style="margin-bottom:12px"><div class="card-title" style="margin-bottom:8px">Streams</div>${bar(a.streams, "stream", "count", "var(--lapis-bright)")}</div>
      <div class="card" style="margin-bottom:12px"><div class="card-title" style="margin-bottom:8px">Event Types</div>${bar(a.event_types, "event_type", "count", "var(--verify)")}</div>
      <div class="card"><div class="card-title" style="margin-bottom:8px">Agentes <span style="color:var(--dust-ghost);font-weight:400;font-size:0.6rem">(prefijo del causal_taint — quién escribió)</span></div>${bar(a.agents, "agent", "count", "var(--gold)")}</div>
    `;
  } catch (err) {
    body.innerHTML = `<div class="empty-state" style="padding:24px 0"><div class="icon">⚠</div><div class="desc" style="color:var(--break)">${escapeHtml(err.message)}</div></div>`;
  }
}
async function runLedgerSearch(q) {
  const el = document.getElementById("ledger-search-results");
  if (!el) return;
  if (!q.trim()) {
    el.innerHTML = "";
    return;
  }
  el.innerHTML = `<div style="color:var(--dust-faint);font-size:0.64rem">Rankeando…</div>`;
  try {
    const data = await get(
      `/api/ledger/search?q=${encodeURIComponent(q)}&limit=15`,
    );
    if (!data.results.length) {
      el.innerHTML = `<div style="color:var(--dust-ghost);font-size:0.64rem">Sin coincidencias léxicas para «${escapeHtml(q)}» en ${data.corpus_size} eventos.</div>`;
      return;
    }
    el.innerHTML = `
      <div style="font-size:0.58rem;color:var(--dust-ghost);margin-bottom:6px">${data.results.length} resultados · ${escapeHtml(data.method)} · corpus ${data.corpus_size}${data.truncated ? ` · escaneados ${data.scanned}/${data.total} (truncado)` : ""}</div>
      ${data.results
        .map(
          (r) => `
        <div class="search-hit" data-seq="${r.seq}" title="Abrir entrada #${r.seq}">
          <span class="search-score">${r.score.toFixed(2)}</span>
          <div style="flex:1;min-width:0">
            <div style="font-size:0.64rem;color:var(--dust-dim)"><b>#${r.seq}</b> · ${escapeHtml(r.event_type)} · ${escapeHtml(r.stream)}</div>
            <div style="font-size:0.58rem;color:var(--dust-faint);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">${escapeHtml(r.snippet)}</div>
          </div>
        </div>`,
        )
        .join("")}
    `;
    el.querySelectorAll("[data-seq]").forEach((h) =>
      h.addEventListener("click", () =>
        openEntryDetail(parseInt(h.dataset.seq)),
      ),
    );
  } catch (err) {
    el.innerHTML = `<div style="color:var(--break);font-size:0.64rem">${escapeHtml(err.message)}</div>`;
  }
}
