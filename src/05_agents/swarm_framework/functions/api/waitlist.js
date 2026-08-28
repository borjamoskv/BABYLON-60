// C5-REAL EXERGY CERTIFIED
// ═══════════════════════════════════════════════════════════
// AGENTS.archi — Waitlist API
// Cloudflare Pages Function · Web Platform Runtime
// POST /api/waitlist
// Body: { email }
// ═══════════════════════════════════════════════════════════

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "https://agents.archi",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export async function onRequestOptions() {
  return new Response(null, { status: 204, headers: CORS_HEADERS });
}

export async function onRequestPost({ request }) {
  try {
    const { email } = await request.json().catch(() => ({}));

    if (!email || typeof email !== "string") {
      return new Response(JSON.stringify({ error: "Invalid email" }), {
        status: 400,
        headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
      });
    }

    const trimmed = email.trim().toLowerCase();
    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
    if (!emailRegex.test(trimmed)) {
      return new Response(JSON.stringify({ error: "Invalid email format" }), {
        status: 400,
        headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
      });
    }

    // C5-REAL: log entry visible in Cloudflare Dashboard → Logs
    console.log(JSON.stringify({
      event: "waitlist_signup",
      email: trimmed,
      ts: new Date().toISOString(),
      source: request.headers.get("referer") || "direct",
    }));

    return new Response(JSON.stringify({ success: true }), {
      status: 200,
      headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  } catch (err) {
    console.error("waitlist error", err?.message);
    return new Response(JSON.stringify({ error: "Internal server error" }), {
      status: 500,
      headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
    });
  }
}
