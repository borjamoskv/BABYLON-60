/**
 * Canonical redirect rules — enforces:
 * - www -> non-www (all domains)
 * - cortexpersist.dev non-API paths -> cortexpersist.com/docs
 * - cortexpersist.org root -> cortexpersist.com
 * - HTTP -> HTTPS (Cloudflare usually handles this, but belt-and-suspenders)
 */
export function handleCanonicalRedirects(url: URL): Response | null {
  const { hostname, pathname, search } = url;

  // www -> non-www
  if (hostname.startsWith('www.')) {
    const canonical = `https://${hostname.slice(4)}${pathname}${search}`;
    return redirect301(canonical);
  }

  // HTTP -> HTTPS
  if (url.protocol === 'http:') {
    const canonical = `https://${hostname}${pathname}${search}`;
    return redirect301(canonical);
  }

  // cortexpersist.dev non-API/SDK paths -> /docs on .com
  if (hostname === 'cortexpersist.dev') {
    const isApiPath = pathname.startsWith('/api/') || pathname.startsWith('/sdk/');
    if (!isApiPath && pathname !== '/') {
      return redirect301(`https://cortexpersist.com/docs${pathname}${search}`);
    }
    if (pathname === '/') {
      // Dev root stays — developer portal home
      return null;
    }
  }

  // cortexpersist.org root -> cortexpersist.com
  if (hostname === 'cortexpersist.org' && pathname === '/') {
    return redirect301('https://cortexpersist.com');
  }

  return null;
}

function redirect301(location: string): Response {
  return new Response(null, {
    status: 301,
    headers: {
      Location: location,
      'Cache-Control': 'public, max-age=31536000',
      'X-Cortex-Redirect': 'canonical',
    },
  });
}
