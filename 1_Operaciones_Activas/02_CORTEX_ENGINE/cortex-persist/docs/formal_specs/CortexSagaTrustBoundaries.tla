---------------- MODULE CortexSagaTrustBoundaries ----------------
\* Formal Verification of CORTEX-Persist Trust Boundaries & Saga Protocol
\* Level: C5-REAL
\* Author: Borja Moskv (borjamoskv)

EXTENDS Naturals, Sequences, TLC

CONSTANTS 
    Agents,       \* Set of external agents { "Agent_1", "Agent_2" }
    ValidHashes   \* Set of valid SHA3-256 signatures

VARIABLES 
    state,        \* Current saga state
    ledger,       \* Immutable append-only hash chain
    payload,      \* The entropy being processed
    taint_sig     \* Cryptographic provenance

vars == <<state, ledger, payload, taint_sig>>

Init ==
    /\ state = "IDLE"
    /\ ledger = <<>>
    /\ payload = "none"
    /\ taint_sig = "none"

Propose(p) ==
    /\ state = "IDLE"
    /\ payload' = p
    /\ state' = "PROPOSED"
    /\ UNCHANGED <<ledger, taint_sig>>

Validate ==
    \* Virgo Guard validation boundary
    /\ state = "PROPOSED"
    /\ state' = "VALIDATED"
    /\ UNCHANGED <<ledger, payload, taint_sig>>

TaintEngine ==
    \* Cryptographic attribution
    /\ state = "VALIDATED"
    /\ taint_sig' \in ValidHashes
    /\ state' = "TAINTED"
    /\ UNCHANGED <<ledger, payload>>

Commit ==
    \* Deterministic persistence to KETER-∞
    /\ state = "TAINTED"
    /\ taint_sig \neq "none"
    /\ ledger' = Append(ledger, <<payload, taint_sig>>)
    /\ state' = "IDLE"
    /\ payload' = "none"
    /\ taint_sig' = "none"

Rollback ==
    \* Saga compensatory sequence (Ouroboros loop)
    /\ state \in {"PROPOSED", "VALIDATED", "TAINTED"}
    /\ state' = "IDLE"
    /\ payload' = "none"
    /\ taint_sig' = "none"
    /\ UNCHANGED ledger

Next ==
    \/ \E p \in {"fact_1", "fact_2", "fact_3"}: Propose(p)
    \/ Validate
    \/ TaintEngine
    \/ Commit
    \/ Rollback

Spec == Init /\ [][Next]_vars

\* ====================================================================
\* INVARIANTS
\* ====================================================================

\* Ledger Continuity Axiom (AX-050)
\* Ensures that no fact ever enters the ledger without a valid signature.
LedgerIntegrity == 
    \A i \in 1..Len(ledger): ledger[i][2] \in ValidHashes

\* Saga Isolation
\* Ensuring the system only commits when properly tainted.
NoUntaintedCommits ==
    state = "COMMITTED" => taint_sig \neq "none"

=============================================================================
