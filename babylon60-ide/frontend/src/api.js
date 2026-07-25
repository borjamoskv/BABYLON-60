const API_BASE = "";
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
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || res.statusText);
  }
  return res.json();
}
export function connectWebSocket(path, onMessage, onError) {
  const protocol = location.protocol === "https:" ? "wss:" : "ws:";
  const controller = { closed: false, ws: null };
  const dial = () => {
    if (controller.closed) return;
    const ws = new WebSocket(`${protocol}//${location.host}${path}`);
    controller.ws = ws;
    ws.onmessage = (e) => {
      let data;
      try {
        data = JSON.parse(e.data);
      } catch {
        return;
      }
      onMessage(data);
    };
    ws.onerror = (e) => onError?.(e);
    ws.onclose = () => {
      if (!controller.closed) setTimeout(dial, 3000);
    };
  };
  controller.close = () => {
    controller.closed = true;
    try {
      controller.ws?.close();
    } catch {}
  };
  dial();
  return controller;
}
export const isTauri =
  typeof window !== "undefined" &&
  (window.__TAURI__ !== undefined ||
    window.__TAURI_INTERNALS__ !== undefined ||
    window.__TAURI_METADATA__ !== undefined);
