// C5-REAL EXERGY CERTIFIED
/* ═══════════════════════════════════════════════════════════
   AGENTS.archi — Commission Request Component
   Interactive Forensic Target Submission
   ═══════════════════════════════════════════════════════════ */

export function initCommissionModal() {
  const btn = document.getElementById('btn-commission');
  if (!btn) return;

  btn.addEventListener('click', () => {
    openCommissionModal();
  });
}

const AUDIT_CONTACT_EMAIL = 'borja@cortexpersist.com';
const DEPTH_LABELS = {
  surface: 'Surface Audit (C4-Verification)',
  deep: 'Deep Formal Verification (ASL-Verified)',
  adversarial: 'Adversarial Stress Test (LEGIØN-1 Strike)',
};

function openCommissionModal() {
  const overlay = document.createElement('div');
  overlay.className = 'commission-overlay';
  overlay.innerHTML = `
    <div class="commission-container reveal">
      <button class="commission-close">&times;</button>
      <div class="commission-header">
        <div class="reality-badge">C5-TARGET · MODO EXPERIMENTO</div>
        <h2>Forensic Commission</h2>
        <p>Submit agentic infrastructure for formal verification or adversarial audit.</p>
        <div style="background: rgba(245, 158, 11, 0.08); border: 1px dashed rgba(245, 158, 11, 0.4); border-radius: 4px; padding: 10px; margin-top: 14px; font-size: 0.78rem; color: #FCD34D; line-height: 1.4;">
          ⚠️ <strong>Aviso de Entorno Experimental:</strong> AGENTS.archi es un laboratorio en fase de pruebas. El formulario procesa solicitudes en modo demostración/sandbox y no constituye oferta contractual de servicio.
        </div>
      </div>

      <form id="commission-form" class="commission-form">
        <div class="form-group">
          <label>Target Identifier (Domain/Repo/Contract)</label>
          <input type="text" name="target" placeholder="e.g. 0x... or github.com/org/repo" required>
        </div>

        <div class="form-group">
          <label>Encrypted Contact Alias (Email)</label>
          <input
            type="text"
            name="email"
            inputmode="email"
            autocomplete="email"
            pattern="[^\\s@]+@[^\\s@]+\\.[^\\s@]+"
            placeholder="agent@protocol.io"
            required
          >
        </div>

        <div class="form-group">
          <label>Verification Depth</label>
          <select name="depth">
            <option value="surface">${DEPTH_LABELS.surface}</option>
            <option value="deep">${DEPTH_LABELS.deep}</option>
            <option value="adversarial">${DEPTH_LABELS.adversarial}</option>
          </select>
        </div>

        <div class="form-group">
          <label>Mission Parameters / Critical Invariants</label>
          <textarea name="parameters" placeholder="Define the 'never' and 'always' properties for this agent..."></textarea>
        </div>

        <div class="form-footer">
          <div class="submission-meta">
            <span class="meta-label">Estimated Exergy:</span>
            <span class="meta-value" id="exergy-calc">Waiting for input...</span>
          </div>
          <button type="submit" class="btn btn-primary">Initialize Strike Pipeline</button>
        </div>
      </form>

      <div id="submission-result" class="submission-result" style="display: none;">
        <div class="result-icon">⬡</div>
        <h3 id="result-title">Target Registered</h3>
        <p id="result-text">Request committed. Send the prepared briefing to open the forensic channel.</p>
        <div class="result-hash" id="target-hash"></div>
        <div class="request-summary" id="request-summary"></div>
        <div class="result-actions">
          <a id="email-request-link" class="btn btn-primary" href="#">Open Email Draft</a>
          <button class="btn btn-outline close-result">Close Terminal</button>
        </div>
      </div>
    </div>
  `;

  document.body.appendChild(overlay);
  setTimeout(() => overlay.classList.add('active'), 10);

  const form = overlay.querySelector('#commission-form');
  const closeBtn = overlay.querySelector('.commission-close');
  const exergyCalc = overlay.querySelector('#exergy-calc');

  closeBtn.addEventListener('click', () => {
    overlay.classList.remove('active');
    setTimeout(() => overlay.remove(), 400);
  });

  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeBtn.click();
  });

  // Dynamic exergy calculation
  form.addEventListener('input', () => {
    const depth = form.depth.value;
    const target = form.target.value;
    if (!target) {
      exergyCalc.textContent = 'Waiting for target...';
      return;
    }
    const base = depth === 'adversarial' ? 500 : (depth === 'deep' ? 200 : 50);
    const rand = Math.floor(Math.random() * 20);
    exergyCalc.textContent = `${base + rand}W (Estimated)`;
  });

  form.addEventListener('submit', async (e) => {
    e.preventDefault();
    const btn = form.querySelector('button[type="submit"]');
    const originalText = btn.textContent;
    btn.disabled = true;
    btn.textContent = 'CRYSTALLIZING...';

    const formData = new FormData(form);
    const payload = {
      target: String(formData.get('target') || '').trim(),
      email: String(formData.get('email') || '').trim(),
      depth: String(formData.get('depth') || 'surface'),
      parameters: String(formData.get('parameters') || '').trim(),
    };

    try {
      const response = await submitAuditRequest(payload);
      renderResult(overlay, payload, response.requestId, true);
    } catch (error) {
      const requestId = createLocalRequestId(payload);
      renderResult(overlay, payload, requestId, false, error);
    } finally {
      btn.disabled = false;
      btn.textContent = originalText;
    }
  });
}

async function submitAuditRequest(payload) {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), 7000);

  try {
    const res = await fetch('/api/audit-request', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload),
      signal: controller.signal,
    });
    const data = await res.json().catch(() => ({}));
    if (!res.ok || !data.success) {
      throw new Error(data.error || 'Audit intake unavailable');
    }
    return data;
  } finally {
    clearTimeout(timeout);
  }
}

function renderResult(overlay, payload, requestId, apiAccepted, error) {
  const form = overlay.querySelector('#commission-form');
  const result = overlay.querySelector('#submission-result');
  const title = overlay.querySelector('#result-title');
  const text = overlay.querySelector('#result-text');
  const hash = overlay.querySelector('#target-hash');
  const summary = overlay.querySelector('#request-summary');
  const emailLink = overlay.querySelector('#email-request-link');
  const closeResult = overlay.querySelector('.close-result');
  const closeBtn = overlay.querySelector('.commission-close');

  form.style.display = 'none';
  result.style.display = 'flex';
  title.textContent = apiAccepted ? 'Target Registered' : 'Email Handoff Required';
  text.textContent = apiAccepted
    ? 'Request committed. Send the prepared briefing to open the forensic channel.'
    : `Local request prepared. ${error?.message || 'Server intake unavailable.'}`;
  hash.textContent = `request_id: ${requestId}`;
  summary.textContent = buildSummary(payload, requestId);
  emailLink.href = buildMailto(payload, requestId);
  closeResult.addEventListener('click', () => closeBtn.click(), { once: true });
}

function buildSummary(payload, requestId) {
  return [
    `request_id: ${requestId}`,
    `target: ${payload.target}`,
    `contact: ${payload.email}`,
    `depth: ${DEPTH_LABELS[payload.depth] || payload.depth}`,
    `parameters: ${payload.parameters || 'Not provided'}`,
  ].join('\n');
}

function buildMailto(payload, requestId) {
  const subject = `[AGENTS.archi] Forensic audit request ${requestId}`;
  const body = [
    'Forensic audit request',
    '',
    `Request ID: ${requestId}`,
    `Target: ${payload.target}`,
    `Contact: ${payload.email}`,
    `Depth: ${DEPTH_LABELS[payload.depth] || payload.depth}`,
    '',
    'Mission parameters / critical invariants:',
    payload.parameters || 'Not provided',
  ].join('\n');

  return `mailto:${AUDIT_CONTACT_EMAIL}?subject=${encodeURIComponent(subject)}&body=${encodeURIComponent(body)}`;
}

function createLocalRequestId(payload) {
  const seed = `${payload.target}|${payload.email}|${payload.depth}|${performance.now()}`;
  let hash = 0;
  for (let i = 0; i < seed.length; i += 1) {
    hash = (hash * 31 + seed.charCodeAt(i)) >>> 0;
  }
  return `ARCHI-${new Date().toISOString().slice(0, 10).replaceAll('-', '')}-${hash.toString(16).toUpperCase().padStart(8, '0')}`;
}
