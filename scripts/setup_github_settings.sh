#!/usr/bin/env bash
set -euo pipefail

REPO="borjamoskv/BABYLON-60"
BRANCH="main"

echo "🟢 [MOSKV-1 APEX] Configuring GitHub Settings for ${REPO}..."

# 1. Update Repository General Settings
echo "⚙️ Updating general repository settings (Squash/Rebase, Delete branch on merge)..."
gh api -X PATCH "/repos/${REPO}" \
  -f has_issues=true \
  -f has_projects=true \
  -f has_wiki=false \
  -f allow_squash_merge=true \
  -f allow_merge_commit=false \
  -f allow_rebase_merge=true \
  -f delete_branch_on_merge=true \
  -f allow_auto_merge=true

# 2. Enable Vulnerability Alerts & Automated Security Fixes
echo "⚙️ Enabling Dependabot vulnerability alerts and automated fixes..."
gh api -X PUT "/repos/${REPO}/vulnerability-alerts" || true
gh api -X PUT "/repos/${REPO}/automated-security-fixes" || true

# 3. Configure Security & Analysis (Secret Scanning & Push Protection)
echo "⚙️ Enabling Secret Scanning & Push Protection..."
gh api -X PATCH "/repos/${REPO}" \
  --input - <<'EOF' || true
{
  "security_and_analysis": {
    "secret_scanning": { "status": "enabled" },
    "secret_scanning_push_protection": { "status": "enabled" }
  }
}
EOF

# 4. Set Branch Protection Rules for 'main'
echo "⚙️ Applying Branch Protection Rules for ${BRANCH}..."
gh api -X PUT "/repos/${REPO}/branches/${BRANCH}/protection" \
  --input - <<'EOF'
{
  "required_status_checks": {
    "strict": true,
    "contexts": [
      "CI Core Suite",
      "CodeQL"
    ]
  },
  "enforce_admins": false,
  "required_pull_request_reviews": {
    "dismiss_stale_reviews": true,
    "require_code_owner_reviews": true,
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false,
  "required_conversation_resolution": true
}
EOF

echo "🟢 [MOSKV-1 APEX] GitHub Repository Settings applied successfully."
