# @cortex/edge-middleware

Cloudflare Worker deployed across all 4 CortexPersist domains.

## Architecture

```
Request
  │
  ├── canonical.ts       Redirect www, http://, .dev/.org canonical rules
  ├── rate-limit.ts      Token-bucket via Cloudflare KV (per IP/domain/window)
  ├── cors.ts            Preflight + cross-domain allow (4 Cortex origins only)
  ├── [proxy to Vercel]
  ├── security-headers.ts HSTS, X-Frame-Options, CSP per domain, anti-fingerprint
  └── telemetry.ts       X-Cortex-* headers + KV bucket write (waitUntil)
```

## Rate Limits

| Domain | Limit | Window |
|---|---|---|
| cortexpersist.com | 300 req | 60s |
| cortexpersist.dev | 120 req | 60s |
| cortexpersist.org | 200 req | 60s |
| agents.archi | 60 req | 60s |

## Deploy

```bash
# One-time setup
cd workers/edge-middleware
pnpm install

# Create KV namespace
npx wrangler kv namespace create CORTEX_KV
npx wrangler kv namespace create CORTEX_KV --preview

# Update wrangler.toml with the returned IDs, then:
npx wrangler deploy

# Staging
npx wrangler deploy --env staging
```

## Health Check

```bash
curl https://cortexpersist.com/health
curl https://agents.archi/health
```

Returns live hourly telemetry from KV:

```json
{
  "status": "ok",
  "domain": "cortexpersist.com",
  "env": "production",
  "version": "0.1.0",
  "timestamp": "2026-06-15T07:38:00.000Z",
  "telemetry": {
    "requestsThisHour": 142,
    "avgLatencyMs": 38,
    "errorsThisHour": 0
  }
}
```

## Telemetry Headers Injected

| Header | Value |
|---|---|
| `X-Cortex-Edge-Ts` | Unix timestamp (ms) |
| `X-Cortex-Route` | hostname |
| `X-Cortex-Latency-Ms` | upstream round-trip |
| `X-Cortex-Env` | production / staging |
| `X-Cortex-Version` | worker version |
| `X-Cortex-Path-Hash` | FNV-1a hash of pathname |

---

> ∴ Signal Sovereign ◈ Ω₂ Entropic Asymmetry
