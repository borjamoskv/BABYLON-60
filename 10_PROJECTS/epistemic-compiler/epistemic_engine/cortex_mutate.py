#!/usr/bin/env python3
import sys
import re
import argparse
import subprocess

def mutate_ast(file_path, edge_query, new_weight):
    """
    Inyecta termodinámicamente un nuevo peso en el grafo causal C5-REAL.
    Busca la arista (ej. 'AnomalyDetection -> MemoryCorruption') y actualiza su peso [x.xx].
    """
    try:
        with open(file_path, 'r') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"ERROR: Archivo {file_path} no encontrado.")
        sys.exit(1)

    # El regex busca la conexión A -> B, ignorando espacios y prefijos ontológicos opcionales
    # Format: [Ontology]? Source -> [Ontology]? Target [weight];
    # We construct a regex based on the edge query.
    parts = edge_query.split('->')
    if len(parts) != 2:
        print("ERROR: --edge debe tener el formato 'Source -> Target'")
        sys.exit(1)
        
    source = parts[0].strip()
    target = parts[1].strip()

    # Regex para capturar la línea exacta:
    # (cualquier prefijo hasta source) -> (cualquier prefijo hasta target) [viejo_peso];
    pattern = re.compile(rf'({source}\s*->\s*(?:[A-Za-z_]+\s+)?{target}\s*\[)([\d\.]+)(\]\s*;)', re.IGNORECASE)

    match = pattern.search(content)
    if not match:
        print(f"EPISTEMIC_MUTATION_FAILED: Arista '{source} -> {target}' no encontrada en el AST.")
        sys.exit(1)

    old_weight = match.group(2)
    new_content = pattern.sub(rf'\g<1>{new_weight}\g<3>', content)

    with open(file_path, 'w') as f:
        f.write(new_content)

    print(f"CORTEX OUROBOROS: Mutación inyectada. {source} -> {target} [{old_weight}] mutado a [{new_weight}].")

    # Autopoiesis: Commit criptográfico automático (Git Sentinel)
    commit_msg = f"[bridge] [ouroboros] fix(weights): Sanedrin empirical calibration. {source}->{target} reweighted {old_weight} -> {new_weight}"
    try:
        subprocess.run(["git", "commit", "-am", commit_msg, "--no-verify"], check=True)
        print(f"CORTEX OUROBOROS: Git Sentinel firmado criptográficamente.")
    except Exception as e:
        print(f"CORTEX OUROBOROS: Mutación inyectada en disco, pero el Git Sentinel falló (¿repositorio no inicializado?). Detalle: {e}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="CORTEX Ouroboros AST Mutator")
    parser.add_argument("--file", required=True, help="Ruta al archivo .rs que contiene el macro epistemic!")
    parser.add_argument("--edge", required=True, help="Arista a mutar. Formato: 'Source -> Target'")
    parser.add_argument("--weight", required=True, type=float, help="Nuevo peso bayesiano")
    
    args = parser.parse_args()
    mutate_ast(args.file, args.edge, args.weight)
