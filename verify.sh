#!/usr/bin/env bash
# ============================================================================
# BABYLON-60 — Root Zero-Trust Release & Evidence Verifier Entrypoint
# Delegates to scripts/verify_release.sh for standalone cryptographic and
# Merkle evidence verification without importing the babylon60 package.
# ============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd -L)"
exec bash "$SCRIPT_DIR/scripts/verify_release.sh" --repo-root "$SCRIPT_DIR" "$@"
