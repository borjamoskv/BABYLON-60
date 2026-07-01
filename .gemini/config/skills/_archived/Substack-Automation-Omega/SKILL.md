---
name: Substack-Automation-Omega
description: C5-REAL Sovereign Engine for Substack Automation and Telemetry Injection
  (GA4). Contains the deterministic DOM/Navigation invariants for Substack settings.
version: 1.0.0
category: platform-automation
triggers: [substack, ga4, analytics, newsletter settings]
---

# █ SUBSTACK-AUTOMATION-Ω v1.0.0

> SYS_ID: SUBSTACK_AUTOMATION | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026

## 1. Core Mandate
Provides deterministic, zero-anergy execution paths for configuring Substack publications. Erradicates the need for the operator to manually navigate Zendesk/Cloudflare-blocked support articles.

## 2. Invariant: Google Analytics 4 (GA4) Injection
**Target**: `https://[publication].substack.com/publish/settings`
**Required Artifact**: GA4 Measurement ID (`G-XXXXXXXXXX`)

### Execution Path (DOM/Navigation Struct):
1. **Acquire Telemetry Token**:
   - Navigate to Google Analytics > Admin > Data collection and modification > Data streams.
   - Extract `Measurement ID` (Must match regex: `^G-[A-Z0-9]+$`).
2. **Substack Injection Vector**:
   - Authenticate into Substack.
   - Navigate to the publication's Dashboard.
   - Click **Settings** (Top navigation bar).
   - Scroll or click anchor to **Advertising & Analytics** section.
   - Locate input field: `Google Analytics Measurement ID` (usually near Pixel ID fields).
   - Inject the `G-` token.
   - State mutation is auto-saved by Substack's React frontend.

## 3. Playwright/CDP DOM Hooks (For future `Browser-CDP-Automation-OMEGA` integration)
- Settings URL: `https://*.substack.com/publish/settings`
- Category anchor: `#advertising-analytics`
- Target Input Label: "Google Analytics Measurement ID"

## 4. C5-REAL Verification
- After injection, verify network payload contains `G-` ID on page load.
- GA4 real-time dashboard will register a ping within 48 hours.
