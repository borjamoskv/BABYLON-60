#!/usr/bin/env bash
# deploy_hotstuff.sh — Deployment script for HotStuff consensus engine.
# Uses environment variables per Ω14 (TOPOLOGÍA INSTANCE-AGNOSTIC).
set -euo pipefail

REPO_ROOT="${REPO_ROOT:-$(git rev-parse --show-toplevel)}"
BRANCH="${HOTSTUFF_BRANCH:-ultrathink/hotstuff}"
MANIFEST="${REPO_ROOT}/cortex/consensus/Cargo.toml"

cd "${REPO_ROOT}"

echo "=== HotStuff Deployment ==="
echo "Repo root: ${REPO_ROOT}"
echo "Branch:    ${BRANCH}"

# 1. Ensure hotstuff feature branch
git checkout -B "${BRANCH}"

# 2. Build Rust component with hotstuff feature flag
if [ -f "${MANIFEST}" ]; then
    cargo build --release --manifest-path "${MANIFEST}" --features use_hotstuff
    echo "Build: OK"
else
    echo "ERROR: Cargo.toml not found at ${MANIFEST}" >&2
    exit 1
fi

# 3. Run unit tests
cargo test --release --manifest-path "${MANIFEST}" --features use_hotstuff
echo "Tests: OK"

# 4. Distribute binary to agents (placeholder — fill with actual rsync/scp)
# AGENT_HOSTS="${AGENT_HOSTS:-}"
# if [ -n "${AGENT_HOSTS}" ]; then
#     for host in ${AGENT_HOSTS}; do
#         rsync -az "${REPO_ROOT}/target/release/cortex-consensus" "${host}:/opt/ultrathink/"
#     done
# fi

# 5. Restart service (placeholder)
# systemctl restart ultrathink.service

echo "=== HotStuff deployment completed ==="
