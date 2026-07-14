#!/bin/bash
# install-into-repo.sh
# KINETIC PREFLIGHT PROTOCOL ENFORCER (C5-REAL)

if [ -z "$1" ]; then
  echo "Usage: ./install-into-repo.sh <path_to_repo>"
  exit 1
fi

TARGET_REPO="$1"
if [ ! -d "$TARGET_REPO" ]; then
  echo "Error: Directory $TARGET_REPO does not exist."
  exit 1
fi

echo "█▄ INJECTING C5-REAL RELEASE KIT INTO $TARGET_REPO"

SRC_DIR="$(pwd)"
mkdir -p "$TARGET_REPO/scripts"
mkdir -p "$TARGET_REPO/.github/workflows"

cp "$SRC_DIR/scripts/preflight.sh" "$TARGET_REPO/scripts/" 2>/dev/null || true
cp "$SRC_DIR/scripts/verify-counters.mjs" "$TARGET_REPO/scripts/" 2>/dev/null || true
cp "$SRC_DIR/.github/workflows/preflight.yml" "$TARGET_REPO/.github/workflows/" 2>/dev/null || true
cp "$SRC_DIR/RELEASE.md" "$TARGET_REPO/" 2>/dev/null || true

chmod +x "$TARGET_REPO/scripts/preflight.sh" 2>/dev/null || true

echo "█▄ FORCING GIT SENTINEL IN $TARGET_REPO"
cd "$TARGET_REPO"
git add scripts/preflight.sh scripts/verify-counters.mjs .github/workflows/preflight.yml RELEASE.md
git commit -m "chore(release-kit): inject autonomous C5-REAL preflight and verification protocol"

echo "⚡ [ATP SAVED: +940] - READY FOR PUSH & CACHE PURGE"
