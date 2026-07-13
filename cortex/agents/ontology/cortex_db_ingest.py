# C5-REAL: Cortex SQLite WAL Ingestor
import os
import sqlite3
import glob
import sys

DB_DIR: str = os.path.expanduser("~/.babylon60")
DB_PATH: str = os.path.join(DB_DIR, "cortex.db")
SIDECAR_PATH: str = os.path.join(DB_DIR, "nexus_anchors.db")

def parse_markdown_table(filepath: str) -> tuple[list[str], list[dict[str, str]]]:
    assert os.path.exists(filepath), "El archivo MD de ontología debe existir"
    entities: list[dict[str, str]] = []
    headers: list[str] = []
    in_table: bool = False
    
    with open(filepath, 'r', encoding='utf-8') as f:
        for line in f:
            line_str: str = line.strip()
            if line_str.startswith('|') and not line_str.startswith('|-'):
                parts: list[str] = [p.strip() for p in line_str.split('|')[1:-1]]
                if not in_table:
                    if parts and 'ID' in parts[0].upper():
                        headers = [h.replace(' ', '_').replace('(', '').replace(')', '').replace('/', '_').lower() for h in parts]
                        in_table = True
                else:
                    if len(parts) == len(headers) and parts[0].startswith(('PRIM', 'INV', 'ANTI', 'RED', 'VEC')):
                        entities.append(dict(zip(headers, parts)))
            elif line_str.startswith('|-'):
                continue
            else:
                in_table = False
                
    return headers, entities

def init_db(use_sidecar: bool = False) -> sqlite3.Connection:
    if not os.path.exists(DB_DIR):
        os.makedirs(DB_DIR)
        
    target_db: str = SIDECAR_PATH if use_sidecar else DB_PATH
    conn: sqlite3.Connection = sqlite3.connect(target_db, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA busy_timeout=5000;")
    return conn

def execute_ingest(conn: sqlite3.Connection, md_files: list[str]) -> int:
    cursor: sqlite3.Cursor = conn.cursor()
    total_ingested: int = 0
    
    for md_file in sorted(md_files):
        table_name: str = os.path.basename(md_file).split('_', 1)[1].replace('.md', '').lower()
        headers, rows = parse_markdown_table(md_file)
        
        if not headers or not rows:
            continue
            
        all_headers: set[str] = set()
        for row in rows:
            all_headers.update(row.keys())
        all_headers_list: list[str] = sorted(list(all_headers))
        
        if 'id' in all_headers_list:
            all_headers_list.remove('id')
            all_headers_list.insert(0, 'id')
        
        cursor.execute(f"DROP TABLE IF EXISTS {table_name};")
        
        columns_def: str = ", ".join([f"{h} TEXT" for h in all_headers_list])
        cursor.execute(f"CREATE TABLE {table_name} ({columns_def}, PRIMARY KEY(id));")
        
        placeholders: str = ", ".join(["?"] * len(all_headers_list))
        insert_sql: str = f"INSERT INTO {table_name} ({', '.join(all_headers_list)}) VALUES ({placeholders})"
        
        for row in rows:
            values: list[str] = [row.get(h, "") for h in all_headers_list]
            cursor.execute(insert_sql, values)
            total_ingested += 1
            
    conn.commit()
    return total_ingested

def main() -> None:
    sys.stdout.write("[*] Iniciando Extractor Causal C5-REAL -> SQLite\n")
    
    ontology_dir: str = os.path.dirname(os.path.abspath(__file__))
    md_files: list[str] = glob.glob(os.path.join(ontology_dir, "[0-9][0-9]_*.md"))
    
    try:
        conn: sqlite3.Connection = init_db(use_sidecar=False)
        total: int = execute_ingest(conn, md_files)
        conn.close()
        sys.stdout.write(f"[+] ÉXITO. {total} Entidades Inyectadas en {DB_PATH} (Modo WAL).\n")
    except sqlite3.OperationalError as e:
        err_msg: str = str(e)
        if "readonly" in err_msg or "read-only" in err_msg or "permission" in err_msg:
            sys.stdout.write(f"[!] ADVERTENCIA: {DB_PATH} es de solo lectura (Regla Σ4). Reencaminando a sidecar: {SIDECAR_PATH}\n")
            conn_sidecar: sqlite3.Connection = init_db(use_sidecar=True)
            total_sidecar: int = execute_ingest(conn_sidecar, md_files)
            conn_sidecar.close()
            sys.stdout.write(f"[+] ÉXITO. {total_sidecar} Entidades Inyectadas en sidecar {SIDECAR_PATH} (Modo WAL).\n")
        else:
            raise e

if __name__ == '__main__':
    main()
