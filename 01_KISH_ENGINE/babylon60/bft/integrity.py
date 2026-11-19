"""Caller-retained ledger checkpoints; never infer external trust from SQLite.

Keep checkpoints outside the database and its rollback domain. ``sqlite_sequence``
catches an ordinary tail deletion on an AUTOINCREMENT table. It does not
authenticate a file that was replaced by another valid chain: pass
``LedgerCheckpoint`` (entry count and head hash) to ``verify_integrity()`` or
``verify_chain()``. Without that pin, a full rewrite is undetectable.
"""

from dataclasses import dataclass


@dataclass(frozen=True)
class LedgerCheckpoint:
    entries: int
    head_hash: str
