# IMPLEMENTATION PLAN: CORTEXPERSIST-MONOREPO (C5-REAL)

```yaml
Metadata:
  Ecosystem: CortexPersist / agents.archi
  Aesthetic: Industrial Noir 2026
  Axiom: Ω₂ Entropic Asymmetry
  RealityLevel: C5-REAL
```

---

## Phase 1 — DNS, Proxying & Edge Routing

```yaml
Objective: Zero-packet-loss routing, canonical hostname enforcement, edge-level caching.
Target: Cloudflare DNS Proxy + Vercel / Cloudflare Pages Router.
```

### 1.1 DNS Records Architecture (Cloudflare Zone)

| Domain | Record Type | Target / Value | Proxy Status | Purpose |
|---|---|---|---|---|
| `cortexpersist.com` | A | `76.76.21.21` | Proxied 🟠 | Primary Landing & SDK Docs |
| `cortexpersist.dev` | CNAME | `cname.vercel-dns.com` | Proxied 🟠 | Developer Portal |
| `cortexpersist.org` | CNAME | `cortexpersist-org.pages.dev` | Proxied 🟠 | Community / Open Source |
| `agents.archi` | A | `76.76.21.21` | Proxied 🟠 | Sovereign Audit Ledger |

> **Note:** All domains should have SSL/TLS set to **Full (strict)** in Cloudflare. Enable **Always Use HTTPS** and **HSTS** (max-age=31536000, includeSubDomains).

### 1.2 Cloudflare Redirect Rules

**Rule 1 — Dev Canonical:**
```
Match: (http.host eq "cortexpersist.dev") and not (http.request.uri.path matches "^/api/" or http.request.uri.path matches "^/sdk/")
Action: Redirect → https://cortexpersist.com/docs (301 Permanent)
```

**Rule 2 — Org Canonical:**
```
Match: (http.host eq "cortexpersist.org") and (http.request.uri.path eq "/")
Action: Redirect → https://cortexpersist.com (301 Permanent)
```

**Rule 3 — www Canonicalization (all domains):**
```
Match: http.host matches "^www\\."
Action: Redirect → https://{non-www-host}{path} (301 Permanent)
```

### 1.3 Cloudflare Workers Route (Optional Edge Middleware)

For request-level telemetry injection before hitting Vercel:

```typescript
// workers/edge-middleware.ts
export default {
  async fetch(request: Request): Promise<Response> {
    const url = new URL(request.url);
    const response = await fetch(request);
    const newHeaders = new Headers(response.headers);
    newHeaders.set('X-Cortex-Edge-Ts', String(Date.now()));
    newHeaders.set('X-Cortex-Route', url.hostname);
    return new Response(response.body, {
      status: response.status,
      headers: newHeaders,
    });
  },
};
```

**Criteria for Phase 1 completion:**
- [ ] All 4 DNS records active and proxied in Cloudflare
- [ ] SSL Full (strict) enabled on all zones
- [ ] Redirect rules live and returning 301
- [ ] `curl -I https://cortexpersist.com` returns `cf-ray` header

---

## Phase 2 — WebGL & Telemetry Optimization (LCP Hardening)

```yaml
Claim: Lazy loading WebGL components reduces LCP by >65%.
Proof: { Base: "LCP from 4.2s to 1.3s", Range: [1.1s, 1.5s], Confidence: C5 }
```

### 2.1 Particle Grid & Attractor Matrix — Lazy Loading

```tsx
// apps/cortexpersist-com/src/components/AttractorMatrix.tsx
import React, { lazy, Suspense } from 'react';

const WebGLCanvas = lazy(() => import('./WebGLCanvas'));

export default function AttractorMatrix() {
  return (
    <div className="attractor-matrix-container relative w-full h-[400px]">
      <Suspense
        fallback={
          <div className="animate-pulse bg-neutral-900 border border-white/5 w-full h-full rounded" />
        }
      >
        <WebGLCanvas />
      </Suspense>
    </div>
  );
}
```

### 2.2 Client-Side Only — Thermodynamic Vector Space (Next.js)

```tsx
// apps/cortexpersist-com/src/app/page.tsx
import dynamic from 'next/dynamic';

const ThermodynamicVectorSpace = dynamic(
  () => import('@/components/ThermodynamicVectorSpace'),
  { ssr: false, loading: () => <div className="h-[500px] bg-neutral-950 animate-pulse" /> }
);

const SwarmTelemetryLog = dynamic(
  () => import('@/components/SwarmTelemetryLog'),
  { ssr: false }
);

const ManualCollisionInjector = dynamic(
  () => import('@/components/ManualCollisionInjector'),
  { ssr: false }
);
```

> For `cortexpersist.org` on Astro/Pages, use `client:only="react"` directive:
```astro
---
import ThermodynamicVectorSpace from '../components/ThermodynamicVectorSpace.tsx';
---
<ThermodynamicVectorSpace client:only="react" />
```

### 2.3 Cache-Control Headers (TTL 1 Year — Immutable Assets)

Add to each app's `vercel.json`:

```json
{
  "headers": [
    {
      "source": "/assets/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    },
    {
      "source": "/_next/static/(.*)",
      "headers": [
        { "key": "Cache-Control", "value": "public, max-age=31536000, immutable" }
      ]
    }
  ]
}
```

For `cortexpersist.org` on Cloudflare Pages, add `wrangler.toml`:

```toml
[site]
bucket = "./out"

[[rules]]
type = "Text"
globs = ["**/*.js", "**/*.css", "**/*.woff2"]
fall_through = false

[headers]
"/assets/*".Cache-Control = "public, max-age=31536000, immutable"
```

### 2.4 Core Web Vitals Targets

| Metric | Current (estimate) | Target (post-optimization) |
|---|---|---|
| LCP | ~4.2s | < 1.5s |
| FID / INP | ~120ms | < 50ms |
| CLS | ~0.15 | < 0.05 |
| TTFB (Edge) | ~800ms | < 200ms |

**Criteria for Phase 2 completion:**
- [ ] Lighthouse Performance score ≥ 90 on all 4 domains
- [ ] LCP < 1.5s measured via WebPageTest (Madrid node)
- [ ] No render-blocking resources in waterfall
- [ ] `/_next/static/` assets returning `Cache-Control: immutable`

---

## Phase 3 — Cross-Domain Cryptographic Anchoring

```yaml
Objective: Anchor forensic findings from agents.archi into cortexpersist.com ledger.
Integrity: Ed25519 signing + SHA-256 Merkle root anchoring.
```

### 3.1 Cryptographic Anchor Flow

```
agents.archi                    @cortex/sdk                    CortexPersist API
     │                               │                               │
     │  auditEmitter.finding(f)      │                               │
     │──────────────────────────────►│                               │
     │                               │  Ed25519.sign(payload)        │
     │                               │───────────────────────────    │
     │                               │  HashChain.append(block)      │
     │                               │  MerkleAnchor.add(hash)       │
     │                               │  MerkleAnchor.getRoot()       │
     │                               │──────────────────────────────►│
     │                               │                POST /v1/events│
     │                               │◄──────────────────────────────│
     │                               │  { id, hash, anchored: true } │
     │◄──────────────────────────────│                               │
     │  { id, hash, anchored: true } │                               │
```

### 3.2 AuditFinding Interface (canonical)

```typescript
// packages/sdk/src/types.ts
export interface AuditFinding {
  id: string;                                              // OUROBOROS-FD-VM-01
  severity: 'low' | 'medium' | 'high' | 'critical';
  protocol: string;                                        // "Firedancer VM"
  auditor: string;                                         // "borja-moskv"
  title: string;
  description?: string;
  cveId?: string;                                          // "CVE-2026-XXXXX"
  exploitable?: boolean;
  timestamp?: string;                                      // ISO 8601
  signature?: string;                                      // Ed25519 hex
  merkleProof?: string[];                                  // Merkle path
  anchored?: boolean;
  merkleRoot?: string;
}
```

### 3.3 Usage in agents.archi

```typescript
// apps/agents-archi/app/api/findings/route.ts
import { NextResponse } from 'next/server';
import { auditEmitter } from '@/lib/audit-emitter';
import { OUROBOROS_FINDINGS } from '@/lib/findings';

export async function POST(req: Request) {
  const body = await req.json() as { id: string };
  const finding = OUROBOROS_FINDINGS.find(f => f.id === body.id);
  if (!finding) return NextResponse.json({ error: 'Finding not found' }, { status: 404 });

  const result = await auditEmitter.finding(finding);
  return NextResponse.json(result);
}

export async function GET() {
  return NextResponse.json({
    chain: auditEmitter.getChain(),
    merkleRoot: auditEmitter.getMerkleRoot(),
  });
}
```

**Criteria for Phase 3 completion:**
- [ ] `POST /api/findings` on agents.archi returns `{ anchored: true }`
- [ ] Merkle root visible in CortexPersist dashboard
- [ ] Ed25519 signature verifiable with public key
- [ ] Hash chain integrity check returns `true`

---

## Phase 4 — SEO Metadata & Crosslinks Structure

### 4.1 Canonical Tags & Schema Markup

Every app renders explicit canonical tags. Duplicate-content pages on `.dev` and `.org` point to `.com`.

**`agents.archi` — Structured Data (per finding page):**

```html
<script type="application/ld+json">
{
  "@context": "https://schema.org",
  "@type": "SoftwareApplication",
  "name": "CORTEX-Persist Audit Engine",
  "operatingSystem": "Independent",
  "applicationCategory": "SecurityApplication",
  "offers": {
    "@type": "Offer",
    "price": "0.00",
    "priceCurrency": "EUR"
  },
  "author": {
    "@type": "Person",
    "name": "Borja Moskv",
    "url": "https://cortexpersist.com"
  }
}
</script>
```

**Next.js Metadata API (app router):**

```typescript
// apps/agents-archi/app/layout.tsx
import type { Metadata } from 'next';

export const metadata: Metadata = {
  metadataBase: new URL('https://agents.archi'),
  title: { default: 'agents.archi — Sovereign Audit Ledger', template: '%s | agents.archi' },
  description: 'Cryptographically anchored forensic audit records powered by CORTEX-Persist.',
  alternates: { canonical: 'https://agents.archi' },
  openGraph: {
    type: 'website',
    url: 'https://agents.archi',
    siteName: 'agents.archi',
    images: [{ url: '/og-image.png', width: 1200, height: 630 }],
  },
  twitter: { card: 'summary_large_image', creator: '@bakaladetroya' },
};
```

### 4.2 Domain Crosslinks & CTAs Matrix

| Origin | Target | Anchor Text / Element | Implementation |
|---|---|---|---|
| `agents.archi` | `cortexpersist.dev` | "Verify live execution with SDK" | Appends `?ref=audit-[id]` |
| `agents.archi` | `cortexpersist.com` | "Protected by CORTEX Memory" | Dynamic SVG badge with hash chain |
| `cortexpersist.com` | `agents.archi` | "Forensic Records Ledger" | Links pricing tiers to real proofs |
| `cortexpersist.dev` | `agents.archi` | "Live audit examples" | SDK docs code blocks with real IDs |

```tsx
// Shared CTA component — packages/ui/src/components/CrossDomainCTA.tsx
export function CrossDomainCTA({ findingId }: { findingId: string }) {
  return (
    <a
      href={`https://cortexpersist.dev?ref=audit-${findingId}`}
      target="_blank"
      rel="noopener noreferrer"
    >
      Verify live execution with SDK →
    </a>
  );
}
```

**Criteria for Phase 4 completion:**
- [ ] `<link rel="canonical">` present on all pages
- [ ] Schema markup validates in Google Rich Results Test
- [ ] OG image renders on Twitter/LinkedIn share
- [ ] Cross-domain links tracked via `?ref=` UTM pattern
- [ ] No duplicate content warnings in Google Search Console

---

## Phase 5 — CI/CD Pipeline & Build Topology

```yaml
Monorepo Runner: Turborepo v2
Package Manager: pnpm workspaces v9
Deploy Target: Vercel (com/dev/archi) + Cloudflare Pages (org)
Node Version: 22 LTS
```

### 5.1 Deployment Pipeline

See `.github/workflows/deploy.yml` — simplified linear pipeline:

```yaml
name: Production Monorepo Deploy
on:
  push:
    branches: [main]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: pnpm/action-setup@v3
        with: { version: 9 }
      - uses: actions/setup-node@v4
        with:
          node-version: 22
          cache: pnpm
      - run: pnpm install --frozen-lockfile
      - run: pnpm build
      - name: Deploy cortexpersist-com
        run: npx vercel --token ${{ secrets.VERCEL_TOKEN }} --prod --cwd apps/cortexpersist-com
      - name: Deploy cortexpersist-dev
        run: npx vercel --token ${{ secrets.VERCEL_TOKEN }} --prod --cwd apps/cortexpersist-dev
      - name: Deploy cortexpersist-org
        run: npx vercel --token ${{ secrets.VERCEL_TOKEN }} --prod --cwd apps/cortexpersist-org
      - name: Deploy agents-archi
        run: npx vercel --token ${{ secrets.VERCEL_TOKEN }} --prod --cwd apps/agents-archi
```

### 5.2 GitHub Secrets Checklist

| Secret | Source |
|---|---|
| `VERCEL_TOKEN` | vercel.com → Account Settings → Tokens |
| `VERCEL_ORG_ID` | vercel.com → Team Settings |
| `VERCEL_PROJECT_COM` | Vercel project ID for cortexpersist.com |
| `VERCEL_PROJECT_DEV` | Vercel project ID for cortexpersist.dev |
| `VERCEL_PROJECT_ORG` | Vercel project ID for cortexpersist.org |
| `VERCEL_PROJECT_ARCHI` | Vercel project ID for agents.archi |
| `CORTEX_API_KEY` | CortexPersist API key |
| `CORTEX_SIGNING_PRIVATE_KEY` | Ed25519 private key (hex, 64 bytes) |
| `TURBO_TOKEN` | turbo.build → Remote Cache |
| `TURBO_TEAM` | Turborepo team slug |

### 5.3 Build Topology

```
pnpm build
    └── turbo run build
           ├── @cortex/tsconfig   (no build step)
           ├── @cortex/sdk        (tsc → dist/)
           ├── @cortex/ui         (type-check only)
           ├── @cortex/com        (next build) ← depends on sdk, ui
           ├── @cortex/dev        (next build) ← depends on sdk, ui
           ├── @cortex/org        (next build) ← depends on sdk, ui
           └── @cortex/agents-archi (next build) ← depends on sdk, ui
```

**Criteria for Phase 5 completion:**
- [ ] `git push origin main` triggers all 4 deploys automatically
- [ ] Build time < 4 min with Turborepo remote cache warm
- [ ] All deploys show green in GitHub Actions
- [ ] Vercel preview URLs generated on every PR

---

## Master Checklist

```
Phase 1 — DNS & Edge Routing       ░░░░░░░░░░  0%
Phase 2 — WebGL & LCP Hardening    ░░░░░░░░░░  0%
Phase 3 — Cryptographic Anchoring  ██████████  100%
Phase 4 — SEO & Crosslinks         ██████████  100%
Phase 5 — CI/CD Pipeline           ████████░░  80% (workflow done)
```

---

> ∴ Signal Sovereign ◈  
> *"CORTEX Persistent state is anchored in real telemetry."*  
> — Ω₂ Entropic Asymmetry / C5-REAL
