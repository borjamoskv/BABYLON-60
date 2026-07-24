import sqlite3
from pathlib import Path

def get_lexicon_db_path() -> Path:
    return Path(__file__).parent.parent / "cortex_lexicon.db"

def main() -> None:
    db_path = get_lexicon_db_path()
    if not db_path.exists():
        print("FATAL: cortex_lexicon.db not found.")
        return
        
    with sqlite3.connect(db_path) as conn:
        # Extraer métricas globales
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM lexicon_nodes")
        total_nodes = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM lexicon_edges")
        total_edges = cur.fetchone()[0]
        
        # Extraer base concepts y algunos ejemplos estructurales
        base_nodes = conn.execute("SELECT concept_hash, canonical_name FROM lexicon_nodes WHERE canonical_name IN ('ACTION', 'ENTITY', 'EXERGY', 'ANERGY', 'BYZANTINE_FAULT_TOLERANCE', 'TRUTH_C5')").fetchall()
        edges = conn.execute("SELECT source_hash, target_hash, relation_type FROM lexicon_edges").fetchall()
        asts = conn.execute("SELECT concept_hash, canonical_name FROM lexicon_nodes WHERE canonical_name LIKE 'AST::%' ORDER BY lamport_t LIMIT 3").fetchall()
        invs = conn.execute("SELECT concept_hash, canonical_name FROM lexicon_nodes WHERE canonical_name LIKE 'INVARIANT::%' ORDER BY lamport_t LIMIT 3").fetchall()
        
        print("### Mapeo Topológico del DAG Criptográfico")
        print(f"**Total Nodos Físicos:** {total_nodes}")
        print(f"**Total Aristas Causales:** {total_edges}")
        print("\n```mermaid")
        print("graph TD")
        print("    classDef base fill:#2B3BE5,stroke:#0A0A0A,stroke-width:2px,color:#fff;")
        print("    classDef ast fill:#0A0A0A,stroke:#2B3BE5,stroke-width:1px,color:#fff;")
        print("    classDef inv fill:#E52B2B,stroke:#0A0A0A,stroke-width:1px,color:#fff;")
        
        for h, name in base_nodes:
            print(f'    {h[:8]}["{name}"]:::base')
            
        for h, name in asts:
            print(f'    {h[:8]}["{name}"]:::ast')
            
        for h, name in invs:
            print(f'    {h[:8]}["{name}"]:::inv')
            
        for src, tgt, rel in edges:
            print(f'    {src[:8]} -->|{rel}| {tgt[:8]}')
            
        print("```")

if __name__ == "__main__":
    main()
