import asyncio
import aiosqlite
from pathlib import Path
from typing import List, Dict, Any

DB_PATH: str = str(Path(__file__).resolve().parent / "osint_primitives.db")


class OSINTOntologyAccessor:
    def __init__(self, db_path: str = DB_PATH) -> None:
        self.db_path = db_path

    async def get_primitives_by_domain(self, domain_name: str) -> List[Dict[str, Any]]:
        query: str = "\n            SELECT p.id, p.name, p.description \n            FROM primitive p\n            JOIN domain d ON p.domain_id = d.id\n            WHERE d.name LIKE ?\n            LIMIT 120\n        "
        async with aiosqlite.connect(self.db_path) as db:
            db.text_factory = str
            await db.execute("PRAGMA busy_timeout=5000")
            await db.execute("PRAGMA journal_mode=WAL")
            async with db.execute(query, (f"%{domain_name}%",)) as cursor:
                rows = await cursor.fetchall()
                if not rows:
                    raise RuntimeError(
                        f"Dominio OSINT no encontrado o vacío: {domain_name}"
                    )
                return [{"id": r[0], "name": r[1], "description": r[2]} for r in rows]

    async def get_all_invariants(self) -> List[Dict[str, str]]:
        query: str = "SELECT code, description FROM invariant"
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("PRAGMA busy_timeout=5000")
            async with db.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [{"code": r[0], "description": r[1]} for r in rows]


if __name__ == "__main__":

    async def run_audit() -> None:
        accessor = OSINTOntologyAccessor()
        invariants = await accessor.get_all_invariants()
        print(f"Loaded {len(invariants)} invariants.")
        primitives = await accessor.get_primitives_by_domain("SOCINT")
        print(
            f"Loaded {len(primitives)} SOCINT primitives. First: {primitives[0]['name']}"
        )

    asyncio.run(run_audit())
