import type { CortexEnv } from './types';

const RATE_LIMIT_WINDOW_S = 60;
const RATE_LIMITS: Record<string, number> = {
  'cortexpersist.com': 300,   // 300 req/min public landing
  'cortexpersist.dev': 120,   // 120 req/min dev portal
  'cortexpersist.org': 200,   // 200 req/min community
  'agents.archi': 60,         // 60 req/min audit ledger (tighter, forensic data)
};

/**
 * Token-bucket rate limiting via Cloudflare KV.
 * Returns a 429 response if the limit is exceeded, null otherwise.
 */
export async function handleRateLimit(
  request: Request,
  env: CortexEnv
): Promise<Response | null> {
  // Skip rate limiting for health checks and static assets
  const url = new URL(request.url);
  if (
    url.pathname === '/health' ||
    url.pathname.startsWith('/_next/static/') ||
    url.pathname.startsWith('/assets/')
  ) {
    return null;
  }

  const ip = request.headers.get('CF-Connecting-IP') ?? 'unknown';
  const hostname = url.hostname;
  const limit = RATE_LIMITS[hostname] ?? 100;
  const windowKey = Math.floor(Date.now() / 1000 / RATE_LIMIT_WINDOW_S);
  const key = `rl:${hostname}:${ip}:${windowKey}`;

  try {
    const current = await env.CORTEX_KV.get(key);
    const count = current ? parseInt(current, 10) : 0;

    if (count >= limit) {
      return new Response(
        JSON.stringify({
          error: 'rate_limit_exceeded',
          domain: hostname,
          limit,
          window: `${RATE_LIMIT_WINDOW_S}s`,
          retryAfter: RATE_LIMIT_WINDOW_S,
        }),
        {
          status: 429,
          headers: {
            'Content-Type': 'application/json',
            'Retry-After': String(RATE_LIMIT_WINDOW_S),
            'X-RateLimit-Limit': String(limit),
            'X-RateLimit-Remaining': '0',
            'X-RateLimit-Reset': String((windowKey + 1) * RATE_LIMIT_WINDOW_S),
            'X-Cortex-Route': hostname,
          },
        }
      );
    }

    // Increment counter (fire-and-forget, non-blocking)
    env.CORTEX_KV.put(key, String(count + 1), {
      expirationTtl: RATE_LIMIT_WINDOW_S * 2,
    });
  } catch {
    // KV failure = fail open (never block legitimate traffic)
    return null;
  }

  return null;
}
