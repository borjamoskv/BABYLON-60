# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] BFT consensus ledger — Fachada Causal.
# Redirige el flujo $\Omega = C \circ V \circ T \circ O$.
# Delega la Verificación (V) a BFT_Validator y el Commit (C) a BFT_Committer.
import sqlite3
import cbor2
from typing import Dict, Optional
from babylon60.bft.consensus_validator import BFT_Validator
from babylon60.bft.consensus_committer import BFT_Committer, StateMutation as StateMutation
from babylon60.bft.integrity import LedgerCheckpoint
from babylon60.core.crypto_utils import canonicalize_cbor, hash_sha3_256

__all__ = ["BFT_Ledger", "StateMutation"]


class BFT_Ledger:
    def __init__(self, db_path: str = "master_ledger.db", node_keys: Optional[Dict[str, str]] = None) -> None:
        self.validator = BFT_Validator(node_keys or {})
        self.committer = BFT_Committer(db_path)

    @property
    def conn(self) -> sqlite3.Connection:
        return self.committer.conn

    def invoke_subagent(self, mutation: StateMutation, f: int, swarm_signatures: Dict[str, str]) -> bool:
        # Snapshot mutable payload/vote containers before checking and persisting.
        frozen = StateMutation(
            mutation.agent_id,
            cbor2.loads(canonicalize_cbor(mutation.payload)),
            mutation.timestamp,
            mutation.signature,
            mutation.causal_taint,
        )
        votes = dict(swarm_signatures)
        mutation_hash = self.validator.validate_votes(frozen.signing_payload(f), f, votes)
        return self.committer.commit_mutation(frozen, mutation_hash, f, votes)

    def close(self) -> None:
        self.committer.close()

    def _verified_checkpoint(self) -> LedgerCheckpoint | None:
        rows = self.committer.get_audit_rows()
        if rows is None:
            print("[-] No state_log table found or database uninitialized.")
            return None
        head = "0" * 64
        for expected_id, row in enumerate(rows, 1):
            row_id, stored_hash, agent, payload_bytes, timestamp, taint, f, proof = row
            try:
                if row_id != expected_id or not isinstance(proof, bytes) or not isinstance(payload_bytes, bytes):
                    raise ValueError("Missing row or authenticated quorum evidence")
                payload = cbor2.loads(payload_bytes)
                votes = cbor2.loads(proof)
                if not isinstance(votes, dict):
                    raise ValueError("Invalid quorum evidence")
                if canonicalize_cbor(payload) != payload_bytes or canonicalize_cbor(votes) != proof:
                    raise ValueError("Noncanonical or trailing CBOR data")
                mutation = StateMutation(agent, payload, timestamp, "", taint)
                digest = self.validator.validate_votes(mutation.signing_payload(f), f, votes)
                if digest != stored_hash:
                    raise ValueError("Signed mutation hash mismatch")
                head = hash_sha3_256(canonicalize_cbor([head, row_id, digest]))
            except (ValueError, TypeError, PermissionError, cbor2.CBORDecodeError, cbor2.CBOREncodeError):
                print(f"[!] Corruption or unauthenticated history in row {row_id}!")
                return None
        high_water = self.conn.execute("SELECT seq FROM sqlite_sequence WHERE name='state_log'").fetchone()
        if (high_water[0] if high_water else 0) != len(rows):
            print("[!] Ledger truncation detected")
            return None
        return LedgerCheckpoint(len(rows), head)

    def audit_integrity(self, *, expected_checkpoint: LedgerCheckpoint | None = None) -> bool:
        """Verify persisted votes and structure; a caller-held pin also detects rollback."""
        self.committer.require_autocommit()
        with self.conn:  # A single read snapshot, including the sequence high-water mark.
            self.conn.execute("BEGIN")
            checkpoint = self._verified_checkpoint()
        return checkpoint is not None and (expected_checkpoint is None or checkpoint == expected_checkpoint)

    def get_checkpoint(self) -> LedgerCheckpoint:
        self.committer.require_autocommit()
        with self.conn:
            self.conn.execute("BEGIN")
            checkpoint = self._verified_checkpoint()
        if checkpoint is None:
            raise ValueError("Cannot checkpoint an unauthenticated ledger")
        return checkpoint


if __name__ == "__main__":
    import sys

    db_path = "master_ledger.db"
    audit_mode = "--audit-mode" in sys.argv
    print(f"[*] [Causal-Determinist] BFT Ledger Audit: db_path={db_path}, audit_mode={audit_mode}")
    ledger = BFT_Ledger(db_path)
    if audit_mode:
        if ledger.audit_integrity():
            print("[+] Audit complete. Verified successfully.")
        else:
            print("[!] Audit failed. Corrupted entries found!")
            sys.exit(1)
