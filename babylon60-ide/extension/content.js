(() => {
  if (window.__b60AlcoveMounted) return;
  window.__b60AlcoveMounted = true;
  const bar = document.createElement('div');
  bar.id = 'b60-alcove-bar';
  const read = document.createElement('div');
  read.id = 'b60-alcove-readout';
  read.textContent = 'MOSKV-1 · …';
  document.documentElement.appendChild(bar);
  document.documentElement.appendChild(read);
  const paint = (snap) => {
    if (!snap || !snap.online) {
      bar.dataset.state = 'offline';
      read.textContent = 'MOSKV-1 · backend offline (localhost:8060)';
      return;
    }
    const reds = snap.repo?.reds || 0;
    const ambers = snap.repo?.ambers || 0;
    bar.dataset.state = reds ? 'alert' : ambers ? 'warn' : 'ok';
    const repo = snap.repo ? `${snap.repo.name}@${snap.repo.branch ?? '—'}` : '—';
    const lineage = reds ? ' ⚠ linaje' : ambers ? ' △' : ' ✓';
    read.textContent = `MOSKV-1 · ${repo}${lineage} · ledger ${snap.entries ?? '—'} · L:${snap.lamport ?? '—'}`;
  };
  const load = () => {
    try {
      chrome.storage.session.get('b60snapshot', (r) => {
        if (chrome.runtime.lastError || !r?.b60snapshot) {
          chrome.storage.local.get('b60snapshot', (r2) => paint(r2?.b60snapshot));
          return;
        }
        paint(r.b60snapshot);
      });
    } catch {  }
  };
  load();
  try {
    chrome.storage.onChanged.addListener((changes) => {
      if (changes.b60snapshot) paint(changes.b60snapshot.newValue);
    });
  } catch {  }
  try { chrome.runtime.sendMessage({ type: 'b60-refresh' }, () => void chrome.runtime.lastError); } catch {  }
})();
