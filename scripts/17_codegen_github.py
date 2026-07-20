import os
import sys
import hashlib
import sqlite3
import datetime

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.append(PROJECT_ROOT)
os.chdir(PROJECT_ROOT)

DOMAINS = [
    "PUSH",
    "PULL_REQUEST",
    "ISSUE",
    "WORKFLOW_RUN",
    "RELEASE",
    "DEPLOYMENT",
    "CODE_SCANNING_ALERT",
    "DISCUSSION",
    "REPOSITORY",
    "PACKAGE",
]

CATEGORIES = [
    "Mutación Autónoma",
    "Destrucción Anergía",
    "Mitosis Celular",
    "Bucle Adversarial",
    "Bloqueo Termodinámico",
    "Bypass Causal",
    "Rechazo Soberano",
    "Contención Epistémica",
    "Causalidad Base-60",
    "Ruteo Multidimensional",
]

ACTION_VERBS = [
    "Transducir",
    "Aniquilar",
    "Cristalizar",
    "Falsar",
    "Confrontar",
    "Auditar",
    "Interceptar",
    "Purgar",
    "Sintetizar",
    "Aislar",
]

# We need exactly 100 primitives per domain to hit 1000.
# We will generate 10 categories * 10 verbs = 100 base archetypes.


def generate_centuria() -> list[dict[str, str]]:
    base_archetypes = []
    idx = 1
    for cat in CATEGORIES:
        for verb in ACTION_VERBS:
            base_archetypes.append(
                {
                    "id": f"ARCH-{idx:03d}",
                    "category": cat,
                    "verb": verb,
                    "description": f"{verb} entropía en contexto de {cat}",
                }
            )
            idx += 1

    primitives = []
    p_idx = 1
    for domain in DOMAINS:
        for arch in base_archetypes:
            name = f"CMX-{p_idx:04d} | {domain}::{arch['verb']}_{arch['category'].replace(' ', '_')}"
            desc = f"Al recibir webhook de {domain}, {arch['verb'].lower()} elementos de {arch['category'].lower()}."
            timestamp = datetime.datetime.now(datetime.timezone.utc).isoformat()

            # CORTEX-TAINT Hash
            raw_data = f"{name}{desc}{timestamp}".encode("utf-8")
            taint_hash = hashlib.sha3_256(raw_data).hexdigest()

            primitives.append(
                {
                    "id": f"CMX-{p_idx:04d}",
                    "domain": domain,
                    "archetype_id": arch["id"],
                    "name": name,
                    "description": desc,
                    "taint_hash": taint_hash,
                    "timestamp": timestamp,
                }
            )
            p_idx += 1

    return primitives


def save_to_markdown(primitives: list[dict[str, str]], filepath: str) -> None:
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, "w") as f:
        f.write(
            "# █▄ CENTURIA MATRIX: 1000 GITHUB WEBHOOK/MCP PRIMITIVES (C5-REAL)\n\n"
        )
        f.write(
            "Invariante: Mapeo ortogonal de 10 dominios de eventos GitHub contra 100 arquetipos APEX.\n\n"
        )

        current_domain = ""
        for p in primitives:
            if p["domain"] != current_domain:
                current_domain = p["domain"]
                f.write(f"\n## DOMINIO: {current_domain}\n\n")

            f.write(f"### {p['name']}\n")
            f.write(f"- **Regla**: {p['description']}\n")
            f.write(f"- **CORTEX-TAINT**: `{p['taint_hash']}`\n\n")


def save_to_sqlite(primitives: list[dict[str, str]], db_path: str) -> None:
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path)

    # Configure BFT MTK SQLite requirements (WAL mode, busy timeout)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")

    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS github_primitives (
            id TEXT PRIMARY KEY,
            domain TEXT NOT NULL,
            archetype_id TEXT,
            name TEXT,
            description TEXT,
            taint_hash TEXT UNIQUE,
            timestamp TEXT
        )
    """)

    cursor.execute("DELETE FROM github_primitives")

    for p in primitives:
        cursor.execute(
            """
            INSERT INTO github_primitives (id, domain, archetype_id, name, description, taint_hash, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
            (
                p["id"],
                p["domain"],
                p["archetype_id"],
                p["name"],
                p["description"],
                p["taint_hash"],
                p["timestamp"],
            ),
        )

    conn.commit()
    conn.close()


if __name__ == "__main__":
    primitives = generate_centuria()

    md_path = os.path.join(os.getcwd(), "docs", "CENTURIA_GITHUB_WEBHOOKS.md")
    db_path = os.path.join(os.getcwd(), "db", "centuria_github.db")

    save_to_markdown(primitives, md_path)
    save_to_sqlite(primitives, db_path)

    print(f"✅ Generadas {len(primitives)} primitivas C5-REAL.")
    print(f"📄 Markdown: {md_path}")
    print(f"💽 Database: {db_path}")
