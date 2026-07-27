# C5-REAL EXERGY CERTIFIED
# [C5-REAL] BFT consensus ledger — Fachada Causal.
# Redirige el flujo $\Omega = C \circ V \circ T \circ O$.
# Delega la Verificación (V) a BFT_Validator y el Commit (C) a BFT_Committer.
from typing import Dict, Optional
from babylon60.bft.consensus_validator import BFT_Validator
from babylon60.bft.consensus_committer import BFT_Committer, StateMutation

class BFT_Ledger:
    def __init__(self, db_path: str = "master_ledger.db", node_keys: Optional[Dict[str, str]] = None) -> None:
        self.validator = BFT_Validator(node_keys or {})
        self.committer = BFT_Committer(db_path)

    @property
    def conn(self):
        return self.committer.conn

    def invoke_subagent(self, mutation: StateMutation, f: int, swarm_signatures: Dict[str, str]) -> bool:
        # V: Validar Atacantes Bizantinos
        mutation_hash = self.validator.validate_votes(mutation.payload, f, swarm_signatures)
        # C: Commit Atómico (WAL)
        return self.committer.commit_mutation(mutation, mutation_hash)

    def audit_integrity(self) -> bool:
        rows = self.committer.get_audit_rows()
        if rows is None:
            print("[-] No state_log table found or database uninitialized.")
            return False

        corrupted = 0
        for row_id, stored_hash, payload_bytes in rows:
            payload_data = self.validator.decode_payload(payload_bytes)
            if not self.validator.audit_payload(payload_data, stored_hash):
                print(f"[!] Corruption detected in row {row_id}!")
                corrupted += 1

        return corrupted == 0

if __name__ == "__main__":
    import sys
    db_path = "master_ledger.db"
    audit_mode = "--audit-mode" in sys.argv
    print(f"[*] [C5-REAL] BFT Ledger Audit: db_path={db_path}, audit_mode={audit_mode}")
    ledger = BFT_Ledger(db_path)
    if audit_mode:
        if ledger.audit_integrity():
            print("[+] Audit complete. Verified successfully.")
        else:
            print("[!] Audit failed. Corrupted entries found!")
            sys.exit(1)
