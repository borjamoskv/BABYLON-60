#!/usr/bin/env python3
"""Reject certification until extracted preconditions and Rust are linked.

The former emitter compiled an unrelated example state machine and promoted
rows to PROVED. A successful compiler exit does not establish that missing
correspondence. This module withdraws that eligibility; it does not claim to
implement the absent proof-producing translation or retire deployed artifacts.
"""

from __future__ import annotations

import hashlib
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path
from typing import Any

REPO_ROOT = Path(__file__).absolute().parents[2]
DEFAULT_DB_PATH = REPO_ROOT / "data/cortex_memory.db"
LEAN_PROOF_DIR = REPO_ROOT / "proof/lean"
UNVERIFIED_REASON = "IMPLEMENTATION_CORRESPONDENCE_UNVERIFIED"


class Lean4ProofEmitter:
    def __init__(self, db_path: Path = DEFAULT_DB_PATH, lean_dir: Path = LEAN_PROOF_DIR):
        self.db_path = Path(db_path)
        self.lean_dir = Path(lean_dir)

    def prove_extracted_clusters(self) -> dict[str, Any]:
        """Mark candidates as unverified; never authorize Rust code generation.

        Existing PROVED eligibility in this pipeline is withdrawn as well.
        No Lean source is emitted or executed: there is no supported translator
        or correspondence checker for the precondition/implementation pair.
        """
        uri = self.db_path.absolute().as_uri() + "?mode=rw"
        with closing(sqlite3.connect(uri, uri=True)) as conn:
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA synchronous=FULL")
            with conn:
                conn.execute("BEGIN IMMEDIATE")
                clusters = conn.execute(
                    """
                    SELECT cluster_id, ast_signature, z3_precondition
                    FROM cortex_invariant_clusters
                    WHERE status = 'EXTRACTED' OR lean4_proof_status = 'PROVED'
                    ORDER BY cluster_id
                    """
                ).fetchall()
                results = []
                for cluster in clusters:
                    cid = cluster["cluster_id"]
                    conn.execute(
                        """
                        UPDATE cortex_invariant_clusters
                        SET lean4_proof_status = 'NOT_VERIFIED',
                            lean4_proof_path = NULL,
                            status = 'EXTRACTED'
                        WHERE cluster_id = ?
                        """,
                        (cid,),
                    )
                    precondition = cluster["z3_precondition"]
                    digest = (hashlib.sha256(precondition.encode("utf-8")).hexdigest()
                              if isinstance(precondition, str) else None)
                    results.append({
                        "cluster_id": cid,
                        "status": "NOT_VERIFIED",
                        "model_check_status": "NOT_EXECUTED",
                        "implementation_correspondence": "NOT_VERIFIED",
                        "precondition_sha256": digest,
                        "reason": UNVERIFIED_REASON,
                        "path": None,
                    })
        return {"total_evaluated": len(results), "results": results,
                "certified": 0, "checker_status": "NOT_IMPLEMENTED"}


if __name__ == "__main__":
    report = Lean4ProofEmitter().prove_extracted_clusters()
    print(json.dumps(report, indent=2))
    sys.exit(2 if report["total_evaluated"] else 0)
