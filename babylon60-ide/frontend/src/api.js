// BABYLON60 IDE — API client
const API_BASE = '';

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

export function connectWebSocket(path, onMessage, onError) {
  const protocol = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${protocol}//${location.host}${path}`);
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  ws.onerror = (e) => onError?.(e);
  ws.onclose = () => {
    setTimeout(() => connectWebSocket(path, onMessage, onError), 3000);
  };
  return ws;
}
