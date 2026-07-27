import type { CortexEnv } from './types';

/**
 * Injects real-time telemetry headers into every response.
 * These are readable by the CortexPersist dashboard and the
 * Swarm Telemetry Log component on cortexpersist.com.
 */
export function injectTelemetryHeaders(
  headers: Headers,
  url: URL,
  latencyMs: number,
  env: CortexEnv
): void {
  headers.set('X-Cortex-Edge-Ts', String(Date.now()));
  headers.set('X-Cortex-Route', url.hostname);
  headers.set('X-Cortex-Latency-Ms', String(latencyMs));
  headers.set('X-Cortex-Env', env.CORTEX_ENV);
  headers.set('X-Cortex-Version', env.CORTEX_VERSION);
  headers.set('X-Cortex-Path-Hash', simpleHash(url.pathname));

  // Expose selected headers to browser JS (for the telemetry dashboard)
  const existing = headers.get('Access-Control-Expose-Headers') ?? '';
  const toExpose = [
    'X-Cortex-Edge-Ts',
    'X-Cortex-Latency-Ms',
    'X-Cortex-Route',
    'X-Cortex-Version',
  ];
  headers.set(
    'Access-Control-Expose-Headers',
    [...new Set([...existing.split(',').map(s => s.trim()), ...toExpose])]
      .filter(Boolean)
      .join(', ')
  );
}

/** FNV-1a 32-bit — lightweight, no crypto overhead */
function simpleHash(input: string): string {
  let hash = 2166136261;
  for (let i = 0; i < input.length; i++) {
    hash ^= input.charCodeAt(i);
    hash = (hash * 16777619) >>> 0;
  }
  return hash.toString(16).padStart(8, '0');
}
