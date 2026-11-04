#!/usr/bin/env bash
set -euo pipefail

echo "Applying branch protection to 'main'..."

gh api \
  --method PUT \
  -H "Accept: application/vnd.github.v3+json" \
  repos/{owner}/{repo}/branches/main/protection \
  --input - <<EOF
{
  "required_status_checks": null,
  "enforce_admins": true,
  "required_pull_request_reviews": {
    "required_approving_review_count": 1
  },
  "restrictions": null,
  "allow_force_pushes": false,
  "allow_deletions": false
}
EOF

echo "Protection rules configured successfully."
