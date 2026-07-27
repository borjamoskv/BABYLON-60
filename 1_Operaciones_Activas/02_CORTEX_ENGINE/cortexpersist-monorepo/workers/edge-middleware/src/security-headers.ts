/**
 * Injects security headers on every response.
 * CSP is per-domain to allow domain-specific origins.
 */
export function injectSecurityHeaders(headers: Headers, url: URL): void {
  const { hostname } = url;

  // HSTS — 1 year, includeSubDomains
  headers.set('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload');

  // Anti-clickjacking
  headers.set('X-Frame-Options', 'DENY');
  headers.set('X-Content-Type-Options', 'nosniff');
  headers.set('Referrer-Policy', 'strict-origin-when-cross-origin');
  headers.set('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');

  // Remove fingerprinting headers
  headers.delete('X-Powered-By');
  headers.delete('Server');

  // Per-domain CSP
  headers.set('Content-Security-Policy', buildCSP(hostname));
}

function buildCSP(hostname: string): string {
  // Shared allowed origins for cross-domain SDK/badge assets
  const cortexOrigins = [
    'https://cortexpersist.com',
    'https://cortexpersist.dev',
    'https://agents.archi',
    'https://api.cortexpersist.com',
  ].join(' ');

  const base = [
    `default-src 'self'`,
    `script-src 'self' 'unsafe-inline' 'unsafe-eval' ${cortexOrigins}`,  // unsafe-eval needed for WebGL shaders
    `style-src 'self' 'unsafe-inline'`,
    `img-src 'self' data: blob: ${cortexOrigins}`,
    `font-src 'self' data:`,
    `connect-src 'self' ${cortexOrigins} wss://${hostname}`,
    `worker-src 'self' blob:`,
    `frame-ancestors 'none'`,
    `base-uri 'self'`,
    `form-action 'self'`,
  ];

  // agents.archi can embed CORTEX badge iframes from .com
  if (hostname === 'agents.archi') {
    base[base.findIndex(d => d.startsWith('frame-ancestors'))] =
      `frame-ancestors 'none'`;
  }

  return base.join('; ');
}
