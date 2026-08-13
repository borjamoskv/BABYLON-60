// C5-REAL EXERGY CERTIFIED
// ═══════════════════════════════════════════════════════════
// AGENTS.archi — Forensic Audit Request
// Cloudflare Pages Function · Web Platform Runtime
// POST /api/audit-request
// Body: { target, email, depth, parameters }
// Returns: { success: true, requestId }
// ═══════════════════════════════════════════════════════════

const ALLOWED_DEPTHS = new Set(['surface', 'deep', 'adversarial']);
const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
const CORS_HEADERS = {
  'Access-Control-Allow-Origin': 'https://agents.archi',
  'Access-Control-Allow-Methods': 'POST, OPTIONS',
  'Access-Control-Allow-Headers': 'Content-Type',
};

// Web Crypto API SHA-256 (available in all CF Workers runtimes)
async function sha256hex(text) {
  const buf = await crypto.subtle.digest('SHA-256', new TextEncoder().encode(text || ''));
  return Array.from(new Uint8Array(buf)).map(b => b.toString(16).padStart(2, '0')).join('');
}

function cleanText(value, maxLength) {
  if (typeof value !== 'string') return '';
  return value.replace(/\s+/g, ' ').trim().slice(0, maxLength);
}

async function createRequestId(payload) {
  const digest = (await sha256hex(JSON.stringify(payload))).slice(0, 12).toUpperCase();
  const day = new Date(payload.ts).toISOString().slice(0, 10).replaceAll('-', '');
  return `ARCHI-${day}-${digest}`;
}

export async function onRequestOptions() {
  return new Response(null, { status: 204, headers: CORS_HEADERS });
}

export async function onRequestPost({ request }) {
  try {
    const body = await request.json().catch(() => ({}));
    const target     = cleanText(body.target,     280);
    const email      = cleanText(body.email,       120).toLowerCase();
    const depth      = cleanText(body.depth,        32);
    const parameters = cleanText(body.parameters, 2000);

    if (target.length < 4)          return jsonError(400, 'Target is required');
    if (!EMAIL_RE.test(email))       return jsonError(400, 'Valid email is required');
    if (!ALLOWED_DEPTHS.has(depth)) return jsonError(400, 'Invalid verification depth');

    const ts        = new Date().toISOString();
    const requestId = await createRequestId({ target, email, depth, parameters, ts });
    const paramHash = await sha256hex(parameters);

    // Structured log — visible in Cloudflare Dashboard → Logs
    console.log(JSON.stringify({
      event:           'forensic_audit_request',
      requestId,
      target,
      email,
      depth,
      parametersHash:  paramHash,
      parametersBytes: new TextEncoder().encode(parameters).length,
      ts,
      source: request.headers.get('referer') || 'direct',
    }));

    return jsonOk({ success: true, requestId, mode: 'experimental_sandbox' });
  } catch (err) {
    console.error('audit-request error', err?.message);
    return jsonError(500, 'Internal server error');
  }
}

// ── Helpers ───────────────────────────────────────────────
function jsonOk(data) {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
  });
}

function jsonError(status, message) {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: { ...CORS_HEADERS, 'Content-Type': 'application/json' },
  });
}
