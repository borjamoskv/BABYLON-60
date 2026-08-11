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
  const controller = { closed: false, ws: null };

  const dial = () => {
    if (controller.closed) return;
    const ws = new WebSocket(`${protocol}//${location.host}${path}`);
    controller.ws = ws;
    ws.onmessage = (e) => {
      let data;
      try { data = JSON.parse(e.data); } catch { return; }
      onMessage(data);
    };
    ws.onerror = (e) => onError?.(e);
    ws.onclose = () => {
      // Reconnect only if not closed on purpose (avoids zombie sockets
      // piling up every time the user leaves the Swarm route).
      if (!controller.closed) setTimeout(dial, 3000);
    };
  };

  controller.close = () => {
    controller.closed = true;
    try { controller.ws?.close(); } catch { /* already closed */ }
  };

  dial();
  return controller;
}

// WebSocket RPC implementation (Replaces Tauri invoke)
export async function wsInvoke(command, args = {}) {
  return new Promise((resolve, reject) => {
    const ws = new WebSocket(`ws://127.0.0.1:4000/ws`);
    ws.onopen = () => {
      ws.send(JSON.stringify({ command, args }));
    };
    ws.onmessage = (e) => {
      try {
        const res = JSON.parse(e.data);
        if (res.error) reject(new Error(res.error));
        else resolve(res.result);
      } catch (err) {
        reject(err);
      } finally {
        ws.close();
      }
    };
    ws.onerror = (e) => reject(e);
  });
}
