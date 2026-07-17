// BABYLON60 IDE — Hybrid API client (Tauri IPC + HTTP Fallback)
const API_BASE = '';
export const isTauri = window.__TAURI_INTERNALS__ !== undefined || window.__TAURI__ !== undefined;

// Attempt to load Tauri core invoke dynamically to avoid breaking the web build
let invoke = null;
if (isTauri) {
  import('@tauri-apps/api/core').then(module => {
    invoke = module.invoke;
  }).catch(err => console.error("Tauri IPC not available:", err));
}

export async function get(path) {
  const res = await fetch(`${API_BASE}${path}`);
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

export async function post(path, body) {
  const res = await fetch(`${API_BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}

export async function appendEvent(eventType, payload) {
  if (isTauri && invoke) {
    return await invoke('append_ledger_event', { eventType, payload });
  } else {
    return await post('/api/ledger/events', { event_type: eventType, payload });
  }
}

export async function getEvents(limit = 50) {
  if (isTauri && invoke) {
    return await invoke('get_ledger_events', { limit });
  } else {
    return await get(`/api/ledger/events?limit=${limit}`);
  }
}

export function connectWebSocket(path, onMessage, onError) {
  if (isTauri) {
    // Tauri doesn't use WebSocket telemetry in the same way, we rely on IPC events.
    // Stub this out for now to prevent connection loops.
    return { close: () => {} };
  }
  
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${protocol}//${location.host}${path}`);
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  ws.onerror = (e) => onError?.(e);
  ws.onclose = () => {
    setTimeout(() => connectWebSocket(path, onMessage, onError), 3000);
  };
  return ws;
}
