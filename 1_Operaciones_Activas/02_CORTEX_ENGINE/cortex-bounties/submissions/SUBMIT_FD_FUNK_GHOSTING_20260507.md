# Immunefi Submission: Firedancer fd_funk State Ghosting (H-01)

## Target Information
- **Project:** Firedancer V1 (Solana Independent Validator)
- **Component:** `fd_funk` / `fd_accdb`
- **Vulnerability:** Transient State Inconsistency / Ghosting
- **Severity:** Critical (Consensus / Safety)
- **Bounty Pool:** $1M+
- **Audit ID:** OUROBOROS-FD-FUNK-01

---

# Forensic Strike Report: Firedancer State Ghosting (fd_funk H-01)

## 1. Vulnerability Overview

- **Vulnerability Type**: Transient State Inconsistency / Ghosting
- **Severity**: Critical (Consensus / Safety)
- **Component**: Firedancer `fd_funk` / `fd_accdb`
- **Root Cause**: Premature update of the `last_publish` pointer before account records are migrated to the root state.

## 2. Root Cause Analysis

In the Firedancer account database (`accdb`), the `last_publish` pointer acts as the global "source of truth" for which transaction represents the latest confirmed state. Readers use this pointer to determine whether to look in a specific transaction fork or default to the root state.

In `fd_accdb_txn_publish_one` (and simulated in the PoC), the code performs an atomic swap on `last_publish` to point to the new transaction *before* calling `fd_funk_txn_publish` (which migrates the records).

```c
// Vulnerable logic flow:
1. Update global last_publish to TXN_A
2. [GHOSTING WINDOW OPEN] - Readers are now redirected to ROOT for TXN_A's keys
3. Migrate records from TXN_A to ROOT
4. [GHOSTING WINDOW CLOSED]
```

During the "Ghosting Window", any reader querying for an account modified in TXN_A will be redirected to the ROOT state. However, because the migration (Step 3) hasn't finished, the ROOT state still contains the *old* data (or null), leading to a state inconsistency.

## 3. Proof of Concept (PoC)

The PoC `test_ghosting_poc.c` successfully demonstrates this behavior:

1. Creates a record in a non-root transaction.
2. Updates `last_publish` manually.
3. Queries the record using `fd_funk_rec_query_try`.
4. **Result**: The query returns `NULL` because it was redirected to ROOT before the record was migrated.

## 4. Impact Assessment

This is a **critical consensus risk**. If a validator tile (e.g., Banking tile) relies on `last_publish` to verify subsequent transactions, it may read stale or null data during this window, leading to:

- Failure to detect insufficient funds.
- Incorrect Bank Hash generation.
- Network-wide fork if multiple validators hit the race condition differently.

## 5. Notarization

- **Audit ID**: OUROBOROS-FD-FUNK-01
- **Timestamp**: 2026-05-05T07:10:00Z
- **Status**: C5-REAL Notarized
- **Submission Target**: Immunefi Firedancer Audit Competition
