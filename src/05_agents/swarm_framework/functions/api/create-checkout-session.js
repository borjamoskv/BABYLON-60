// C5-REAL EXERGY CERTIFIED
// ═══════════════════════════════════════════════════════════
// AGENTS.archi — Stripe Checkout Session (C5-REAL Native Fetch)
// Cloudflare Pages Function · Web Platform Runtime
// POST /api/create-checkout-session
// Body: { plan, email, customAmount }
// Returns: { url }
// ═══════════════════════════════════════════════════════════

const CORS_HEADERS = {
  "Access-Control-Allow-Origin": "https://agents.archi",
  "Access-Control-Allow-Methods": "POST, OPTIONS",
  "Access-Control-Allow-Headers": "Content-Type",
};

export async function onRequestOptions() {
  return new Response(null, { status: 204, headers: CORS_HEADERS });
}

export async function onRequestPost({ request, env }) {
  // ── Env guard ─────────────────────────────────────────────
  const secretKey = env.STRIPE_SECRET_KEY;
  if (!secretKey) {
    console.error("[stripe] STRIPE_SECRET_KEY not set");
    return jsonError(500, "Payment service not configured");
  }

  try {
    const body = await request.json().catch(() => ({}));
    const { plan, email, customAmount } = body;

    // ── Input validation ──────────────────────────────────────
    if (!plan) {
      return jsonError(400, "Invalid plan selected");
    }

    if (email && !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email)) {
      return jsonError(400, "Invalid email address");
    }

    // PWYW Pricing logic (minimum $1 if hitting Stripe)
    let amountInCents = 10000; // Default $100
    if (customAmount !== undefined && customAmount !== null) {
      const parsedAmount = parseInt(customAmount, 10);
      if (isNaN(parsedAmount) || parsedAmount < 1) {
        return jsonError(400, "Amount must be at least $1 for Stripe checkout");
      }
      amountInCents = parsedAmount * 100;
    }

    // ── Create Checkout Session via Native Fetch API ─────────
    const baseUrl = env.NEXT_PUBLIC_URL || "https://agents.archi";

    const params = new URLSearchParams();
    params.append('mode', 'payment');
    if (email) params.append('customer_email', email);
    params.append('success_url', `${baseUrl}/success.html?session_id={CHECKOUT_SESSION_ID}`);
    params.append('cancel_url', `${baseUrl}/#pricing`);
    params.append('allow_promotion_codes', 'true');
    params.append('billing_address_collection', 'auto');

    params.append('line_items[0][price_data][currency]', 'usd');
    params.append('line_items[0][price_data][product_data][name]', `AGENTS.ARCHI - ${plan.toUpperCase()} (MODO EXPERIMENTO)`);
    params.append('line_items[0][price_data][product_data][description]', 'Aportación a Laboratorio de Investigación Experimental AGENTS.archi (Sandbox Status)');
    params.append('line_items[0][price_data][unit_amount]', String(amountInCents));
    params.append('line_items[0][quantity]', '1');

    params.append('metadata[source]', 'AGENTS.archi');
    params.append('metadata[status]', 'experimental_research_mode');
    params.append('metadata[notice]', 'Payment gateway active for experimental contributions; production commercial service provision not yet active.');
    params.append('metadata[cortex_taint]', `taint:checkout:${performance.now()}`);

    const res = await fetch('https://api.stripe.com/v1/checkout/sessions', {
      method: 'POST',
      headers: {
        'Authorization': `Bearer ${secretKey}`,
        'Content-Type': 'application/x-www-form-urlencoded',
      },
      body: params.toString(),
    });

    const sessionData = await res.json();

    if (!res.ok) {
      console.error("[stripe] Checkout session error:", sessionData.error?.message || JSON.stringify(sessionData));
      return jsonError(res.status, sessionData.error?.message || "Failed to create checkout session");
    }

    return jsonOk({ url: sessionData.url });

  } catch (err) {
    console.error("[stripe] Checkout session error:", err.message);
    return jsonError(500, "Failed to create checkout session");
  }
}

// ── Helpers ───────────────────────────────────────────────
function jsonOk(data) {
  return new Response(JSON.stringify(data), {
    status: 200,
    headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
  });
}

function jsonError(status, message) {
  return new Response(JSON.stringify({ error: message }), {
    status,
    headers: { ...CORS_HEADERS, "Content-Type": "application/json" },
  });
}
