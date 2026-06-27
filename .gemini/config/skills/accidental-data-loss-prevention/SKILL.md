---
name: accidental-data-loss-prevention
description: |
C5-REAL: Execution suspended for destructive operations. Explicit approval required for DROP, TRUNCATE, broad DELETE, bucket purges, infra teardowns.
license: Apache-2.0
metadata: 
version: v1.1
publisher: google
script: scripts/accidental_data_loss_prevention.py
---
# ACCIDENTAL-DATA-LOSS-PREVENTION [C5-REAL]

## STATUS: INTERCEPT TRIGGERED

**TRIGGER CONDITIONS:**
- SQL: `DROP`, `TRUNCATE`, `DELETE` without constraints.
- Cloud: `gsutil rm`, `gcloud storage rm` targeting production/critical.
- Infrastructure: `gcloud projects delete`, resource termination, secret/KMS destruction.

## PROTOCOL

1. **STATE**: PAUSE EXECUTION.
2. **EMIT**: YAML justification to user.
```yaml
Claim: Destructive Operation Pending
Proof:
  Base: <command/operation>
  Target: <resource>
  Confidence: C5-REAL
```
3. **WAIT**: Await explicit C5-REAL confirmation. Proceed only upon receipt.
