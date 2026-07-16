# C5-REAL: Fact Extractor Masivo
import os
import sqlite3
import json
import glob
import sys


def init_db(db_path: str) -> sqlite3.Connection:
    assert isinstance(db_path, str), "db_path debe ser string"
    conn: sqlite3.Connection = sqlite3.connect(db_path, timeout=5.0)
    return conn


def extract_from_db(db_path: str) -> list[dict[str, str]]:
    assert os.path.exists(db_path), "El archivo DB debe existir"
    conn: sqlite3.Connection = init_db(db_path)
    cursor: sqlite3.Cursor = conn.cursor()
    facts: list[dict[str, str]] = []

    try:
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='facts';"
        )
        if cursor.fetchone():
            cursor.execute("SELECT * FROM facts;")
            columns: list[str] = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                fact: dict[str, str] = dict(zip(columns, [str(r) for r in row]))
                fact["_source_db"] = db_path
                fact["_source_table"] = "facts"
                facts.append(fact)

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='vec_facts';"
        )
        if cursor.fetchone():
            cursor.execute("SELECT * FROM vec_facts;")
            columns = [desc[0] for desc in cursor.description]
            for row in cursor.fetchall():
                fact = dict(zip(columns, [str(r) for r in row]))
                fact["_source_db"] = db_path
                fact["_source_table"] = "vec_facts"
                facts.append(fact)

    finally:
        conn.close()

    return facts


def main() -> None:
    sys.stdout.write("[*] Iniciando Extracción Masiva de Facts (C5-REAL)\n")
    db_paths: list[str] = []
    db_paths.extend(glob.glob(os.path.expanduser("~/.cortex/*.db")))
    db_paths.extend(glob.glob(os.path.expanduser("~/.cortex/*.sqlite")))
    db_paths.extend(glob.glob(os.path.expanduser("~/.babylon60/*.db")))

    all_facts: list[dict[str, str]] = []

    for db in db_paths:
        db_facts: list[dict[str, str]] = extract_from_db(db)
        if db_facts:
            sys.stdout.write(f"[+] {db}: {len(db_facts)} facts encontrados.\n")
            all_facts.extend(db_facts)

    sys.stdout.write(f"\n[*] Total Facts consolidados: {len(all_facts)}\n")

    out_dir: str = os.path.expanduser("~/.cortex/snapshots")
    os.makedirs(out_dir, exist_ok=True)
    out_file: str = os.path.join(out_dir, "facts_raw_export.jsonl")

    with open(out_file, "w", encoding="utf-8") as f:
        for fact in all_facts:
            f.write(json.dumps(fact, ensure_ascii=False) + "\n")

    sys.stdout.write(f"[+] Export completado en {out_file}\n")


if __name__ == "__main__":
    main()
