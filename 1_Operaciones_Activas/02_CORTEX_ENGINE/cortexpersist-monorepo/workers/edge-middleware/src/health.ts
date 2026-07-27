import type { CortexEnv } from './types';

/**
 * Health check endpoint — returns live telemetry stats from KV.
 * GET /health on any of the 4 domains.
 */
export async function handleHealthCheck(
  env: CortexEnv,
  hostname: string
): Promise<Response> {
  const hour = new Date().toISOString().slice(0, 13);
  const key = `telemetry:${hostname}:${hour}`;

  let stats: { requests: number; totalLatency: number; errors: number } | null = null;
  try {
    const raw = await env.CORTEX_KV.get(key);
    if (raw) stats = JSON.parse(raw);
  } catch { /* ignore */ }

  const avgLatency = stats && stats.requests > 0
    ? Math.round(stats.totalLatency / stats.requests)
    : 0;

  return new Response(
    JSON.stringify({
      status: 'ok',
      domain: hostname,
      env: env.CORTEX_ENV,
      version: env.CORTEX_VERSION,
      timestamp: new Date().toISOString(),
      telemetry: {
        requestsThisHour: stats?.requests ?? 0,
        avgLatencyMs: avgLatency,
        errorsThisHour: stats?.errors ?? 0,
      },
    }, null, 2),
    {
      status: 200,
      headers: {
        'Content-Type': 'application/json',
        'Cache-Control': 'no-store',
        'X-Cortex-Route': hostname,
      },
    }
  );
}
