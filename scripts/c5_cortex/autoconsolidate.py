#!/usr/bin/env python3
"""Legacy consolidation API, disabled until a durable journal contract exists."""

import asyncio
import sys

UNSUPPORTED = (
    "CONSOLIDATION_UNSUPPORTED: journal load/merge/save have no durable schema "
    "contract; originals are preserved and no database is opened"
)


class ConsolidationUnsupportedError(RuntimeError):
    """The legacy consolidation operation cannot safely persist a replacement."""


class JournalEntry:
    """Legacy data holder; persistence and merging deliberately reject."""

    def __init__(self, entry_id: str, payload: dict | None = None) -> None:
        self.id = entry_id
        self.payload = dict(payload) if payload is not None else {}

    @classmethod
    async def load(cls, entry_id: str) -> "JournalEntry":
        raise ConsolidationUnsupportedError(UNSUPPORTED)

    @classmethod
    def merge(cls, entries: list["JournalEntry"]) -> "JournalEntry":
        raise ConsolidationUnsupportedError(UNSUPPORTED)

    async def save(self) -> None:
        raise ConsolidationUnsupportedError(UNSUPPORTED)


async def autoconsolidate(batch_size: int = 500, db_path: str = "journal.db") -> None:
    """Refuse before resolving a path, connecting, creating or deleting data."""
    if type(batch_size) is not int or batch_size <= 0:
        raise ValueError("batch_size must be a positive integer")
    raise ConsolidationUnsupportedError(UNSUPPORTED)


if __name__ == "__main__":
    try:
        asyncio.run(autoconsolidate())
    except ConsolidationUnsupportedError as error:
        print(str(error), file=sys.stderr)
        raise SystemExit(2)
