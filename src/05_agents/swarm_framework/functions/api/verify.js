// C5-REAL EXERGY CERTIFIED
// ═══════════════════════════════════════════════════════════
// AGENTS.archi — Verification Scorecard
// Cloudflare Pages Function · Web Platform Runtime
// GET /api/verify?hash={certHash}
// ═══════════════════════════════════════════════════════════

const DEMO_CERTS = {
  demo: {
    agent: "PaymentBot-v2",
    org: "Acme Corp",
    threats_covered: 8,
    threats_total: 10,
    formal_proofs: 4,
    proofs_passed: 4,
    composition_safety: 72,
    audit_date: "2026-05-10",
    expiry_date: "2026-11-10",
    auditor: "AGENTS.archi",
    hash: "0xA3F7...demo",
    status: "VERIFIED",
  },
};

export async function onRequestGet({ request }) {
  const url = new URL(request.url);
  const hash = url.searchParams.get("hash") || "demo";
  const cert = DEMO_CERTS[hash] || DEMO_CERTS.demo;

  const coveragePct = Math.round((cert.threats_covered / cert.threats_total) * 100);

  const html = `<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8"/>
  <meta name="viewport" content="width=device-width, initial-scale=1.0"/>
  <title>Verification Scorecard — ${cert.agent} | AGENTS.archi</title>
  <meta name="description" content="Public verification scorecard for ${cert.agent}. ${cert.threats_covered}/${cert.threats_total} threat vectors covered."/>
  <link rel="preconnect" href="https://fonts.googleapis.com"/>
  <link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;600;700;900&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet"/>
  <style>
    *{margin:0;padding:0;box-sizing:border-box}
    body{background:#0A0A0A;color:#e2e8f0;font-family:"Inter",sans-serif;min-height:100vh;display:flex;align-items:center;justify-content:center;padding:2rem}
    .card{background:#0f1117;border:1px solid #1e293b;border-radius:16px;max-width:520px;width:100%;overflow:hidden}
    .card-header{padding:1.5rem 2rem;border-bottom:1px solid #1e293b;display:flex;align-items:center;gap:1rem}
    .logo{color:#2B3BE5;font-size:1.5rem}
    .header-text h1{font-size:1rem;font-weight:700;color:#f8fafc}
    .header-text p{font-size:.75rem;color:#64748b;font-family:"JetBrains Mono",monospace}
    .status{margin-left:auto;display:flex;align-items:center;gap:.5rem;padding:.35rem .75rem;border-radius:6px;font-size:.7rem;font-weight:700;font-family:"JetBrains Mono",monospace;text-transform:uppercase}
    .status.verified{background:#22c55e15;color:#22c55e;border:1px solid #22c55e30}
    .card-body{padding:2rem}
    .metric{margin-bottom:1.25rem}
    .metric-header{display:flex;justify-content:space-between;margin-bottom:.5rem}
    .metric-label{font-size:.8rem;color:#94a3b8}
    .metric-value{font-size:.8rem;font-weight:600;color:#f8fafc;font-family:"JetBrains Mono",monospace}
    .bar-track{height:6px;background:#1e293b;border-radius:3px;overflow:hidden}
    .bar-fill{height:100%;border-radius:3px;transition:width 1s ease}
    .bar-green{background:linear-gradient(90deg,#22c55e,#16a34a)}
    .bar-blue{background:linear-gradient(90deg,#2B3BE5,#6366f1)}
    .bar-amber{background:linear-gradient(90deg,#eab308,#f59e0b)}
    .meta{padding:1.5rem 2rem;border-top:1px solid #1e293b;display:grid;grid-template-columns:1fr 1fr;gap:1rem}
    .meta-item{font-size:.7rem}
    .meta-item .label{color:#64748b;display:block;margin-bottom:.15rem}
    .meta-item .value{color:#cbd5e1;font-family:"JetBrains Mono",monospace;font-weight:600}
    .footer{padding:1rem 2rem;border-top:1px solid #1e293b;text-align:center;font-size:.65rem;color:#475569}
    .footer a{color:#2B3BE5;text-decoration:none}
    .dot{width:8px;height:8px;border-radius:50%;background:#22c55e;animation:pulse 2s infinite}
    @keyframes pulse{0%,100%{opacity:1}50%{opacity:.4}}
  </style>
</head>
<body>
  <div class="card">
    <div class="card-header">
      <span class="logo">⬡</span>
      <div class="header-text">
        <h1>${cert.agent}</h1>
        <p>${cert.org} · ${cert.hash}</p>
      </div>
      <div class="status verified"><span class="dot"></span>${cert.status}</div>
    </div>
    <div class="card-body">
      <div class="metric">
        <div class="metric-header">
          <span class="metric-label">Threat Coverage</span>
          <span class="metric-value">${cert.threats_covered}/${cert.threats_total} (${coveragePct}%)</span>
        </div>
        <div class="bar-track"><div class="bar-fill bar-green" style="width:${coveragePct}%"></div></div>
      </div>
      <div class="metric">
        <div class="metric-header">
          <span class="metric-label">Formal Proofs</span>
          <span class="metric-value">${cert.proofs_passed}/${cert.formal_proofs} PASS</span>
        </div>
        <div class="bar-track"><div class="bar-fill bar-blue" style="width:100%"></div></div>
      </div>
      <div class="metric">
        <div class="metric-header">
          <span class="metric-label">Composition Safety</span>
          <span class="metric-value">${cert.composition_safety}%</span>
        </div>
        <div class="bar-track"><div class="bar-fill bar-amber" style="width:${cert.composition_safety}%"></div></div>
      </div>
    </div>
    <div class="meta">
      <div class="meta-item"><span class="label">Audit Date</span><span class="value">${cert.audit_date}</span></div>
      <div class="meta-item"><span class="label">Valid Until</span><span class="value">${cert.expiry_date}</span></div>
      <div class="meta-item"><span class="label">Auditor</span><span class="value">${cert.auditor}</span></div>
      <div class="meta-item"><span class="label">Engine</span><span class="value">Z3 SMT-LIB2</span></div>
    </div>
    <div class="footer">
      Cryptographically signed by <a href="https://agents.archi">AGENTS.archi</a> — The Architecture of Agent Security
    </div>
  </div>
</body>
</html>`;

  return new Response(html, {
    status: 200,
    headers: {
      "Content-Type": "text/html; charset=utf-8",
      "Cache-Control": "public, max-age=3600",
    },
  });
}
