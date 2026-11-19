#!/usr/bin/env bash
# ============================================================================
# BABYLON-60 Sovereign Hardened — C5-REAL Branch Governance Enforcement
# ============================================================================
set -euo pipefail

REPO="borjamoskv/BABYLON-60"
BRANCH="main"

echo "🔒 [C5-GOVERNANCE] Enforcing Sovereign Branch Protection on $REPO:$BRANCH..."

if ! command -v gh >/dev/null 2>&1; then
    echo "⚠️  GitHub CLI (gh) not found. Skipping remote branch protection API call."
    exit 0
fi

# Apply branch protection via GitHub API
gh api   --method PUT   -H "Accept: application/vnd.github+json"   "/repos/$REPO/branches/$BRANCH/protection"   --input - <<EOF || echo "ℹ️  Branch protection update requires admin token or pro tier."
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["CI Suite (Ubuntu, Mac, Windows)"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "required_linear_history": true,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF

echo "✓ [C5-GOVERNANCE] Branch protection configuration dispatched."
