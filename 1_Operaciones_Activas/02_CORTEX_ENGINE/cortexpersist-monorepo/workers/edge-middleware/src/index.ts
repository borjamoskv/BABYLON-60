import { handleCanonicalRedirects } from './canonical';
import { injectSecurityHeaders } from './security-headers';
import { injectTelemetryHeaders } from './telemetry';
import { handleRateLimit } from './rate-limit';
import { handleCors } from './cors';
import { handleHealthCheck } from './health';
import type { CortexEnv } from './types';

export default {
  async fetch(request: Request, env: CortexEnv, ctx: ExecutionContext): Promise<Response> {
    const url = new URL(request.url);

    // 0. Health check endpoint (CORTEX edge self-telemetry)
    if (url.pathname === '/health') {
      return await handleHealthCheck(env, url.hostname);
    }

    // 1. Canonical redirects (before anything else)
    const redirect = handleCanonicalRedirects(url);
    if (redirect) return redirect;

    // 2. Rate limiting (blocks before proxying)
    const rateLimitResult = await handleRateLimit(request, env);
    if (rateLimitResult) return rateLimitResult;

    // 3. CORS preflight
    const corsResult = handleCors(request);
    if (corsResult) return corsResult;

    // 4. Proxy to origin (Vercel)
    const startTs = Date.now();
    let response: Response;

    try {
      response = await fetch(request);
    } catch (err) {
      return new Response(
        JSON.stringify({ error: 'upstream_unavailable', domain: url.hostname }),
        {
          status: 503,
          headers: { 'Content-Type': 'application/json', 'Retry-After': '10' },
        }
      );
    }

    const latencyMs = Date.now() - startTs;

    // 5. Build mutable response with injected headers
    const mutableResponse = new Response(response.body, response);

    injectSecurityHeaders(mutableResponse.headers, url);
    injectTelemetryHeaders(mutableResponse.headers, url, latencyMs, env);

    // 6. Fire-and-forget telemetry to KV (non-blocking)
    ctx.waitUntil(recordTelemetry(env, url, latencyMs, response.status));

    return mutableResponse;
  },
};

async function recordTelemetry(
  env: CortexEnv,
  url: URL,
  latencyMs: number,
  status: number
): Promise<void> {
  try {
    const payload = {
      timestamp: Date.now(),
      hostname: url.hostname,
      pathname: url.pathname,
      latencyMs,
      status,
      method: 'GET',
    };

    // Forward telemetry to Next.js API route
    await fetch('https://cortexpersist.com/api/telemetry', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${env.CORTEX_API_KEY}`,
      },
      body: JSON.stringify(payload),
    });
  } catch {
    // telemetry is best-effort, never throw
  }
}
