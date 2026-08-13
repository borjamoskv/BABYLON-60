// C5-REAL EXERGY CERTIFIED
// ═══════════════════════════════════════════════════════════
// AGENTS.archi — Badge API
// Cloudflare Pages Function · Web Platform Runtime
// GET /api/badge?hash={certHash}&style={flat|shield}&theme={dark|light}&coverage={87}
// ═══════════════════════════════════════════════════════════

export async function onRequestGet({ request }) {
  const url = new URL(request.url);
  const hash = url.searchParams.get("hash") || "demo";
  const style = url.searchParams.get("style") || "shield";
  const theme = url.searchParams.get("theme") || "dark";
  const coverage = url.searchParams.get("coverage") || "87";

  const coverageNum = Math.min(100, Math.max(0, parseInt(coverage, 10) || 0));

  // Color based on coverage
  let statusColor, statusText;
  if (coverageNum >= 80) {
    statusColor = "#22c55e";
    statusText = "VERIFIED";
  } else if (coverageNum >= 50) {
    statusColor = "#eab308";
    statusText = "PARTIAL";
  } else {
    statusColor = "#ef4444";
    statusText = "AT RISK";
  }

  const bgColor = theme === "light" ? "#f8fafc" : "#0A0A0A";
  const textColor = theme === "light" ? "#0f172a" : "#e2e8f0";
  const borderColor = theme === "light" ? "#cbd5e1" : "#1e293b";
  const accentColor = "#2B3BE5";

  const svg = `<svg xmlns="http://www.w3.org/2000/svg" width="280" height="42" viewBox="0 0 280 42">
  <defs>
    <linearGradient id="bg" x1="0" y1="0" x2="1" y2="0">
      <stop offset="0%" stop-color="${bgColor}"/>
      <stop offset="100%" stop-color="${bgColor}"/>
    </linearGradient>
  </defs>
  <rect width="280" height="42" rx="6" fill="url(#bg)" stroke="${borderColor}" stroke-width="1"/>

  <!-- Logo section -->
  <rect x="0" y="0" width="130" height="42" rx="6" fill="${bgColor}"/>
  <text x="10" y="26" font-family="Inter, -apple-system, sans-serif" font-size="11" font-weight="600" fill="${accentColor}">⬡</text>
  <text x="24" y="26" font-family="Inter, -apple-system, sans-serif" font-size="11" font-weight="600" fill="${textColor}">AGENTS.archi</text>

  <!-- Status section -->
  <rect x="130" y="0" width="150" height="42" rx="6" fill="${statusColor}15"/>
  <rect x="130" y="0" width="1" height="42" fill="${borderColor}"/>

  <circle cx="145" cy="21" r="4" fill="${statusColor}"/>
  <text x="155" y="18" font-family="JetBrains Mono, monospace" font-size="10" font-weight="700" fill="${statusColor}">${statusText}</text>
  <text x="155" y="30" font-family="JetBrains Mono, monospace" font-size="9" font-weight="400" fill="${textColor}80">Coverage: ${coverageNum}%</text>

  <!-- Hash -->
  <text x="250" y="26" font-family="JetBrains Mono, monospace" font-size="7" fill="${textColor}40" text-anchor="end">${hash.slice(0, 8)}</text>
</svg>`;

  return new Response(svg, {
    status: 200,
    headers: {
      "Content-Type": "image/svg+xml",
      "Cache-Control": "public, max-age=3600, s-maxage=3600",
      "Access-Control-Allow-Origin": "*",
    },
  });
}
