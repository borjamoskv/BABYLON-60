// C5-REAL EXERGY CERTIFIED
/* ═══════════════════════════════════════════════════════════
   AGENTS.archi — Architect's Swarm Component
   Neural Visualization & Interaction v2.0
   ═══════════════════════════════════════════════════════════ */

import {
  ARCHITECT_HELPERS,
  getDomainStats,
  getHelpersByDomain,
  getHelperCount,
  getActiveHelpers,
} from '../data/architectTemplate.js';

import { fetchComplianceStatus, generateSovereignCertificate } from '../services/cortexApi.js';

let activeFilter = 'all';
let crystallizationCount = 0;
let canvas, ctx;
let animationFrameId;
let particles = [];
let connections = [];
let pulses = [];
let agentPositions = new Map();
let lastTimestamp = 0;
let systemStress = 0;

export function initArchitectSwarm() {
  const container = document.getElementById('swarm-grid');
  const filterBar = document.getElementById('swarm-filters');
  const countEl = document.getElementById('swarm-count');
  canvas = document.getElementById('swarm-canvas');

  if (!container) return;

  loadSwarmState();
  renderFilters(filterBar);
  renderSwarm(container, ARCHITECT_HELPERS);
  updateCount(countEl);

  initNeuralCanvas();
  startContextSimulation();
  startDashboardTelemetry();

  const optBtn = document.getElementById('btn-swarm-opt');
  if (optBtn) {
    optBtn.addEventListener('click', () => optimizeSwarm());
  }

  const auditBtn = document.getElementById('btn-swarm-audit');
  if (auditBtn) {
    auditBtn.addEventListener('click', () => runSovereignAudit());
  }

  window.addEventListener('resize', () => {
    resizeCanvas();
    renderSwarm(container, activeFilter === 'all' ? ARCHITECT_HELPERS : getHelpersByDomain(activeFilter));
  });
}

/* ── Persistence ── */
function saveSwarmState() {
  const state = ARCHITECT_HELPERS.map(h => ({
    id: h.id,
    context: h.context
  }));
  localStorage.setItem('cortex_swarm_state', JSON.stringify(state));
}

function loadSwarmState() {
  const saved = localStorage.getItem('cortex_swarm_state');
  if (!saved) return;
  try {
    const state = JSON.parse(saved);
    state.forEach(s => {
      const helper = ARCHITECT_HELPERS.find(h => h.id === s.id);
      if (helper) helper.context = s.context;
    });
  } catch (e) {
    console.error("Failed to load swarm state", e);
  }
}

/* ── Filters ── */
function renderFilters(bar) {
  if (!bar) return;
  bar.innerHTML = '';

  const allBtn = createFilterBtn('all', `All (${getHelperCount()})`, '⬡');
  allBtn.classList.add('filter-active');
  bar.appendChild(allBtn);

  const stats = getDomainStats();
  Object.values(stats).forEach(domain => {
    if (domain.total === 0) return;
    const btn = createFilterBtn(domain.id, `${domain.label} (${domain.total})`, domain.icon);
    bar.appendChild(btn);
  });
}

function createFilterBtn(filterId, label, icon) {
  const btn = document.createElement('button');
  btn.className = 'swarm-filter-btn';
  btn.dataset.filter = filterId;
  btn.innerHTML = `<span class="filter-icon">${icon}</span><span class="filter-label">${label}</span>`;

  btn.addEventListener('click', () => {
    activeFilter = filterId;
    document.querySelectorAll('.swarm-filter-btn').forEach(b => b.classList.remove('filter-active'));
    btn.classList.add('filter-active');

    const container = document.getElementById('swarm-grid');
    const helpers = filterId === 'all' ? ARCHITECT_HELPERS : getHelpersByDomain(filterId);
    renderSwarm(container, helpers);

    // Update mapping after layout change
    setTimeout(updateAgentPositions, 400);
  });

  return btn;
}

/* ── Swarm Grid ── */
function renderSwarm(container, helpers) {
  container.innerHTML = '';

  helpers.forEach((helper, i) => {
    const card = document.createElement('div');
    card.className = `swarm-card swarm-tier-${helper.tier} reveal`;
    card.style.transitionDelay = `${i * 20}ms`;
    card.dataset.id = helper.id;
    card.dataset.status = helper.status;

    // Domain accent stripe
    const stripe = document.createElement('div');
    stripe.className = 'swarm-card-stripe';
    stripe.style.background = helper.domain.color;
    card.appendChild(stripe);

    // Header
    const header = document.createElement('div');
    header.className = 'swarm-card-header';
    header.innerHTML = `
      <div class="swarm-name-row">
        <span class="swarm-icon">${helper.domain.icon}</span>
        <span class="swarm-name">${helper.name}</span>
        <span class="swarm-tier-badge tier-${helper.tier}">${helper.tier.toUpperCase()}</span>
      </div>
      <div class="swarm-role">${helper.role}</div>
    `;
    card.appendChild(header);

    // Context Management
    if (helper.context) {
      const ctxContainer = document.createElement('div');
      ctxContainer.className = 'swarm-context-mgmt';
      ctxContainer.dataset.agentId = helper.id;

      const exergy = (Math.random() * 0.5 + 0.1).toFixed(2);

      ctxContainer.innerHTML = `
        <div class="swarm-ctx-header">
          <span class="ctx-label">CONTEXT_LEDGER v6.0</span>
          <span class="ctx-status status-${helper.context.state}" data-ctx-field="state">${helper.context.state.toUpperCase()}</span>
        </div>
        <div class="swarm-ctx-metrics">
          <div class="ctx-metric"><span>Memory</span><span data-ctx-field="memory">${helper.context.memory}</span></div>
          <div class="ctx-metric"><span>Exergy</span><span data-ctx-field="exergy">${exergy}W</span></div>
        </div>
        <div class="swarm-resolution-container">
          <div class="swarm-resolution-bar" data-ctx-field="res-bar"></div>
          <div class="swarm-resolution-glitch" data-ctx-field="res-glitch"></div>
        </div>
        <div class="swarm-ctx-log" id="log-${helper.id}">
          <div class="log-line">TAINT: ${Math.random().toString(36).substring(2, 10)}...</div>
          <div class="log-line">INIT_AUTO_MANAGEMENT_DAEMON</div>
        </div>
      `;
      card.appendChild(ctxContainer);
    }

    // Status footer
    const footer = document.createElement('div');
    footer.className = 'swarm-card-footer';
    footer.innerHTML = `
      <span class="swarm-status-dot status-${helper.status}"></span>
      <span class="swarm-status-text">${helper.status.toUpperCase()}</span>
      <span class="swarm-pulse">λ ${helper.pulse.toFixed(1)}s</span>
    `;
    card.appendChild(footer);

    // Interaction: Force Crystallization
    card.addEventListener('click', () => {
      if (helper.context && helper.context.state === 'synchronized') {
        startResolution(helper);
        showRipple(card);
      }
    });

    container.appendChild(card);

    // Reveal animation
    setTimeout(() => card.classList.add('revealed'), 50);
  });

  // Update canvas after rendering
  setTimeout(updateAgentPositions, 300);
}

function showRipple(card) {
  const ripple = document.createElement('div');
  ripple.className = 'card-ripple';
  card.appendChild(ripple);
  setTimeout(() => ripple.remove(), 600);
}

function startResolution(agent) {
  if (!agent.context || agent.context.state === 'resolving') return;

  agent.context.state = 'resolving';
  agent.context.resolution = 0;

  const card = document.querySelector(`.swarm-card[data-id="${agent.id}"]`);
  if (card) card.classList.add('resolving');

  syncAgentUI(agent);
  addLogLine(agent.id, "INIT_EPISTEMIC_RESOLUTION");

  // Stress-Based Epistemic Friction: Neighborhood stress slows resolution
  const neighborhood = agent.connectsTo || [];
  const neighborStress = neighborhood.reduce((acc, nid) => {
    const n = ARCHITECT_HELPERS.find(h => h.id === nid);
    return acc + (n && n.context ? parseInt(n.context.memory) : 0);
  }, 0) / (neighborhood.length || 1);

  const friction = 1 - (neighborStress / 150); // High stress neighborhood = more friction
  const baseSpeed = (agent.tier === 'apex' ? 22 : (agent.tier === 'commander' ? 14 : 9)) * Math.max(0.3, friction);

  const interval = setInterval(() => {
    agent.context.resolution += (Math.random() * baseSpeed + 2);

    if (agent.context.resolution >= 100) {
      agent.context.resolution = 100;
      clearInterval(interval);
      if (card) card.classList.remove('resolving');
      crystallizeAgent(agent);
    }
    syncAgentUI(agent);
  }, 300);
}

function startScrubbing(agent) {
  if (!agent.context || agent.context.state !== 'synchronized') return;

  agent.context.state = 'scrubbing';
  const card = document.querySelector(`.swarm-card[data-id="${agent.id}"]`);
  if (card) card.classList.add('scrubbing');

  syncAgentUI(agent);
  addLogLine(agent.id, "SCRUBBING_STALE_CONTEXT...");

  let steps = 0;
  const interval = setInterval(() => {
    const memNum = parseInt(agent.context.memory);
    const reduction = Math.floor(Math.random() * 8 + 4);
    agent.context.memory = `${Math.max(20, memNum - reduction)}%`;
    steps++;

    if (steps > 5 || parseInt(agent.context.memory) < 40) {
      clearInterval(interval);
      agent.context.state = 'synchronized';
      if (card) card.classList.remove('scrubbing');
      addLogLine(agent.id, "SCRUB_COMPLETE_YIELD_OPTIMIZED");
      syncAgentUI(agent);
    } else {
      syncAgentUI(agent);
    }
  }, 800);
}

function crystallizeAgent(agent) {
  if (!agent.context) return;

  agent.context.state = 'crystallizing';
  const card = document.querySelector(`.swarm-card[data-id="${agent.id}"]`);
  if (card) card.classList.add('crystallizing');
  syncAgentUI(agent);

  addLogLine(agent.id, "CRYSTALLIZING_FACTS...");

    // Pulse neighbors to help them resolve
    if (agent.connectsTo) {
      agent.connectsTo.forEach(tid => {
        createPulse(agent.id, tid, '#00f2ff');
        const target = ARCHITECT_HELPERS.find(h => h.id === tid);
        if (target && target.context && target.context.state === 'resolving') {
          target.context.resolution += 15; // Boost neighbor
          addLogLine(tid, `RECV_BOOST <- ${agent.name.split(' ')[0].toUpperCase()}`);
        }
      });
    }

    setTimeout(() => {
      agent.context.state = 'synchronized';
      agent.context.memory = `${Math.floor(Math.random() * 15 + 5)}%`;
      agent.context.lastCrystallization = 'Just now';
      agent.context.resolution = 0;
      crystallizationCount++;
      if (card) card.classList.remove('crystallizing');
      syncAgentUI(agent);
      addLogLine(agent.id, "SYNC_COMMITTED_LEDGER_V6");
      saveSwarmState();
    }, 1200);
}

function addLogLine(agentId, text) {
  const log = document.getElementById(`log-${agentId}`);
  if (!log) return;
  const line = document.createElement('div');
  line.className = 'log-line';
  const timestamp = new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  line.textContent = `[${timestamp}] ${text}`;
  log.prepend(line);
  if (log.children.length > 5) log.lastChild.remove();
}

/* ── Neural Canvas ── */
function initNeuralCanvas() {
  if (!canvas) return;
  ctx = canvas.getContext('2d');
  resizeCanvas();
  initParticles();
  animate(0);
}

function resizeCanvas() {
  const section = document.getElementById('architect-swarm');
  if (!section || !canvas) return;
  canvas.width = section.clientWidth;
  canvas.height = section.clientHeight;
  updateAgentPositions();
}

function updateAgentPositions() {
  const cards = document.querySelectorAll('.swarm-card');
  const sectionRect = document.getElementById('architect-swarm').getBoundingClientRect();

  agentPositions.clear();
  cards.forEach(card => {
    const id = parseInt(card.dataset.id);
    const rect = card.getBoundingClientRect();

    agentPositions.set(id, {
      x: rect.left - sectionRect.left + rect.width / 2,
      y: rect.top - sectionRect.top + rect.height / 2,
      id: id,
      color: ARCHITECT_HELPERS.find(h => h.id === id)?.domain.color || '#2B3BE5'
    });
  });

  // Re-map connections based on current visibility
  connections = [];
  if (activeFilter === 'all') {
    ARCHITECT_HELPERS.forEach(helper => {
      if (helper.connectsTo && agentPositions.has(helper.id)) {
        helper.connectsTo.forEach(targetId => {
          if (agentPositions.has(targetId)) {
            connections.push({
              start: agentPositions.get(helper.id),
              end: agentPositions.get(targetId),
              color: helper.domain.color
            });
          }
        });
      }
    });
  }
}

function initParticles() {
  particles = [];
  for (let i = 0; i < 60; i++) {
    particles.push({
      x: Math.random() * canvas.width,
      y: Math.random() * canvas.height,
      vx: (Math.random() - 0.5) * 0.3,
      vy: (Math.random() - 0.5) * 0.3,
      size: Math.random() * 2 + 1,
      alpha: Math.random() * 0.3 + 0.1
    });
  }
}

function createPulse(startId, endId, color) {
  const start = agentPositions.get(startId);
  const end = agentPositions.get(endId);
  if (!start || !end) return;

  pulses.push({
    start,
    end,
    progress: 0,
    speed: 0.005 + Math.random() * 0.01,
    color: color
  });
}

function drawStressHeatmap() {
  if (!ctx || agentPositions.size === 0) return;

  agentPositions.forEach(pos => {
    const agent = ARCHITECT_HELPERS.find(h => h.id === pos.id);
    if (!agent || !agent.context) return;

    const mem = parseInt(agent.context.memory);
    if (mem > 40) {
      const radius = (mem / 100) * 100;
      const opacity = (mem - 40) / 100 * 0.2;

      const grad = ctx.createRadialGradient(pos.x, pos.y, 0, pos.x, pos.y, radius);

      // Color shifts from blue to red based on stress
      const r = Math.floor((mem / 100) * 229);
      const b = Math.floor((1 - mem / 100) * 229);
      const g = 62;

      grad.addColorStop(0, `rgba(${r}, ${g}, ${b}, ${opacity})`);
      grad.addColorStop(1, 'rgba(0, 0, 0, 0)');

      ctx.beginPath();
      ctx.fillStyle = grad;
      ctx.arc(pos.x, pos.y, radius, 0, Math.PI * 2);
      ctx.fill();

      // High stress glitch lines
      if (mem > 85 && Math.random() > 0.8) {
        ctx.strokeStyle = `rgba(229, 62, 62, ${opacity * 2})`;
        ctx.lineWidth = 1;
        ctx.beginPath();
        ctx.moveTo(pos.x - 20, pos.y + (Math.random() - 0.5) * 10);
        ctx.lineTo(pos.x + 20, pos.y + (Math.random() - 0.5) * 10);
        ctx.stroke();
      }
    }
  });
}

function drawNeuralNetwork(timestamp) {
  if (!ctx) return;
  ctx.clearRect(0, 0, canvas.width, canvas.height);

  // 0. Draw Stress Heatmap
  drawStressHeatmap();

  // 1. Draw Particles
  particles.forEach(p => {
    p.x += p.vx;
    p.y += p.vy;
    if (p.x < 0) p.x = canvas.width;
    if (p.x > canvas.width) p.x = 0;
    if (p.y < 0) p.y = canvas.height;
    if (p.y > canvas.height) p.y = 0;

    ctx.beginPath();
    ctx.fillStyle = `rgba(255, 255, 255, ${p.alpha})`;
    ctx.arc(p.x, p.y, p.size, 0, Math.PI * 2);
    ctx.fill();
  });

  // 2. Draw Connections
  if (activeFilter === 'all') {
    ctx.lineWidth = 1;
    connections.forEach(conn => {
      const gradient = ctx.createLinearGradient(conn.start.x, conn.start.y, conn.end.x, conn.end.y);
      gradient.addColorStop(0, conn.color + '22');
      gradient.addColorStop(0.5, conn.color + '05');
      gradient.addColorStop(1, conn.color + '11');

      ctx.beginPath();
      ctx.strokeStyle = gradient;
      ctx.moveTo(conn.start.x, conn.start.y);
      ctx.lineTo(conn.end.x, conn.end.y);
      ctx.stroke();
    });
  }

  // 3. Draw Pulses (Data Packets)
  pulses = pulses.filter(p => p.progress < 1);
  pulses.forEach(p => {
    p.progress += p.speed;
    const x = p.start.x + (p.end.x - p.start.x) * p.progress;
    const y = p.start.y + (p.end.y - p.start.y) * p.progress;

    ctx.beginPath();
    const glow = ctx.createRadialGradient(x, y, 0, x, y, 4);
    glow.addColorStop(0, '#fff');
    glow.addColorStop(1, p.color + '00');
    ctx.fillStyle = glow;
    ctx.arc(x, y, 4, 0, Math.PI * 2);
    ctx.fill();

    // Trailing spark
    ctx.beginPath();
    ctx.fillStyle = p.color + '88';
    ctx.arc(x, y, 1.5, 0, Math.PI * 2);
    ctx.fill();
  });
}

function animate(timestamp) {
  animationFrameId = requestAnimationFrame(animate);
  drawNeuralNetwork(timestamp);
}

/* ── Simulation ── */
const CONTEXT_MESSAGES = [
  "LEDGER_HASH_VERIFIED",
  "FIREDANCER_GHOSTING_AUDIT",
  "EXACTLY_MARKLE_ROOT_SYNC",
  "TAINT_SCRUB_COMPLETE",
  "FORENSIC_MEMORY_DUMP",
  "Z3_PROOF_COMPILATION_PASS",
  "SAGA_CONTRACT_COMMITTED",
  "CRYPTO_CHAIN_VALID",
  "BITFLOW_FEE_BYPASS_DETECTION",
  "EXERGY_YIELD_CALCULATED"
];

function startContextSimulation() {
  setInterval(() => {
    const activeHelpers = ARCHITECT_HELPERS.filter(h => h.status !== 'dormant');
    const sampleSize = Math.max(1, Math.floor(activeHelpers.length * 0.15));
    const targets = activeHelpers.sort(() => 0.5 - Math.random()).slice(0, sampleSize);

    targets.forEach(agent => {
      if (agent.context.state === 'synchronized') {
        updateAgentContext(agent);

        // Context Exchange (Talking to others)
        if (activeFilter === 'all' && agent.connectsTo && Math.random() > 0.6) {
          const targetId = agent.connectsTo[Math.floor(Math.random() * agent.connectsTo.length)];
          const target = ARCHITECT_HELPERS.find(h => h.id === targetId);

          if (target && target.status !== 'dormant') {
            createPulse(agent.id, targetId, agent.domain.color);
            addLogLine(agent.id, `PUSH_CTX -> ${target.name.split(' ')[0].toUpperCase()}`);

            // Interaction logic: Pressure Contagion
            if (parseInt(agent.context.memory) > 65 && target.context.state === 'synchronized') {
              const leakage = Math.floor(Math.random() * 5 + 2);
              const targetMem = parseInt(target.context.memory);
              target.context.memory = `${Math.min(100, targetMem + leakage)}%`;
              addLogLine(target.id, `RECV_LEAKAGE <- ${agent.name.split(' ')[0].toUpperCase()}`);
              syncAgentUI(target);
            }
          }
        }
      }
    });
  }, 3000);
}

function updateAgentContext(agent) {
  if (!agent.context) return;

  const memNum = parseInt(agent.context.memory);
  // Drift scales with global system stress (Entropy factor)
  const stressMultiplier = 1 + (systemStress / 100);
  const drift = (agent.status === 'active' ? Math.floor(Math.random() * 8) : Math.floor(Math.random() * 3)) * stressMultiplier;
  const newMem = Math.min(100, memNum + Math.round(drift));
  agent.context.memory = `${newMem}%`;

  if (newMem > 90) {
    agent.context.state = 'overflow';
    addLogLine(agent.id, "STATUS: CRITICAL_PRESSURE_O_LEVEL");
    setTimeout(() => {
      if (agent.context.state === 'overflow') startResolution(agent);
    }, 1500);
  } else if (newMem > 65 && agent.context.state === 'synchronized' && Math.random() > 0.7) {
    // Proactive context management
    startScrubbing(agent);
  } else if (Math.random() > 0.85) {
    if (Math.random() > 0.95) {
      // Periodic Taint Signature (AGENTS.md Compliance)
      const taint = `TAINT:${String(agent.id).substring(0,4)}:${performance.now().toString(36)}`;
      addLogLine(agent.id, `SIG_VERIFY: ${taint}`);
    } else {
      const msg = CONTEXT_MESSAGES[Math.floor(Math.random() * CONTEXT_MESSAGES.length)];
      addLogLine(agent.id, msg);
    }
  }

  syncAgentUI(agent);
}

/* ── Dashboard Telemetry ── */
function startDashboardTelemetry() {
  setInterval(updateGlobalMetrics, 2000);

  setInterval(() => {
    const rateEl = document.getElementById('dash-rate');
    if (rateEl) {
      rateEl.innerHTML = `${(crystallizationCount / 5).toFixed(1)}<small>hz</small>`;
    }
    crystallizationCount = 0;
  }, 5000);
}

function updateGlobalMetrics() {
  const helpersWithContext = ARCHITECT_HELPERS.filter(h => h.context);
  if (helpersWithContext.length === 0) return;

  const totalMem = helpersWithContext.reduce((acc, h) => acc + parseInt(h.context.memory), 0);
  const avgMem = Math.round(totalMem / helpersWithContext.length);

  // Calculate System Stress
  const overflowCount = helpersWithContext.filter(h => h.context.state === 'overflow').length;
  systemStress = Math.min(100, Math.round((avgMem * 0.7) + (overflowCount * 15)));

  const syncedCount = helpersWithContext.filter(h => h.context.state === 'synchronized').length;
  const syncPercent = Math.round((syncedCount / helpersWithContext.length) * 100);

  const memVal = document.getElementById('dash-memory');
  const memBar = document.getElementById('bar-memory');
  const syncVal = document.getElementById('dash-sync');
  const syncBar = document.getElementById('bar-sync');
  const stressVal = document.getElementById('dash-stress');
  const stressBar = document.getElementById('bar-stress');
  const rateVal = document.getElementById('dash-rate');

  if (memVal) memVal.textContent = `${avgMem}%`;
  if (memBar) memBar.style.width = `${avgMem}%`;
  if (syncVal) syncVal.textContent = `${syncPercent}%`;
  if (syncBar) syncBar.style.width = `${syncPercent}%`;

  if (stressVal) stressVal.textContent = `${systemStress}%`;
  if (stressBar) stressBar.style.width = `${systemStress}%`;

  if (rateVal) {
    const rate = (10 - (systemStress / 10)).toFixed(1);
    rateVal.innerHTML = `${rate}<small>hz</small>`;
  }

  // Update section ambient glow based on stress
  const section = document.getElementById('architect-swarm');
  if (section) {
    const stressColor = systemStress > 70 ? 'rgba(229, 62, 62, 0.08)' : 'rgba(43, 59, 229, 0.04)';
    section.style.setProperty('--stress-glow', stressColor);
  }
}

function optimizeSwarm() {
  const helpersWithContext = ARCHITECT_HELPERS.filter(h => h.context);

  // 1. Logic: Reduce memory and clear overflows
  helpersWithContext.forEach(h => {
    const mem = parseInt(h.context.memory);
    if (mem > 30) {
      h.context.memory = Math.round(mem * 0.3) + '%';
      if (h.context.state === 'overflow') {
        h.context.state = 'scrubbing';
      }
    }
    syncAgentUI(h);
  });

  // 2. Visual: Massive pulse wave
  const centerAgent = ARCHITECT_HELPERS[Math.floor(ARCHITECT_HELPERS.length / 2)];
  ARCHITECT_HELPERS.forEach((h, i) => {
    if (i % 5 === 0) {
      setTimeout(() => {
        createPulse(centerAgent.id, h.id, '#2B3BE5'); // Standard blue for optimization
      }, i * 20);
    }
  });

  updateGlobalMetrics();
  saveSwarmState();
}

/* ── Sovereign Audit ── */
async function runSovereignAudit() {
  const auditBtn = document.getElementById('btn-swarm-audit');
  if (!auditBtn || auditBtn.classList.contains('auditing')) return;

  auditBtn.classList.add('auditing');
  auditBtn.innerHTML = '<span class="audit-spinner"></span> AUDITING...';

  // 1. Create audit overlay
  const overlay = createAuditOverlay();
  document.body.appendChild(overlay);
  setTimeout(() => overlay.classList.add('active'), 10);

  try {
    const logContainer = overlay.querySelector('.audit-log-window');
    const total = ARCHITECT_HELPERS.length;

    addLogLineToAudit(logContainer, "INITIALIZING_SOVEREIGN_AUDIT_V6");
    addLogLineToAudit(logContainer, "SCANNING_NEURAL_TOPOLOGY...");

    // 2. Visual Sweep through agents
    for (let i = 0; i < total; i++) {
      const agent = ARCHITECT_HELPERS[i];
      updateAuditProgress(overlay, i + 1, total, agent.name);

      // Visual focus on card if visible
      const card = document.querySelector(`.swarm-card[data-id="${agent.id}"]`);
      if (card) {
        card.classList.add('audit-focus');
        if (i % 5 === 0) card.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }

      await auditAgent(agent, logContainer);

      if (card) card.classList.remove('audit-focus');

      // Adjust speed based on tier (apex agents take longer to audit)
      const delay = agent.tier === 'apex' ? 200 : 30;
      await new Promise(r => setTimeout(r, delay));
    }

    // 3. Backend Integrity Check
    addLogLineToAudit(logContainer, "CONNECTING_TO_CORTEX_LEDGER...");
    const compliance = await fetchComplianceStatus();
    addLogLineToAudit(logContainer, `LEDGER_VALID: ${compliance.ledger_valid}`);
    addLogLineToAudit(logContainer, `COMPLIANCE_LEVEL: ${compliance.compliance_level}`);

    // 4. Finalize
    setTimeout(() => showAuditResult(overlay, compliance), 800);

  } catch (err) {
    console.error("Audit failed", err);
    addLogLineToAudit(overlay.querySelector('.audit-log-window'), `CRITICAL_ERROR: ${err.message}`, 'error');
  } finally {
    auditBtn.classList.remove('auditing');
    auditBtn.innerHTML = 'SOVEREIGN_AUDIT_λ';
  }
}

function createAuditOverlay() {
  const overlay = document.createElement('div');
  overlay.id = 'report-overlay';
  overlay.className = 'audit-overlay';
  overlay.innerHTML = `
    <div class="report-container audit-report-container">
      <button class="report-close">&times;</button>
      <div class="report-header">
        <div class="report-reality-badge">C5-REAL</div>
        <h1>SOVEREIGN_AUDIT</h1>
        <div class="report-subtitle">Neural Integrity Verification Protocol</div>
      </div>

      <div class="audit-progress-section">
        <div class="audit-progress-header">
          <span class="audit-progress-text">SCANNING AGENTS...</span>
          <span class="audit-progress-percent">0%</span>
        </div>
        <div class="audit-progress-bar-wrap">
          <div class="audit-progress-bar"></div>
        </div>
        <div class="audit-current-agent">Initializing...</div>
      </div>

      <div class="audit-log-window"></div>

      <div class="audit-results-area" style="display: none;">
        <div class="section-divider">VERIFICATION_RESULT</div>
        <div class="audit-result-card">
          <div class="result-status-row">
            <span class="result-status-label">STATUS:</span>
            <span class="result-status-value status-compliant">PASSED</span>
          </div>
          <div class="result-metrics-grid">
            <div class="res-metric">
              <span class="res-label">LEDGER_VALID</span>
              <span class="res-value" id="res-ledger">TRUE</span>
            </div>
            <div class="res-metric">
              <span class="res-label">TRUST_SCORE</span>
              <span class="res-value" id="res-trust">0.99</span>
            </div>
            <div class="res-metric">
              <span class="res-label">COMPLIANCE</span>
              <span class="res-value" id="res-compliance">ALPHA</span>
            </div>
          </div>
          <div class="merkle-proof-row">
            <span class="merkle-label">MERKLE_ROOT:</span>
            <span class="merkle-value" id="res-merkle">0x...</span>
          </div>
        </div>
        <div class="audit-actions">
          <button class="btn-certify" id="btn-download-cert">GENERATE_CERTIFICATE_Ω</button>
        </div>
      </div>
    </div>
  `;

  overlay.querySelector('.report-close').addEventListener('click', () => {
    overlay.classList.remove('active');
    setTimeout(() => overlay.remove(), 400);
  });

  return overlay;
}

function updateAuditProgress(overlay, current, total, agentName) {
  const percent = Math.round((current / total) * 100);
  const bar = overlay.querySelector('.audit-progress-bar');
  const text = overlay.querySelector('.audit-progress-percent');
  const currentEl = overlay.querySelector('.audit-current-agent');

  if (bar) bar.style.width = `${percent}%`;
  if (text) text.textContent = `${percent}%`;
  if (currentEl) currentEl.textContent = `AUDITING: ${agentName.toUpperCase()}`;
}

async function auditAgent(agent, logContainer) {
  const status = agent.context ? agent.context.state : 'unknown';
  const taint = Math.random().toString(36).substring(2, 10).toUpperCase();

  let logType = 'info';
  let message = `AGENT_${agent.id} [${agent.name}]: OK | TAINT_${taint}`;

  if (status === 'overflow') {
    logType = 'warning';
    message = `AGENT_${agent.id} [${agent.name}]: PRESSURE_DETECTED | RESOLVING...`;
  } else if (agent.status === 'dormant') {
    message = `AGENT_${agent.id} [${agent.name}]: STANDBY_MODE`;
  }

  addLogLineToAudit(logContainer, message, logType);
}

function addLogLineToAudit(container, text, type = 'info') {
  if (!container) return;
  const line = document.createElement('div');
  line.className = `audit-log-line log-${type}`;
  const timestamp = new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  line.innerHTML = `<span class="log-ts">[${timestamp}]</span> ${text}`;
  container.appendChild(line);
  container.scrollTop = container.scrollHeight;
}

function showAuditResult(overlay, compliance) {
  const progressSection = overlay.querySelector('.audit-progress-section');
  const resultsArea = overlay.querySelector('.audit-results-area');

  if (progressSection) progressSection.style.display = 'none';
  if (resultsArea) {
    resultsArea.style.display = 'block';
    resultsArea.classList.add('reveal');

    // Update values
    overlay.querySelector('#res-ledger').textContent = compliance.ledger_valid ? 'TRUE' : 'FALSE';
    overlay.querySelector('#res-trust').textContent = compliance.total_trust_score.toFixed(2);
    overlay.querySelector('#res-compliance').textContent = compliance.compliance_level.split('-')[1] || 'ALPHA';
    overlay.querySelector('#res-merkle').textContent = compliance.merkle_root || '0x...';

    const statusVal = overlay.querySelector('.result-status-value');
    statusVal.textContent = compliance.status.toUpperCase();
    statusVal.className = `result-status-value status-${compliance.status}`;

    // Hook up download button
    const downloadBtn = overlay.querySelector('#btn-download-cert');
    if (downloadBtn) {
      downloadBtn.onclick = async () => {
        downloadBtn.textContent = 'GENERATING...';
        downloadBtn.disabled = true;
        await generateSovereignCertificate(compliance);
        downloadBtn.textContent = 'CERTIFICATE_DOWNLOADED';
        setTimeout(() => {
          downloadBtn.textContent = 'GENERATE_CERTIFICATE_Ω';
          downloadBtn.disabled = false;
        }, 2000);
      };
    }
  }
}

function syncAgentUI(agent) {
  const card = document.querySelector(`.swarm-card[data-id="${agent.id}"]`);
  const ctxEl = document.querySelector(`.swarm-context-mgmt[data-agent-id="${agent.id}"]`);
  if (!ctxEl) return;

  const stateEl = ctxEl.querySelector('[data-ctx-field="state"]');
  const memoryEl = ctxEl.querySelector('[data-ctx-field="memory"]');
  const syncEl = ctxEl.querySelector('[data-ctx-field="sync"]');
  const resBar = ctxEl.querySelector('[data-ctx-field="res-bar"]');

  if (stateEl) {
    stateEl.textContent = agent.context.state.toUpperCase();
    stateEl.className = `ctx-status status-${agent.context.state}`;
  }
  if (memoryEl) memoryEl.textContent = agent.context.memory;
  if (syncEl) syncEl.textContent = agent.context.lastCrystallization;
  if (resBar) resBar.style.width = `${agent.context.resolution || 0}%`;

  if (card) {
    card.dataset.status = agent.context.state;

    // Manage state classes
    card.classList.remove('overflow', 'resolving', 'scrubbing', 'crystallizing');
    if (agent.context.state !== 'synchronized') {
      card.classList.add(agent.context.state);
    }
  }
}

function updateCount(el) {
  if (!el) return;
  const active = getActiveHelpers().length;
  const total = getHelperCount();
  el.textContent = `${active}/${total} ACTIVE`;
}
