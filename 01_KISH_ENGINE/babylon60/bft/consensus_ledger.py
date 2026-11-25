# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# [Causal-Determinist] BFT consensus ledger — Fachada Causal.
# Redirige el flujo $\Omega = C \circ V \circ T \circ O$.
# Delega la Verificación (V) a BFT_Validator y el Commit (C) a BFT_Committer.
import argparse
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
import cbor2
from typing import Dict, Optional
from babylon60.bft.consensus_validator import BFT_Validator
from babylon60.bft.consensus_committer import BFT_Committer, StateMutation as StateMutation, read_audit_rows
from babylon60.database.core import resolve_db_path
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
        return self.committer.commit_mutation(frozen, mutation_hash, f, votes, validator=self.validator)

    def close(self) -> None:
        self.committer.close()

    def audit_integrity(self, *, expected_checkpoint: LedgerCheckpoint | None = None) -> bool:
        """Verify persisted votes and structure; a caller-held pin also detects rollback."""
        self.committer.require_autocommit()
        with self.conn:  # A single read snapshot, including the sequence high-water mark.
            self.conn.execute("BEGIN")
            checkpoint = _verified_checkpoint(self.conn, self.validator)
        return checkpoint is not None and (expected_checkpoint is None or checkpoint == expected_checkpoint)

    def get_checkpoint(self) -> LedgerCheckpoint:
        self.committer.require_autocommit()
        with self.conn:
            self.conn.execute("BEGIN")
            checkpoint = _verified_checkpoint(self.conn, self.validator)
        if checkpoint is None:
            raise ValueError("Cannot checkpoint an unauthenticated ledger")
        return checkpoint


def _verified_checkpoint(conn: sqlite3.Connection, validator: BFT_Validator) -> LedgerCheckpoint | None:
    rows = read_audit_rows(conn)
    if rows is None:
        print("[-] No state_log table found or database uninitialized.")
        return None
    head = "0" * 64
    for expected_id, row in enumerate(rows, 1):
        row_id, stored_hash, agent, payload_bytes, timestamp, taint, f, proof = row
        try:
            if (
                row_id != expected_id
                or f is None
                or not isinstance(proof, bytes)
                or not isinstance(payload_bytes, bytes)
            ):
                raise ValueError("Missing row or authenticated quorum evidence")
            payload = cbor2.loads(payload_bytes)
            if canonicalize_cbor(payload) != payload_bytes:
                raise ValueError("Noncanonical or trailing CBOR data")
            mutation = StateMutation(agent, payload, timestamp, "", taint)
            if not validator.stored_votes_match(mutation.signing_payload(f), f, proof, stored_hash):
                raise ValueError("Signed mutation hash mismatch")
            head = hash_sha3_256(canonicalize_cbor([head, row_id, stored_hash]))
        except (ValueError, TypeError, PermissionError, cbor2.CBORDecodeError, cbor2.CBOREncodeError):
            print(f"[!] Corruption or unauthenticated history in row {row_id}!")
            return None
    high_water = conn.execute("SELECT seq FROM sqlite_sequence WHERE name='state_log'").fetchone()
    if (high_water[0] if high_water else 0) != len(rows):
        print("[!] Ledger truncation detected")
        return None
    return LedgerCheckpoint(len(rows), head)


def _unique_node_keys(pairs: list[tuple[str, str]]) -> dict[str, str]:
    keys = dict(pairs)
    if len(keys) != len(pairs):
        raise ValueError("Duplicate node identifier")
    return keys


def main() -> int:
    parser = argparse.ArgumentParser(description="Audit signatures and structure of a BFT ledger.")
    parser.add_argument("--audit-mode", action="store_true", help="Verify an existing ledger in read-only mode.")
    parser.add_argument("--db", type=Path, help="SQLite file to verify (default: configured master_ledger.db).")
    parser.add_argument(
        "--node-keys", type=Path, help="Trusted JSON object mapping node IDs to Ed25519 public keys in hex."
    )
    args = parser.parse_args()
    if not args.audit_mode:
        if args.db is not None or args.node_keys is not None:
            parser.error("--db and --node-keys require --audit-mode")
        ledger = BFT_Ledger()
        ledger.close()
        return 0
    if args.node_keys is None:
        parser.error("--audit-mode requires --node-keys")
    try:
        keys = json.loads(args.node_keys.read_text(encoding="utf-8"), object_pairs_hook=_unique_node_keys)
        if not isinstance(keys, dict) or not keys or not all(isinstance(v, str) for v in keys.values()):
            raise ValueError("Expected a nonempty JSON object of public keys")
        validator = BFT_Validator(keys)
    except (OSError, ValueError) as exc:
        parser.error(f"Invalid --node-keys: {exc}")

    path = args.db or resolve_db_path("master_ledger.db", create_parent=False)
    try:
        with closing(sqlite3.connect(path.resolve().as_uri() + "?mode=ro", uri=True)) as conn:
            conn.execute("BEGIN")
            checkpoint = _verified_checkpoint(conn, validator)
    except sqlite3.Error as exc:
        print(f"[!] Audit failed: {exc}", file=sys.stderr)
        return 1
    if checkpoint is None:
        print("[!] Audit failed. Ledger integrity could not be verified.")
        return 1
    print("[+] Audit complete. Verified successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
