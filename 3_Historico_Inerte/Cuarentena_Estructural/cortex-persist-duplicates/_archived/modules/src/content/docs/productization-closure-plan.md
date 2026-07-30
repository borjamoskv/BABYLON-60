---
title: "Productization Closure Plan"
description: "Execution plan to close the public product contract for BABYLON60 Persist."
---

# Productization Closure Plan

> **Status:** Active execution spec
> **Last updated:** 2026-04-13
> **Scope:** Public package, docs, onboarding, and supported-core definition

This document turns the current productization feedback into a concrete closing sequence. The repository already contains real engineering depth. The problem to solve now is narrower: the **public contract** still exposes more surface than the product can confidently support.

## Current diagnosis

The strongest part of BABYLON60 is already clear:

- It has a differentiated thesis: verifiable memory and decision records for agents.
- It does not position itself as "another vector DB" or "another logging tool."
- It already has real trust primitives: hash chaining, Merkle checkpoints, audit exports, and explicit verification language.

The weakest part is also clear:

- The supported core is not officially delimited.
- Public naming is inconsistent across package, import, docs, and SDK surfaces.
- Distribution and onboarding are not yet closed end-to-end.
- The public docs still expose more platform surface than the first product contract should carry.

## Product principle

For this phase, BABYLON60 should be presented as a **trust layer with one canonical flow**, not as the full breadth of the repository.

The official public path should be:

```text
install -> init -> store -> verify -> export
```

`search` should **not** be part of the first canonical onboarding. It adds conceptual and dependency weight before the user has seen the core value proposition.

## Supported core proposal

The supported core for the current product line should be:

- Public Python package with a single install story.
- Stable public CLI for local-first usage.
- Local SQLite/WAL deployment as the default supported environment.
- Core commands:
  - `babylon60 init`
  - `babylon60 memory store`
  - `babylon60 verify`
  - `babylon60 trust-ledger verify`
  - `babylon60 compliance-report` or the final canonical export command
- One tangible audit artifact that proves value in a clean environment.

Everything else should be explicitly labeled before being pitched publicly:

- `beta`
- `experimental`
- `internal`
- `not yet published`

That applies especially to SDK variants, broad swarm surfaces, cloud/distributed claims, and any public docs section that depends on unpublished distribution or unstable naming.

## Execution order

The correct closing order is:

1. **Define supported core**
   Issue: [#208](https://github.com/borjamoskv/Babylon60-Persist/issues/208)
2. **Unify public naming**
   Issue: [#205](https://github.com/borjamoskv/Babylon60-Persist/issues/205)
3. **Close public distribution**
   Issue: [#204](https://github.com/borjamoskv/Babylon60-Persist/issues/204)
4. **Repair public links and entry surfaces**
   Issue: [#207](https://github.com/borjamoskv/Babylon60-Persist/issues/207)
5. **Publish one canonical 5-minute onboarding**
   Issue: [#206](https://github.com/borjamoskv/Babylon60-Persist/issues/206)
6. **Publish one canonical demo**
   Issue: [#209](https://github.com/borjamoskv/Babylon60-Persist/issues/209)

This order is intentional. Onboarding and demo should not be finalized before the package name, supported core, and real distribution story are fixed.

## Workstream details

### 1. Supported core

Deliverables:

- One explicit table: `Core / Beta / Experimental`
- One official list of supported commands and capabilities
- README reordered to lead with the supported core
- Documentation separated between product contract and broader repository surfaces

Exit criteria:

- A new user can identify what is safe to adopt without reading the whole repo
- The main README no longer reads like a lab surface first

### 2. Naming

Deliverables:

- One final public naming decision for package, import, CLI, and SDK naming
- Removal of contradictory examples across README, docs, and examples
- Public snippets aligned with real importable surfaces

Exit criteria:

- The answer to "what do I install?" is unambiguous
- The answer to "what do I import?" is unambiguous

### 3. Distribution

Deliverables:

- Public release artifacts that match the documented install path
- Verified clean install path for the supported Python package
- Explicit decision on whether the JS SDK is published now or removed from the public pitch

Exit criteria:

- Public installation claims are true in a clean environment
- The docs do not advertise unpublished surfaces

### 4. Public surface repair

Deliverables:

- Main README links validated
- Canonical docs routes validated
- Broken or placeholder public routes removed or replaced
- Automated validation for critical public links

Exit criteria:

- A serious evaluator does not hit `404` in the primary reading path

### 5. Canonical onboarding

Deliverables:

- One short quickstart in README and docs
- One validated command sequence using final naming
- One clean-environment validation path in CI or preflight

Canonical flow:

```bash
pip install <final-package-name>
babylon60 init
babylon60 memory store demo "Decision recorded" --type decision
babylon60 verify <FACT_ID>
babylon60 trust-ledger verify
babylon60 compliance-report
```

Exit criteria:

- A user reaches visible proof of value in under 5 minutes

### 6. Canonical demo

Deliverables:

- One short demo story
- One reproducible script or walkthrough
- One shared artifact reused across README, docs, pilots, and diligence

Exit criteria:

- Sales, evaluation, and technical review all point to the same demo

## Definition of done

The public contract is considered closed only when all of the following are true:

- README, docs, package metadata, and examples tell the same story
- Installation works the way the public docs say it works
- The first-time user path reaches a real audit artifact quickly
- The supported core is visibly smaller than the full repository
- Experimental and unpublished surfaces are clearly marked
- The product can be explained in one sentence and demonstrated in one flow

## Non-goals for this phase

The following are valuable, but they should not block closure of the first public contract:

- Broad re-architecture of internal subsystems
- Full cleanup of every experimental module in the repository
- Expanding the canonical onboarding to search, recall, MCP, API, or consensus flows
- Cloud positioning beyond what is already truly installable and supportable

## Short version

The repository already contains enough engineering to support a serious product story. The immediate work is not to add more breadth. It is to **cut the public surface down to a supported nucleus and make every public claim true end-to-end**.
