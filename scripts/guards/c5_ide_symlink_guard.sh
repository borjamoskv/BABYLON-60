#!/usr/bin/env bash
# Delegate to the same validator used by local checks and CI.
set -euo pipefail
script_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)"
exec python3 "$script_dir/verify_active_topology.py" "$@"
