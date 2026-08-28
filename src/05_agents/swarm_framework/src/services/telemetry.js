// C5-REAL EXERGY CERTIFIED
/* ═══════════════════════════════════════════════════════════
   AGENTS.archi — Telemetry Service
   ───────────────────────────────────────────────────────────
   WebSocket bridge to the MOSKV-10k-RS engine.
   Reality level: C5-HYBRID — active when WS backend present,
   graceful no-op in static/Cloudflare deployments without backend.
   ═══════════════════════════════════════════════════════════ */

let socket        = null;
let retryDelay    = 1000;        // starts at 1s
const MAX_DELAY   = 60_000;      // cap at 60s
const listeners   = new Set();

// Resolve URL from env (injected by Vite at build time) or skip
const WS_URL = import.meta.env.VITE_TELEMETRY_WS_URL ?? null;

export function connectTelemetry() {
  if (!WS_URL) {
    // No backend configured — telemetry is silent (C4-SIM only)
    return;
  }
  if (socket) return;

  console.log(`[TELEMETRY] Connecting to swarm engine: ${WS_URL}`);

  try {
    socket = new WebSocket(WS_URL);
  } catch (e) {
    console.warn('[TELEMETRY] WebSocket construction failed:', e);
    _scheduleRetry();
    return;
  }

  socket.onopen = () => {
    retryDelay = 1000; // reset backoff on success
    console.log('[TELEMETRY] [C5-HYBRID] Link established.');
  };

  socket.onmessage = (event) => {
    try {
      const data = JSON.parse(event.data);
      listeners.forEach(cb => cb(data));
    } catch (e) {
      console.error('[TELEMETRY] Parse error:', e);
    }
  };

  socket.onclose = () => {
    socket = null;
    _scheduleRetry();
  };

  socket.onerror = () => {
    // onclose fires after onerror — retry handled there
    socket = null;
  };
}

function _scheduleRetry() {
  const jitter = Math.random() * 1000;
  const delay  = Math.min(retryDelay + jitter, MAX_DELAY);
  retryDelay   = Math.min(retryDelay * 2, MAX_DELAY);
  console.warn(`[TELEMETRY] Reconnecting in ${(delay / 1000).toFixed(1)}s...`);
  setTimeout(connectTelemetry, delay);
}

/** Register a callback for incoming telemetry frames.
 *  Returns an unsubscribe function. */
export function onTelemetryData(callback) {
  listeners.add(callback);
  return () => listeners.delete(callback);
}
