import os
import re
import sqlite3

DB_PATH = "$CORTEX_ROOT/10_PROJECTS/anglomorph/ontology/ontology.db"
ONTOLOGY_DIR = "$CORTEX_ROOT/10_PROJECTS/anglomorph/ontology"

def parse_markdown_table(filepath):
    if not os.path.exists(filepath):
        print(f"Error: {filepath} no existe.")
        return []
    
    rows = []
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()
        
    in_table = False
    for line in lines:
        line = line.strip()
        if line.startswith("|") and line.endswith("|"):
            # Omitir cabecera (ID) y divisores (que contienen múltiples guiones continuos)
            if re.match(r"^\|\s*ID\s*\|", line, re.IGNORECASE) or "---" in line:
                in_table = True
                continue
            if in_table:
                # Separar columnas por pipe
                cols = [c.strip() for c in line.split("|")[1:-1]]
                if cols and cols[0] and not cols[0].startswith("---"):
                    rows.append(cols)
    return rows

def main():
    print("Inicializando cristalización de ontología en SQLite...")
    
    # Asegurar que el directorio de salida existe
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    # Inicializar conexión (Cumpliendo R10: busy_timeout=5000 y WAL)
    conn = sqlite3.connect(DB_PATH, timeout=5.0) # 5000ms
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    cursor = conn.cursor()
    
    # 1. Crear tablas
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS primitives (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            mechanism TEXT NOT NULL,
            trigger TEXT NOT NULL,
            sensor TEXT NOT NULL,
            timescale TEXT NOT NULL,
            severity TEXT NOT NULL,
            intervention TEXT NOT NULL
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS invariants (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            logic TEXT NOT NULL,
            implication TEXT NOT NULL,
            boundary_condition TEXT NOT NULL,
            falsifiable_metric TEXT NOT NULL
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS antipatterns (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            disfunction TEXT NOT NULL,
            presence_signal TEXT NOT NULL,
            impact TEXT NOT NULL,
            refactor TEXT NOT NULL
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS redundancies (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            topology TEXT NOT NULL,
            mitigated_risk TEXT NOT NULL,
            overhead TEXT NOT NULL,
            dependencies TEXT NOT NULL
        );
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS adversarial (
            id TEXT PRIMARY KEY,
            name TEXT NOT NULL,
            attack_surface TEXT NOT NULL,
            exploitation TEXT NOT NULL,
            thermodynamic_impact TEXT NOT NULL,
            defense TEXT NOT NULL
        );
    """)
    
    # Limpiar tablas previas antes del volcado
    cursor.execute("DELETE FROM primitives;")
    cursor.execute("DELETE FROM invariants;")
    cursor.execute("DELETE FROM antipatterns;")
    cursor.execute("DELETE FROM redundancies;")
    cursor.execute("DELETE FROM adversarial;")
    
    # 2. Parsear y volcar datos
    # Primitivas
    primitives = parse_markdown_table(os.path.join(ONTOLOGY_DIR, "primitives.md"))
    for row in primitives:
        if len(row) >= 8:
            cursor.execute("INSERT OR REPLACE INTO primitives VALUES (?,?,?,?,?,?,?,?)", row[:8])
            
    # Invariantes
    invariants = parse_markdown_table(os.path.join(ONTOLOGY_DIR, "invariants.md"))
    for row in invariants:
        if len(row) >= 6:
            cursor.execute("INSERT OR REPLACE INTO invariants VALUES (?,?,?,?,?,?)", row[:6])
            
    # Antipatrones
    antipatterns = parse_markdown_table(os.path.join(ONTOLOGY_DIR, "antipatterns.md"))
    for row in antipatterns:
        if len(row) >= 6:
            cursor.execute("INSERT OR REPLACE INTO antipatterns VALUES (?,?,?,?,?,?)", row[:6])
            
    # Redundancias
    redundancies = parse_markdown_table(os.path.join(ONTOLOGY_DIR, "redundancies.md"))
    for row in redundancies:
        if len(row) >= 6:
            cursor.execute("INSERT OR REPLACE INTO redundancies VALUES (?,?,?,?,?,?)", row[:6])
            
    # Adversariales
    adversarial = parse_markdown_table(os.path.join(ONTOLOGY_DIR, "adversarial.md"))
    for row in adversarial:
        if len(row) >= 6:
            cursor.execute("INSERT OR REPLACE INTO adversarial VALUES (?,?,?,?,?,?)", row[:6])
            
    conn.commit()
    print(f"Éxito: Cristalización completada en {DB_PATH}.")
    
    # Validar número de registros insertados
    for table in ["primitives", "invariants", "antipatterns", "redundancies", "adversarial"]:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        print(f" -> Tabla '{table}': {count} registros colapsados.")
        
    conn.close()

if __name__ == "__main__":
    main()
