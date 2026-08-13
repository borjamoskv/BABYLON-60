// C5-REAL EXERGY CERTIFIED
/* ═══════════════════════════════════════════════════════════
   AGENTS.archi — Sovereign Council Component v2
   ═══════════════════════════════════════════════════════════ */

import { getCouncilCore } from '../data/architectTemplate.js';

const COUNCIL_AGENTS = getCouncilCore();


const MISSION_MESSAGES = [
  { type: 'info',    text: 'Initializing Sovereign Forensic Protocol Ω₃...' },
  { type: 'cmd',     text: 'LEGIØN-1 heartbeat confirmed. Δt = 0.003s.' },
  { type: 'success', text: 'Byzantine Consensus achieved across 9 nodes.' },
  { type: 'warn',    text: 'Threat Vector [V09] attempting exfiltration bypass.' },
  { type: 'info',    text: 'Antigravity deploying SMT counter-measure...' },
  { type: 'success', text: 'Invariant proof complete. Zero-entropy maintained.' },
  { type: 'cmd',     text: 'Ouroboros Strike: target acquired — Firedancer V1.' },
  { type: 'success', text: 'Critical ghosting vulnerability verified via fd_accdb.' },
  { type: 'cmd',     text: 'Ouroboros Strike: target acquired — Exactly Protocol.' },
  { type: 'success', text: 'VerifiedAuditor delegate bypass confirmed. C5-REAL.' },
  { type: 'warn',    text: 'MCP supply-chain probe detected on Forensic-Unit-02.' },
  { type: 'info',    text: 'Network-Observer issuing isolation order for compromised tool.' },
  { type: 'success', text: 'Isolation complete. Swarm integrity at 100%.' },
  { type: 'cmd',     text: 'Forensic-Unit-01 executing 200-thread stress test on ASL engine.' },
  { type: 'success', text: 'ASL engine: 200/200 invariants held. C5-REAL confirmed.' },
  { type: 'info',    text: 'Archaeologist crystallizing new KI from session delta...' },
  { type: 'cmd',     text: 'Mariscal dispatching Antigravity → Kimi bridge task.' },
];

let hoveredNodeId = null;
let addLogMessageCallback = null;

export function initSovereignCouncil() {
  const grid = document.getElementById('council-grid');
  const log  = document.getElementById('council-log');
  if (!grid || !log) return;

  renderCouncilGrid(grid);
  startMissionLog(log);
  updateMetrics();
  initCouncilSVG();
}

/* ── Grid ── */
function renderCouncilGrid(container) {
  container.innerHTML = '';
  COUNCIL_AGENTS.forEach((agent, i) => {
    const node = document.createElement('div');
    node.className = 'council-node reveal';
    node.style.transitionDelay = `${i * 80}ms`;
    node.id = `node-${agent.id}`;

    const icon = document.createElement('div');
    icon.className = 'node-icon';
    icon.textContent = '⬡';

    const info = document.createElement('div');
    info.className = 'node-info';

    const nameEl = document.createElement('div');
    nameEl.className = 'node-name';
    nameEl.textContent = agent.name;

    const roleEl = document.createElement('div');
    roleEl.className = 'node-role';
    roleEl.textContent = agent.role;
    info.append(nameEl, roleEl);

    const statusWrap = document.createElement('div');
    statusWrap.className = 'node-status';

    const pulse = document.createElement('span');
    pulse.className = 'status-pulse';
    pulse.style.animationDuration = `${agent.pulse}s`;

    const statusText = document.createElement('span');
    statusText.className = 'status-text';
    statusText.textContent = agent.status.toUpperCase();
    statusWrap.append(pulse, statusText);

    node.append(icon, info, statusWrap);

    // Interactions
    node.addEventListener('mouseenter', () => {
      hoveredNodeId = agent.id;
      node.classList.add('active');
    });

    node.addEventListener('mouseleave', () => {
      hoveredNodeId = null;
      node.classList.remove('active');
    });

    node.addEventListener('click', () => {
      node.classList.add('speaking');
      setTimeout(() => node.classList.remove('speaking'), 1400);

      if (addLogMessageCallback) {
        addLogMessageCallback({
          type: 'cmd',
          text: `[AUTH] ${agent.name} (${agent.role}) executing tactical override.`
        });
        setTimeout(() => {
          addLogMessageCallback({
            type: 'success',
            text: `[AUTH] ${agent.name} sequence complete. Yield updated.`
          });
        }, 1200);
      }
    });

    container.appendChild(node);
  });
}

/* ── Mission Log with typewriter ── */
function startMissionLog(container) {
  let index = 0;
  let isTyping = false;
  const queue = [];

  const processQueue = () => {
    if (isTyping || queue.length === 0) return;
    isTyping = true;

    const msg = queue.shift();
    const div = document.createElement('div');
    div.className = `log-entry log-${msg.type}`;

    const ts = document.createElement('span');
    ts.className = 'log-time';
    ts.textContent = `[${new Date().toLocaleTimeString()}]`;
    div.appendChild(ts);
    div.appendChild(document.createTextNode(' '));

    const textNode = document.createElement('span');
    div.appendChild(textNode);
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;

    // Typewriter
    let charIdx = 0;
    const txt = msg.text;
    const type = () => {
      if (charIdx <= txt.length) {
        textNode.textContent = txt.slice(0, charIdx);
        charIdx++;
        setTimeout(type, 15);
      } else {
        isTyping = false;
        setTimeout(processQueue, 100);
      }
    };
    type();
  };

  addLogMessageCallback = (msg) => {
    queue.push(msg);
    processQueue();
  };

  const loopDefaultMessages = () => {
    if (!isTyping && queue.length === 0) {
      addLogMessageCallback(MISSION_MESSAGES[index % MISSION_MESSAGES.length]);
      index++;
    }
    setTimeout(loopDefaultMessages, Math.random() * 4000 + 3000);
  };

  loopDefaultMessages();
}

/* ── Metrics ── */
function updateMetrics() {
  const yieldEl = document.getElementById('metric-yield');
  if (!yieldEl) return;

  // σ = cumulative ops/s emitted by the simulation engine
  let σ = 0;
  const _intervalId = setInterval(() => {
    σ += Math.random() * 0.12 + 0.02;
    yieldEl.textContent = `Σ ${σ.toFixed(2)} ops/s`;
  }, 800);
  // _intervalId exposed here; attach to window.CORTEX_CLEANUP if needed.
  return _intervalId;
}

/* ── Animated SVG pulse lines ── */
function initCouncilSVG() {
  const svg = document.getElementById('council-svg');
  if (!svg) return;

  // Derive connections from COUNCIL_AGENTS
  const CONNECTIONS = [];
  COUNCIL_AGENTS.forEach((agent, i) => {
    agent.connectsTo.forEach(targetId => {
      const targetIndex = targetId - 1; // ID matches index + 1
      if (targetIndex >= 0 && targetIndex < COUNCIL_AGENTS.length) {
        // Prevent duplicates
        if (!CONNECTIONS.find(c => (c[0] === i && c[1] === targetIndex) || (c[1] === i && c[0] === targetIndex))) {
          CONNECTIONS.push([i, targetIndex]);
        }
      }
    });
  });

  // Particle pool for animated data flow
  const particles = [];

  function getCenter(node) {
    const svgRect = svg.getBoundingClientRect();
    const r = node.getBoundingClientRect();
    return {
      x: r.left - svgRect.left + r.width / 2,
      y: r.top  - svgRect.top  + r.height / 2,
    };
  }

  function spawnParticle(p1, p2, isHighlighted) {
    particles.push({
      p1, p2, t: 0,
      speed: isHighlighted ? (0.015 + Math.random() * 0.01) : (0.008 + Math.random() * 0.006),
      isHighlighted
    });
  }

  let lastSpawn = 0;

  function frame(ts) {
    const nodes = document.querySelectorAll('.council-node');
    if (nodes.length < 9) { requestAnimationFrame(frame); return; }

    const centers = Array.from(nodes).map(getCenter);
    svg.innerHTML = '';

    const hoveredIndex = hoveredNodeId ? hoveredNodeId - 1 : -1;

    // Static ring + cross lines
    CONNECTIONS.forEach(([i, j]) => {
      const a = centers[i]; const b = centers[j];
      const isConnectedToHover = hoveredIndex === i || hoveredIndex === j;
      const isHoverActive = hoveredIndex !== -1;

      const line = document.createElementNS('http://www.w3.org/2000/svg', 'line');
      line.setAttribute('x1', a.x); line.setAttribute('y1', a.y);
      line.setAttribute('x2', b.x); line.setAttribute('y2', b.y);

      if (isHoverActive) {
        if (isConnectedToHover) {
          line.setAttribute('stroke', 'rgba(43,59,229,0.8)');
          line.setAttribute('stroke-width', '1.5');
        } else {
          line.setAttribute('stroke', 'rgba(43,59,229,0.05)');
          line.setAttribute('stroke-width', '0.5');
        }
      } else {
        line.setAttribute('stroke', 'rgba(43,59,229,0.12)');
        line.setAttribute('stroke-width', '1');
      }

      svg.appendChild(line);
    });

    // Spawn new particle every ~600ms (faster if hovered)
    const spawnRate = hoveredNodeId ? 200 : 600;
    if (ts - lastSpawn > spawnRate) {
      if (hoveredNodeId) {
        // Spawn from hovered node to its connections
        const agent = COUNCIL_AGENTS[hoveredIndex];
        const targetId = agent.connectsTo[Math.floor(Math.random() * agent.connectsTo.length)];
        spawnParticle(centers[hoveredIndex], centers[targetId - 1], true);
      } else {
        const conn = CONNECTIONS[Math.floor(Math.random() * CONNECTIONS.length)];
        spawnParticle(centers[conn[0]], centers[conn[1]], false);
      }
      lastSpawn = ts;
    }

    // Draw + advance particles
    for (let k = particles.length - 1; k >= 0; k--) {
      const p = particles[k];
      p.t += p.speed;
      if (p.t >= 1) { particles.splice(k, 1); continue; }

      const x = p.p1.x + (p.p2.x - p.p1.x) * p.t;
      const y = p.p1.y + (p.p2.y - p.p1.y) * p.t;

      const dot = document.createElementNS('http://www.w3.org/2000/svg', 'circle');
      dot.setAttribute('cx', x); dot.setAttribute('cy', y);
      dot.setAttribute('r', p.isHighlighted ? '4' : '3');
      dot.setAttribute('fill', p.isHighlighted ? `rgba(255, 255, 255, ${1 - p.t})` : `rgba(43,59,229,${0.8 - p.t * 0.5})`);
      if (p.isHighlighted) {
        dot.setAttribute('filter', 'drop-shadow(0 0 4px rgba(43,59,229,0.8))');
      }
      svg.appendChild(dot);
    }

    requestAnimationFrame(frame);
  }

  // Start after nodes are in DOM
  setTimeout(() => requestAnimationFrame(frame), 600);
  window.addEventListener('resize', () => particles.length = 0);
}
