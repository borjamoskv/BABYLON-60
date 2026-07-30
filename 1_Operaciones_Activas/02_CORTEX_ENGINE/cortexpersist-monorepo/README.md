# CortexPersist Monorepo

Turborepo monorepo powering the full CortexPersist ecosystem.

## Apps

| App | Domain | Port | Description |
|---|---|---|---|
| `@cortex/com` | cortexpersist.com | 3000 | Main landing, SDK docs, pricing |
| `@cortex/dev` | cortexpersist.dev | 3001 | Developer portal, API keys, demos |
| `@cortex/org` | cortexpersist.org | 3002 | Community, open-source, changelog |
| `@cortex/agents-archi` | agents.archi | 3003 | Sovereign Audit Ledger |

## Packages

| Package | Description |
|---|---|
| `@cortex/sdk` | Core SDK — CortexClient, AuditEmitter, HashChain, MerkleAnchor, Ed25519Signer |
| `@cortex/ui` | Shared React components — CortexBadge, OuroborosBadge, HashChainViewer, AuditEventCard |
| `@cortex/tsconfig` | Shared TypeScript configurations |

## Getting Started

```bash
# Install dependencies
pnpm install

# Run all apps in development
pnpm dev

# Run a specific app
pnpm turbo run dev --filter=@cortex/com

# Build all
pnpm build

# Lint + type-check
pnpm lint
```

## Environment Variables

Copy `.env.example` to `.env.local` in each app directory and fill in the values.

```bash
cp .env.example apps/cortexpersist-com/.env.local
cp .env.example apps/agents-archi/.env.local
```

## GitHub Secrets Required

For CI/CD to work, add these secrets to the repository:

```
VERCEL_TOKEN
VERCEL_ORG_ID
VERCEL_PROJECT_COM
VERCEL_PROJECT_DEV
VERCEL_PROJECT_ORG
VERCEL_PROJECT_ARCHI
TURBO_TOKEN
TURBO_TEAM
```

## Architecture

```
cortexpersist-monorepo/
├── apps/
│   ├── cortexpersist-com/     # cortexpersist.com
│   ├── cortexpersist-dev/     # cortexpersist.dev
│   ├── cortexpersist-org/     # cortexpersist.org
│   └── agents-archi/          # agents.archi
├── packages/
│   ├── sdk/                   # @cortex/sdk
│   ├── ui/                    # @cortex/ui
│   └── tsconfig/              # @cortex/tsconfig
├── .github/workflows/
│   ├── deploy.yml             # Main deploy pipeline
│   └── pr-preview.yml         # PR preview deployments
├── turbo.json
├── package.json
└── pnpm-workspace.yaml
```

## Cross-Domain Integration

`agents.archi` emits every audit finding as a cryptographically signed event to the CortexPersist API, anchoring it via Merkle tree. This means the audit portfolio **self-demonstrates** the product it documents.

```typescript
import { auditEmitter } from '@/lib/audit-emitter';

await auditEmitter.finding({
  id: 'OUROBOROS-FD-VM-01',
  severity: 'critical',
  protocol: 'Firedancer VM',
  auditor: 'borja-moskv',
  title: 'Unbounded loop in JIT compiler path',
  exploitable: true,
});
```

---

**Borja Moskv · Moskv Systems · Bilbao, Spain**


---

```yaml
AESTHETIC:    INDUSTRIAL NOIR 2026 (#0A0A0A / #2B3BE5)
EPISTEMOLOGY: C5-REAL EDG V6 — Error Navigation System
CORE TENET:   Optimize for correction, not certainty. Uncertainty is telemetry, not weakness.
UPDATED:      June 2026 — Falsifiable Memory Infrastructure
```
