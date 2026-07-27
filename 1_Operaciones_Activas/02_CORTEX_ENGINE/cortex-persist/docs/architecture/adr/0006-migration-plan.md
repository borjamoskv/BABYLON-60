# ADR-0006: Namespace Migration Plan

## Context

Decoupling the `cortex` namespace and migrating to `babylon60` must be executed without breaking production API surfaces.

## Migration Waves

We establish a 5-wave migration plan:

### Wave 1: Compatibility Layer (Active)
* Create `babylon60/compat` module structure.
* Map critical imports dynamically to allow external libraries referencing `cortex` to import from `babylon60` transparently.
* Establish root-level symbolic links for the legacy `cortex` package layout.

### Wave 2: Internal Refactoring
* Migrate all internal package imports from `cortex.*` to `babylon60.*`.
* Update tests to verify package integrity under the new import path.

### Wave 3: MCP Server Migration
* Update MCP configuration and tool registrations to point directly to `babylon60` modules.
* Update schema output descriptors.

### Wave 4: Ledger & Persistence Paths
* Align database tables, environment variable fallbacks, and local storage folders to use `babylon60` instead of `cortex` paths where applicable.

### Wave 5: Deprecation & Deletion
* Log deprecation warnings for any usage of the legacy `cortex` entrypoint.
* Eventually remove symbolic links and old compatibility wrappers in a future major version release.

## Status

Approved. Starting Wave 1 execution.
