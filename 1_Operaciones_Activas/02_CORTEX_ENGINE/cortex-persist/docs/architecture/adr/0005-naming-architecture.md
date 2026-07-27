# ADR-0005: Naming Architecture & Namespace Decoupling

## Context

The branding and product names of our systems have become intertwined:
1. `cortex` has been used as the internal module namespace and product identifier.
2. `BABYLON-60` is the brand and codebase identity.
3. `MOSKV-1` is the sovereign execution kernel identity.

To improve engineering hygiene and separate execution logic from brand identity, we need to decouple these concerns.

## Decision

We will migrate the internal Python namespace from `cortex` to `babylon60`. 
To ensure backward compatibility for external integrations and legacy consumers:
1. The `cortex` folder at the root of the project will act as a symbolic link / routing compatibility wrapper to `babylon60`.
2. All imports inside the project should progressively move to `babylon60`.
3. We will introduce a compatibility layer in `babylon60/compat` to alias legacy exports.

## Status

Approved. Wave 1 (Compatibility Layer) execution in progress.
