"""Caller-retained ledger checkpoints; never infer external trust from SQLite.

Keep checkpoints outside the database and its rollback domain. SQLite's own
sequence catches ordinary deletions, but cannot authenticate a complete restore.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LedgerCheckpoint:
    entries: int
    head_hash: str
