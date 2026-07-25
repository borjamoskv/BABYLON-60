const BASE = "http://localhost:8060";
const ALT = "http://127.0.0.1:8060";
const POLL_ALARM = "b60-pulse";
async function fetchJSON(path) {
  for (const host of [BASE, ALT]) {
    try {
      const res = await fetch(`${host}${path}`, { cache: "no-store" });
      if (res.ok) return await res.json();
    } catch {}
  }
  return null;
}
async function pulse() {
  const [stats, sentinel] = await Promise.all([
    fetchJSON("/api/ledger/stats"),
    fetchJSON("/api/sentinel/status"),
  ]);
  const online = stats !== null || sentinel !== null;
  const reds = (sentinel?.warnings || []).filter(
    (w) => w.level === "red",
  ).length;
  const ambers = (sentinel?.warnings || []).filter(
    (w) => w.level === "amber",
  ).length;
  let color = "#3E3B4F";
  let text = "";
  if (online) {
    text = stats?.entries != null ? String(stats.entries) : "·";
    color = reds ? "#E3877E" : ambers ? "#E5B567" : "#86C79A";
  }
  try {
    await chrome.action.setBadgeText({ text });
    await chrome.action.setBadgeBackgroundColor({ color });
  } catch {}
  const snapshot = {
    online,
    ts: Date.now(),
    entries: stats?.entries ?? null,
    lamport: stats?.latest?.lamport_t ?? null,
    repo: sentinel
      ? {
          name: sentinel.repo_name,
          branch: sentinel.branch,
          head: sentinel.head,
          reds,
          ambers,
        }
      : null,
  };
  try {
    await chrome.storage.session.set({ b60snapshot: snapshot });
  } catch {
    try {
      await chrome.storage.local.set({ b60snapshot: snapshot });
    } catch {}
  }
}
chrome.runtime.onInstalled.addListener(() => {
  chrome.alarms.create(POLL_ALARM, { periodInMinutes: 0.5 });
  pulse();
});
chrome.runtime.onStartup?.addListener(() => {
  chrome.alarms.create(POLL_ALARM, { periodInMinutes: 0.5 });
  pulse();
});
chrome.alarms.onAlarm.addListener((a) => {
  if (a.name === POLL_ALARM) pulse();
});
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg?.type === "b60-refresh") {
    pulse().then(() => sendResponse({ ok: true }));
    return true;
  }
  return false;
});
