import os
import sys
import hashlib
import sqlite3
import datetime
from typing import TypedDict


class PlaywrightPrimitiveDict(TypedDict):
    id: str
    domain: str
    verb: str
    category: str
    name: str
    description: str
    taint_hash: str
    timestamp: str


PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

DOMAINS = [
    "DOM_MUTATION",
    "EVENT_INTERCEPTION",
    "CONTEXT_ISOLATION",
]

CATEGORIES = [
    "Inyección_JS_Causal",
    "Purga_de_Nodos_Fantasmas",
    "Validación_BFT_Visual",
    "Extracción_de_Exergía_DOM",
    "Bypass_Shadow_DOM",
    "Extracción_de_Trazas_CDP",
    "Profiling_Memoria_V8",
    "Bloqueo_Event_Loop",
    "Aniquilación_Caché",
    "Transducción_Proxy",
]

ACTION_VERBS = [
    "Transducir",
    "Aislar",
    "Forzar",
    "Inyectar",
    "Destruir",
    "Sincronizar",
    "Evaluar",
    "Purgar",
    "Evadir",
    "Cristalizar",
]

# 3 Domains * 10 Categories * 10 Verbs = 300 base archetypes.


def generate_playwright_primitives() -> list[PlaywrightPrimitiveDict]:
    primitives: list[PlaywrightPrimitiveDict] = []
    p_idx = 1

    for domain in DOMAINS:
        for cat in CATEGORIES:
            for verb in ACTION_VERBS:
                name = f"PLW-{p_idx:04d} | {domain}::{verb}_{cat}"
                desc = f"Al operar en {domain}, {verb.lower()} vectores de {cat.replace('_', ' ').lower()} vía Playwright Core."
                timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

                # CORTEX-TAINT Hash
                raw_data = f"{name}{desc}{timestamp}".encode("utf-8")
                taint_hash = hashlib.sha3_256(raw_data).hexdigest()

                primitives.append(
                    {
                        "id": f"PLW-{p_idx:04d}",
                        "domain": domain,
                        "verb": verb,
                        "category": cat,
                        "name": name,
                        "description": desc,
                        "taint_hash": taint_hash,
                        "timestamp": timestamp,
                    }
                )
                p_idx += 1

    return primitives


def save_to_markdown(primitives: list[PlaywrightPrimitiveDict], filepath: str) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write("# █▄ PLAYWRIGHT MATRIX: 300 INTERNAL C5-REAL PRIMITIVES\n\n")
        f.write(
            "Invariante: Mapeo ortogonal de 3 dominios de browser automation contra 100 operaciones APEX.\n\n"
        )

        current_domain = ""
        for p in primitives:
            if p["domain"] != current_domain:
                current_domain = p["domain"]
                f.write(f"\n## DOMINIO: {current_domain}\n\n")

            f.write(f"### {p['name']}\n")
            f.write(f"- **Regla**: {p['description']}\n")
            f.write(f"- **CORTEX-TAINT**: `{p['taint_hash']}`\n\n")


def save_to_sqlite(primitives: list[PlaywrightPrimitiveDict], db_path: str) -> None:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)

    # Configure BFT MTK SQLite requirements (WAL mode, busy timeout)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")

    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS playwright_primitives (
            id TEXT PRIMARY KEY,
            domain TEXT NOT NULL,
            verb TEXT,
            category TEXT,
            name TEXT,
            description TEXT,
            taint_hash TEXT UNIQUE,
            timestamp TEXT
        )
    """)

    cursor.execute("DELETE FROM playwright_primitives")

    for p in primitives:
        cursor.execute(
            """
            INSERT INTO playwright_primitives (id, domain, verb, category, name, description, taint_hash, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """,
            (
                p["id"],
                p["domain"],
                p["verb"],
                p["category"],
                p["name"],
                p["description"],
                p["taint_hash"],
                p["timestamp"],
            ),
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    primitives = generate_playwright_primitives()

    md_path = os.path.join(os.getcwd(), "docs", "PLAYWRIGHT_INTERNAL_PRIMITIVES.md")
    db_path = os.path.join(os.getcwd(), "db", "playwright_primitives.db")

    save_to_markdown(primitives, md_path)
    save_to_sqlite(primitives, db_path)

    print(f"✅ Generadas {len(primitives)} primitivas C5-REAL Playwright.")
    print(f"📄 Markdown: {md_path}")
    print(f"💽 Database: {db_path}")
