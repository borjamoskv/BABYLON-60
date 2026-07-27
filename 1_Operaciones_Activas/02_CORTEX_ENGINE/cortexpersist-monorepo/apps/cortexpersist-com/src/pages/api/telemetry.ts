import type { APIRoute } from 'astro';

export const POST: APIRoute = async ({ request }) => {
  if (request.headers.get('Authorization') !== `Bearer ${import.meta.env.CORTEX_API_KEY || 'dummy-build-key'}`) {
    return new Response('Unauthorized', { status: 401 });
  }
  try {
    const res = await fetch(`${import.meta.env.CORTEX_API_URL || 'http://127.0.0.1:8100'}/telemetry`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: request.body,
      // @ts-ignore
      duplex: 'half',
    });
    return new Response(res.body, { status: res.status, headers: { 'Content-Type': 'application/json' } });
  } catch (e: any) {
    return new Response(JSON.stringify({ error: e.message }), { status: 500 });
  }
};
