const ALLOWED_ORIGINS = new Set([
  'https://cortexpersist.com',
  'https://cortexpersist.dev',
  'https://cortexpersist.org',
  'https://agents.archi',
]);

/**
 * Handles CORS preflight requests and injects CORS headers.
 * Only allows cross-origin requests between the 4 Cortex domains.
 */
export function handleCors(request: Request): Response | null {
  const origin = request.headers.get('Origin') ?? '';
  const isAllowed = ALLOWED_ORIGINS.has(origin);

  // Preflight
  if (request.method === 'OPTIONS') {
    return new Response(null, {
      status: 204,
      headers: buildCorsHeaders(origin, isAllowed),
    });
  }

  return null;
}

export function buildCorsHeaders(origin: string, isAllowed: boolean): Headers {
  const headers = new Headers();
  if (isAllowed) {
    headers.set('Access-Control-Allow-Origin', origin);
    headers.set('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
    headers.set('Access-Control-Allow-Headers', 'Content-Type, Authorization, X-Cortex-Chain-Index, X-Cortex-Block-Hash');
    headers.set('Access-Control-Max-Age', '86400');
    headers.set('Vary', 'Origin');
  }
  return headers;
}
