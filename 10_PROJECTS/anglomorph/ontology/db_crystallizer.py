import os
import re
import sqlite3
import sys

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(SCRIPT_DIR, "ontology.db")
ONTOLOGY_DIR = SCRIPT_DIR

SCHEMA = {
    "primitives": (
        "id TEXT PRIMARY KEY, name TEXT NOT NULL, mechanism TEXT NOT NULL, "
        "trigger TEXT NOT NULL, sensor TEXT NOT NULL, timescale TEXT NOT NULL, "
        "severity TEXT NOT NULL, intervention TEXT NOT NULL",
        8, "primitives.md"
    ),
    "invariants": (
        "id TEXT PRIMARY KEY, name TEXT NOT NULL, logic TEXT NOT NULL, "
        "implication TEXT NOT NULL, boundary_condition TEXT NOT NULL, "
        "falsifiable_metric TEXT NOT NULL",
        6, "invariants.md"
    ),
    "antipatterns": (
        "id TEXT PRIMARY KEY, name TEXT NOT NULL, disfunction TEXT NOT NULL, "
        "presence_signal TEXT NOT NULL, impact TEXT NOT NULL, "
        "refactor TEXT NOT NULL",
        6, "antipatterns.md"
    ),
    "redundancies": (
        "id TEXT PRIMARY KEY, name TEXT NOT NULL, topology TEXT NOT NULL, "
        "mitigated_risk TEXT NOT NULL, overhead TEXT NOT NULL, "
        "dependencies TEXT NOT NULL",
        6, "redundancies.md"
    ),
    "adversarial": (
        "id TEXT PRIMARY KEY, name TEXT NOT NULL, attack_surface TEXT NOT NULL, "
        "exploitation TEXT NOT NULL, thermodynamic_impact TEXT NOT NULL, "
        "defense TEXT NOT NULL",
        6, "adversarial.md"
    )
}

def parse_markdown_table(filepath):
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Archivo matriz no encontrado: {filepath}")
    
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    in_table = False
    for line in lines:
        line = line.strip()
        if line.startswith("|") and line.endswith("|"):
            if re.match(r"^\|\s*ID\s*\|", line, re.IGNORECASE) or "---" in line:
                in_table = True
                continue
            if in_table:
                cols = [c.strip() for c in line.split("|")[1:-1]]
                if cols and cols[0] and not cols[0].startswith("---"):
                    rows.append(cols)
    return rows

def main():
    print("Inicializando cristalización de ontología en SQLite (Protocolo C5-REAL)...")
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # 1. Staging: Parseo y validación pre-ejecución (Apoptosis Celular en caso de fallo)
    staged_data = {}
    for table_name, (schema_def, cols_count, filename) in SCHEMA.items():
        filepath = os.path.join(ONTOLOGY_DIR, filename)
        try:
            raw_rows = parse_markdown_table(filepath)
        except Exception as e:
            print(f"ERROR CRÍTICO: Fallo al leer {filename}. {e}")
            print("Abortando cristalización para evitar corrupción de estado (Apoptosis).")
            sys.exit(1)
            
        valid_rows = [row[:cols_count] for row in raw_rows if len(row) >= cols_count]
        if not valid_rows:
            print(f"ERROR CRÍTICO: La matriz {filename} produjo 0 registros válidos.")
            print("Abortando cristalización para evitar borrado de la tabla.")
            sys.exit(1)
            
        staged_data[table_name] = {
            "rows": valid_rows,
            "cols_count": cols_count,
            "schema": schema_def
        }
        
    # 2. Transacción de Mutación de Disco (Regla R10)
    conn = sqlite3.connect(DB_PATH, timeout=5.0)
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor = conn.cursor()
    
    try:
        cursor.execute("BEGIN EXCLUSIVE;")
        
        for table_name, data in staged_data.items():
            # Construcción de la tabla
            cursor.execute(f"CREATE TABLE IF NOT EXISTS {table_name} ({data['schema']});")
            # Vaciado atómico seguro (estamos en transacción y staging verificado)
            cursor.execute(f"DELETE FROM {table_name};")
            
            # Inserción matricial optimizada (executemany)
            placeholders = ",".join(["?"] * data["cols_count"])
            cursor.executemany(
                f"INSERT OR REPLACE INTO {table_name} VALUES ({placeholders})", 
                data["rows"]
            )
            
        conn.commit()
        print(f"Éxito: Cristalización completada y validada en {DB_PATH}.")
        
        for table_name in staged_data.keys():
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            print(f" -> Tabla '{table_name}': {cursor.fetchone()[0]} registros colapsados.")
            
    except Exception as e:
        conn.rollback()
        print(f"ERROR DURANTE TRANSACCIÓN (ROLLBACK EJECUTADO): {e}")
        sys.exit(1)
    finally:
        conn.close()

if __name__ == "__main__":
    main()
