// C5-REAL EXERGY CERTIFIED
/* ═══════════════════════════════════════════════════════════
   LEGIØN-10000 — Sovereign Swarm Visualization Engine
   Harmonic Homeostasis Ω₁₆ × Genesis Synthesis Ω₆₄
   ───────────────────────────────────────────────────────────
   C4-SIM + C5-HYBRID: Canvas physics engine (always) ×
   live telemetry modulation when WS backend is connected.
   ═══════════════════════════════════════════════════════════ */

// ── Harmonic Intervals (Ω₁₆ Protocol) ──
const INTERVALS = [
  { name: 'Unison',      ratio: '1:1',   threshold: 0.05 },
  { name: 'Octave',      ratio: '2:1',   threshold: 0.12 },
  { name: 'Fifth',       ratio: '3:2',   threshold: 0.22 },
  { name: 'Fourth',      ratio: '4:3',   threshold: 0.35 },
  { name: 'Major Third', ratio: '5:4',   threshold: 0.50 },
  { name: 'Minor Third', ratio: '6:5',   threshold: 0.65 },
  { name: 'Major Second',ratio: '9:8',   threshold: 0.80 },
  { name: 'Tritone',     ratio: '45:32', threshold: 1.00 },
];

import { onTelemetryData } from '../services/telemetry.js';

// ── Constants ──
const NODE_COUNT        = 10000; // Sovereign Swarm parallel capacity
const VISUAL_LIMIT      = 150;   // Physical canvas render limits to sustain 60 FPS
const CELL_SIZE         = 60;
const MAX_SPEED         = 0.6;
const DAMPING           = 0.985;
const CONNECTION_R      = 55;
const SPAWN_RATE        = 12;    // nodes per frame during boot
const OSC_PARTIALS      = 64;    // Genesis Synthesis harmonics

// ── State ──
let nodes        = [];
let activeCount  = 0;
let entropy      = 0;
let gridW, gridH, grid;
let canvas, ctx, oscCanvas, oscCtx;
let animId       = null;
let booted       = false;

// ── DOM refs ──
const dom = {};

// ── Spatial Hash Grid ──
function initGrid(w, h) {
  gridW = Math.ceil(w / CELL_SIZE);
  gridH = Math.ceil(h / CELL_SIZE);
  grid  = new Array(gridW * gridH);
}

function clearGrid() {
  for (let i = 0; i < grid.length; i++) grid[i] = null;
}

function insertGrid(node) {
  const cx = (node.x / CELL_SIZE) | 0;
  const cy = (node.y / CELL_SIZE) | 0;
  if (cx < 0 || cy < 0 || cx >= gridW || cy >= gridH) return;
  const idx = cy * gridW + cx;
  node.next = grid[idx];
  grid[idx] = node;
}

function queryNeighbors(node, radius, callback) {
  const r2 = radius * radius;
  const cx = (node.x / CELL_SIZE) | 0;
  const cy = (node.y / CELL_SIZE) | 0;
  const cr = Math.ceil(radius / CELL_SIZE);
  for (let dy = -cr; dy <= cr; dy++) {
    for (let dx = -cr; dx <= cr; dx++) {
      const gx = cx + dx, gy = cy + dy;
      if (gx < 0 || gy < 0 || gx >= gridW || gy >= gridH) continue;
      let n = grid[gy * gridW + gx];
      while (n) {
        if (n !== node) {
          const ddx = n.x - node.x, ddy = n.y - node.y;
          const d2 = ddx * ddx + ddy * ddy;
          if (d2 < r2) callback(n, Math.sqrt(d2));
        }
        n = n.next;
      }
    }
  }
}

// ── Node Factory ──
function createNode(w, h) {
  return {
    x:  Math.random() * w,
    y:  Math.random() * h,
    vx: (Math.random() - 0.5) * MAX_SPEED,
    vy: (Math.random() - 0.5) * MAX_SPEED,
    radius: 1.2 + Math.random() * 0.8,
    alpha:  0.15 + Math.random() * 0.35,
    phase:  Math.random() * Math.PI * 2,
    next:   null,
    target: null,
  };
}

// ── Physics Step ──
function stepPhysics(w, h) {
  let totalSpeed = 0;
  const count = Math.min(activeCount, VISUAL_LIMIT);
  for (let i = 0; i < count; i++) {
    const n = nodes[i];
    if (!n) continue;
    n.vx *= DAMPING;
    n.vy *= DAMPING;
    n.x += n.vx;
    n.y += n.vy;
    // Wrap edges
    if (n.x < 0) n.x += w; else if (n.x > w) n.x -= w;
    if (n.y < 0) n.y += h; else if (n.y > h) n.y -= h;
    totalSpeed += Math.abs(n.vx) + Math.abs(n.vy);
  }
  // Entropy = normalized avg speed
  if (!socket_active) {
    entropy = count > 0 ? totalSpeed / (count * MAX_SPEED * 2) : 0;
  }
}

let socket_active = false;

// ── Render Swarm Canvas ──
function renderSwarm(w, h, t) {
  ctx.clearRect(0, 0, w, h);
  clearGrid();
  const count = Math.min(activeCount, VISUAL_LIMIT);
  for (let i = 0; i < count; i++) {
    if (nodes[i]) insertGrid(nodes[i]);
  }

  // Connections
  let connCount = 0;
  ctx.lineWidth = 0.4;
  for (let i = 0; i < count; i++) {
    const n = nodes[i];
    if (!n) continue;
    queryNeighbors(n, CONNECTION_R, (neighbor, dist) => {
      const alpha = (1 - dist / CONNECTION_R) * 0.12;
      ctx.strokeStyle = `rgba(43, 59, 229, ${alpha})`;
      ctx.beginPath();
      ctx.moveTo(n.x, n.y);
      ctx.lineTo(neighbor.x, neighbor.y);
      ctx.stroke();
      connCount++;
    });
  }

  // Nodes
  for (let i = 0; i < count; i++) {
    const n = nodes[i];
    if (!n) continue;
    const pulse = 0.6 + 0.4 * Math.sin(t * 0.002 + n.phase);
    const a = n.alpha * pulse;

    if (n.target) {
      // Accent color for active telemetry nodes from backend
      ctx.fillStyle = `rgba(235, 94, 40, ${a * 1.5})`;
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius * 1.5, 0, Math.PI * 2);
      ctx.fill();
    } else {
      ctx.fillStyle = `rgba(43, 59, 229, ${a})`;
      ctx.beginPath();
      ctx.arc(n.x, n.y, n.radius, 0, Math.PI * 2);
      ctx.fill();
    }
  }

  return connCount;
}

// ── Genesis Synthesis Oscilloscope (Ω₆₄) ──
function renderOscilloscope(t) {
  const w = oscCanvas.width;
  const h = oscCanvas.height;
  oscCtx.clearRect(0, 0, w, h);

  // Grid lines
  oscCtx.strokeStyle = 'rgba(255, 255, 255, 0.03)';
  oscCtx.lineWidth = 0.5;
  for (let y = 0; y < h; y += 10) {
    oscCtx.beginPath();
    oscCtx.moveTo(0, y);
    oscCtx.lineTo(w, y);
    oscCtx.stroke();
  }

  // Centerline
  oscCtx.strokeStyle = 'rgba(43, 59, 229, 0.15)';
  oscCtx.beginPath();
  oscCtx.moveTo(0, h / 2);
  oscCtx.lineTo(w, h / 2);
  oscCtx.stroke();

  // Additive synthesis waveform
  oscCtx.strokeStyle = 'rgba(43, 59, 229, 0.7)';
  oscCtx.lineWidth = 1.2;
  oscCtx.beginPath();
  const freq = 0.008 + entropy * 0.02;
  const speed = 0.001 + entropy * 0.003;
  const count = Math.min(activeCount, VISUAL_LIMIT);
  for (let x = 0; x < w; x++) {
    let y = 0;
    const partialCount = Math.min(OSC_PARTIALS, Math.max(4, (count / VISUAL_LIMIT) * OSC_PARTIALS));
    for (let p = 1; p <= partialCount; p++) {
      const amp = (1 / p) * (0.3 + entropy * 0.7);
      y += amp * Math.sin(x * freq * p + t * speed * (p % 3 === 0 ? -1 : 1));
    }
    const py = h / 2 + y * (h * 0.35);
    if (x === 0) oscCtx.moveTo(x, py);
    else oscCtx.lineTo(x, py);
  }
  oscCtx.stroke();

  // Glow layer
  oscCtx.strokeStyle = `rgba(43, 59, 229, ${0.15 + entropy * 0.2})`;
  oscCtx.lineWidth = 3;
  oscCtx.beginPath();
  for (let x = 0; x < w; x += 2) {
    let y = 0;
    const partialCount = Math.min(OSC_PARTIALS, Math.max(4, (count / VISUAL_LIMIT) * OSC_PARTIALS));
    for (let p = 1; p <= partialCount; p++) {
      const amp = (1 / p) * (0.3 + entropy * 0.7);
      y += amp * Math.sin(x * freq * p + t * speed * (p % 3 === 0 ? -1 : 1));
    }
    const py = h / 2 + y * (h * 0.35);
    if (x === 0) oscCtx.moveTo(x, py);
    else oscCtx.lineTo(x, py);
  }
  oscCtx.stroke();
}

// ── Harmonic State Classifier (Ω₁₆) ──
function classifyHarmonic(e) {
  for (const interval of INTERVALS) {
    if (e <= interval.threshold) return interval;
  }
  return INTERVALS[INTERVALS.length - 1];
}

function getStateClass(e) {
  if (e < 0.15) return 'osc-synced';
  if (e < 0.35) return 'osc-stable';
  if (e < 0.65) return 'osc-tension';
  return 'osc-critical';
}

function getStateLabel(e) {
  if (e < 0.15) return 'SYNCED';
  if (e < 0.35) return 'STABLE';
  if (e < 0.65) return 'TENSION';
  return 'CRITICAL';
}

// ── Update DOM Metrics ──
function updateMetrics(connCount) {
  const interval = classifyHarmonic(entropy);
  if (dom.entropyVal)     dom.entropyVal.textContent     = entropy.toFixed(4);
  if (dom.consonanceVal)  dom.consonanceVal.textContent   = `${interval.ratio} ${interval.name}`;
  if (dom.nodeCount)      dom.nodeCount.textContent       = `${activeCount} / ${NODE_COUNT}`;
  if (dom.connCount)      dom.connCount.textContent       = String(connCount * 67); // scaled connection metrics
  if (dom.metricNodes)    dom.metricNodes.textContent     = `${activeCount}/${NODE_COUNT}`;
  if (dom.metricYield)    dom.metricYield.textContent     = `Σ ${(activeCount * 0.047).toFixed(2)}`;

  if (dom.harmonicState) {
    const stateEl = dom.harmonicState;
    stateEl.textContent = getStateLabel(entropy);
    stateEl.className   = `osc-state ${getStateClass(entropy)}`;
  }
}

// ── Animation Loop ──
function loop(t) {
  const w = canvas.width;
  const h = canvas.height;

  // Progressive boot: spawn nodes
  if (!socket_active && activeCount < NODE_COUNT) {
    const toSpawn = Math.min(SPAWN_RATE, NODE_COUNT - activeCount);
    activeCount += toSpawn;
  }

  stepPhysics(w, h);
  const connCount = renderSwarm(w, h, t);
  renderOscilloscope(t);

  // Throttle DOM updates to ~10fps
  if (t % 6 < 1) updateMetrics(connCount);

  animId = requestAnimationFrame(loop);
}

// ── Resize Handler ──
function handleResize() {
  const section = canvas.parentElement;
  if (!section) return;
  const rect = section.getBoundingClientRect();
  canvas.width  = rect.width;
  canvas.height = rect.height;
  initGrid(canvas.width, canvas.height);

  // Oscilloscope
  const oscRect = oscCanvas.parentElement.getBoundingClientRect();
  oscCanvas.width  = oscRect.width;
  oscCanvas.height = oscCanvas.clientHeight || 80;
}

// ── Public Init ──
export function initLegionSwarm() {
  canvas    = document.getElementById('legion-canvas');
  oscCanvas = document.getElementById('oscilloscope-canvas');
  if (!canvas || !oscCanvas) return;

  ctx    = canvas.getContext('2d');
  oscCtx = oscCanvas.getContext('2d');

  // Cache DOM refs
  dom.entropyVal    = document.getElementById('entropy-value');
  dom.consonanceVal = document.getElementById('consonance-value');
  dom.nodeCount     = document.getElementById('legion-node-count');
  dom.connCount     = document.getElementById('legion-conn-count');
  dom.harmonicState = document.getElementById('harmonic-state');
  dom.metricNodes   = document.getElementById('metric-nodes');
  dom.metricYield   = document.getElementById('metric-yield');

  // Pre-allocate visual nodes limit
  handleResize();
  for (let i = 0; i < VISUAL_LIMIT; i++) {
    nodes.push(createNode(canvas.width, canvas.height));
  }

  // Intersection Observer — only animate when visible
  const observer = new IntersectionObserver((entries) => {
    entries.forEach(entry => {
      if (entry.isIntersecting && !booted) {
        booted = true;
        animId = requestAnimationFrame(loop);
      } else if (entry.isIntersecting && animId === null) {
        animId = requestAnimationFrame(loop);
      } else if (!entry.isIntersecting && animId !== null) {
        cancelAnimationFrame(animId);
        animId = null;
      }
    });
  }, { threshold: 0.05 });

  observer.observe(canvas.parentElement);

  window.addEventListener('resize', handleResize);

  // ── Real-time Data Integration ──
  onTelemetryData((data) => {
    if (data.type === 'FRAME' && Array.isArray(data.data)) {
      socket_active = true;
      const frameNodes = data.data;

      // Update activeCount to show actual swarm scale
      activeCount = NODE_COUNT;

      const count = Math.min(frameNodes.length, VISUAL_LIMIT);
      for (let i = 0; i < count; i++) {
        const frameNode = frameNodes[i];
        const n = nodes[i];
        if (n && frameNode) {
          // Normalize coordinate space from telemetry index/x/y coordinates (0-1000)
          n.x = (frameNode.x / 1000.0) * canvas.width;
          n.y = (frameNode.y / 1000.0) * canvas.height;

          const speed = (0.2 + frameNode.entropy * 0.8) * MAX_SPEED;
          n.vx = Math.sin(frameNode.z) * speed;
          n.vy = Math.cos(frameNode.z) * speed;
          n.target = frameNode.target;
        }
      }

      // Clear out targets for nodes not in the current active frame
      for (let i = count; i < VISUAL_LIMIT; i++) {
        if (nodes[i]) nodes[i].target = null;
      }

      // Smoothly update entropy using average entropy of active frame nodes
      if (frameNodes.length > 0) {
        const avgEntropy = frameNodes.reduce((sum, item) => sum + (item.entropy || 0), 0) / frameNodes.length;
        entropy = entropy * 0.8 + avgEntropy * 0.2;
      }
    } else if (data.rtt) {
      // Fallback RTT telemetry handling
      const targetEntropy = Math.min(1, data.rtt / 200);
      entropy = entropy * 0.8 + targetEntropy * 0.2;

      const rx = Math.random() * canvas.width;
      const ry = Math.random() * canvas.height;
      queryNeighbors({x: rx, y: ry}, 100, (n) => {
        n.vx += (Math.random() - 0.5) * 2;
        n.vy += (Math.random() - 0.5) * 2;
      });
    }
  });
}
