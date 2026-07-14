#!/usr/bin/env python3
# C5-REAL: Macrófago Ontológico Ouroboros (v2.2 — HARDENED)
# Erradicación Autónoma de Context Rot mediante Jaccard N-Grams, Mutación Directa y Git Sentinel.
#
# CHANGELOG v2.2 (sobre v2.1):
#   [P0] Purga anclada a inicio de fila (^| ID |): v2.1 amputaba filas que solo
#        CITABAN el ID en una celda (referencia cruzada) -> apoptosis colateral.
#   [P0] N-Grams keyed por índice, no por ID: los IDs duplicados (la presa de
#        este agente) colisionaban en el mapa y corrompían la similitud.
#   [P1] Git Sentinel con scope: add SOLO de los archivos mutados + reporte.
#        Anchor pre-apoptosis si el working tree está sucio (rollback garantizado).
#   [P1] Escritura atómica real (tempfile + os.replace, mismo filesystem).
#   [P1] Gate BFT: validate_ontology.py vía subprocess (cero acoplamiento AST)
#        antes de --execute. Fail-closed. Bypass explícito con --no-gate.
#   [P2] Dedupe de purgas, --threshold configurable, histograma de calibración,
#        léxico Anergía con word-boundaries (adiós falso positivo "inútil"~"útil").

import os
import re
import sys
import argparse
import tempfile
import subprocess

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
ID_SAFE = re.compile(r"^[A-Z]+-[A-Z0-9-]+$")

# Anergy Lexicon (Green Theater markers) # anergy
ANERGY_TOKENS = {  # anergy
    "holístico",
    "es importante",
    "sin embargo",
    "espero que",
    "útil",  # anergy
    "en conclusión",
    "cabe destacar",
    "por otro lado",
    "es crucial",  # anergy
    "sinergia",
    "paradigma",
    "revolucionario",
    "convergencia formal",  # anergy
    "c5-real",  # anergy
}  # anergy
ANERGY_PATTERNS = [
    re.compile(r"\b" + re.escape(t) + r"\b", re.IGNORECASE) for t in ANERGY_TOKENS
]


def tokenize_ngrams(text, n=2):
    text = text.lower()
    text = re.sub(r"[^a-z0-9áéíóúñü]", " ", text)
    tokens = text.split()
    stopwords = {
        "el",
        "la",
        "los",
        "las",
        "un",
        "una",
        "unos",
        "unas",
        "y",
        "e",
        "o",
        "u",
        "de",
        "del",
        "a",
        "en",
        "que",
        "para",
        "por",
        "con",
        "sin",
        "sobre",
        "como",
        "es",
        "son",
        "no",
        "si",
        "se",
        "su",
        "sus",
        "al",
        "lo",
    }
    tokens = [t for t in tokens if t not in stopwords and len(t) > 2]
    if len(tokens) < n:
        return set(tokens)
    return set(["_".join(tokens[i : i + n]) for i in range(len(tokens) - n + 1)])


def get_jaccard_similarity(set1, set2):
    if not set1 or not set2:
        return 0.0
    intersection = set1.intersection(set2)
    union = set1.union(set2)
    return len(intersection) / len(union)


def detect_anergy(content):
    return sum(1 for p in ANERGY_PATTERNS if p.search(content))


def parse_markdown_tables(filepath):
    entities = []
    with open(filepath, "r", encoding="utf-8") as f:
        lines = f.readlines()

    in_table = False
    headers = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("|") and not stripped.startswith("|-"):
            parts = [p.strip() for p in stripped.split("|")[1:-1]]
            if not in_table:
                if len(parts) > 0 and "ID" in parts[0].upper():
                    headers = parts
                    in_table = True
            else:
                if len(parts) == len(headers):
                    entity = dict(zip(headers, parts))
                    if "ID" in entity and entity["ID"].startswith(
                        ("ANTI-", "INV-", "PRIM-", "VEC-", "RED-")
                    ):
                        entities.append(
                            {
                                "id": entity["ID"],
                                "file": os.path.abspath(filepath),
                                "filename": os.path.basename(filepath),
                                "content": " ".join(parts[1:]),
                            }
                        )
        elif stripped.startswith("|-"):
            continue
        else:
            in_table = False

    return entities


def purge_entity(filepath, entity_id):
    """Elimina SOLO la fila definitoria (^| ID |). Escritura atómica (tempfile + os.replace)."""
    row_pattern = re.compile(r"^\|\s*" + re.escape(entity_id) + r"\s*\|")
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            lines = f.readlines()

        new_lines = [line for line in lines if not row_pattern.match(line.lstrip())]

        removed = len(lines) - len(new_lines)
        if removed > 0:
            fd, tmp_path = tempfile.mkstemp(
                dir=os.path.dirname(filepath), suffix=".macrofago"
            )
            try:
                with os.fdopen(fd, "w", encoding="utf-8") as f:
                    f.writelines(new_lines)
                os.replace(tmp_path, filepath)
            except BaseException:
                os.unlink(tmp_path)
                raise
        return removed
    except Exception as e:
        print(f"[-] Falla al purgar {entity_id} en {filepath}: {e}")
        return 0


def run_validation_gate():
    """Gate BFT: proceso aislado, cero import cruzado. Fail-closed."""
    gate = os.path.join(SCRIPT_DIR, "validate_ontology.py")
    if not os.path.exists(gate):
        print(
            "[-] GATE AUSENTE (validate_ontology.py). Fail-closed: apoptosis DENEGADA. Usa --no-gate para forzar."
        )
        return False
    print("[*] Ejecutando Validation Gateway (validate_ontology.py)...")
    result = subprocess.run([sys.executable, gate], capture_output=True, text=True)
    for line in result.stdout.strip().splitlines()[-3:]:
        print(f"    {line}")
    if result.returncode != 0:
        print("[-] GATE FALLIDO: la ontología no es íntegra. Apoptosis DENEGADA.")
        return False
    print("[+] Gate superado. Integridad verificada.")
    return True


def _git(directory, *args):
    return subprocess.run(
        ["git", "-C", directory] + list(args),
        check=True,
        capture_output=True,
        text=True,
    )


def git_preanchor(directory, files):
    """Ancla el estado PRE-apoptosis si hay mutaciones sin commitear (rollback garantizado)."""
    try:
        status = _git(directory, "status", "--porcelain", "--", *files).stdout.strip()
        if not status:
            return True
        _git(directory, "add", "--", *files)
        _git(
            directory,
            "commit",
            "-m",
            "[Macrófago] Anchor pre-apoptosis: estado previo asegurado",
            "--no-verify",
        )
        print(
            "[+] Git Sentinel: anchor pre-apoptosis commiteado (working tree estaba sucio)."
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] Git pre-anchor falló: {(e.stderr or str(e)).strip()}")
        return False


def git_sentinel_commit(directory, files, purged_count):
    """Commit atómico con scope: SOLO los archivos mutados + reporte. --no-verify por directiva."""
    try:
        _git(directory, "add", "--", *files)
        msg = f"[Macrófago] Apoptosis termodinámica ejecutada: {purged_count} entidades purgadas"
        _git(directory, "commit", "-m", msg, "--no-verify")
        print("[+] Git Sentinel: commit anclado (--no-verify).")
        return True
    except subprocess.CalledProcessError as e:
        print(f"[-] Git Sentinel falló: {(e.stderr or str(e)).strip()}")
        return False


def main():
    parser = argparse.ArgumentParser(
        description="Macrófago Ontológico Ouroboros (C5-REAL v2.2)"
    )
    parser.add_argument("--dir", type=str, default=".", help="Directorio objetivo")
    parser.add_argument(
        "--execute", action="store_true", help="Ejecuta la apoptosis real en disco"
    )
    parser.add_argument(
        "--threshold", type=float, default=0.08, help="Umbral Jaccard (default 0.08)"
    )
    parser.add_argument(
        "--no-gate",
        action="store_true",
        help="Saltar el Validation Gateway (entropía asumida)",
    )
    args = parser.parse_args()

    directory = args.dir
    threshold = args.threshold
    is_dry_run = not args.execute

    print(f"[*] Iniciando Macrófago Ontológico Ouroboros v2.2 en {directory}...")
    if is_dry_run:
        print(
            "[!] EJECUCIÓN DRY-RUN: Usa --execute para mutar el disco y crear commits."
        )
    elif args.no_gate:
        print("[!] Gate BYPASSED (--no-gate). Entropía asumida por el Operador.")
    elif not run_validation_gate():
        sys.exit(1)

    all_entities = []
    for root, dirs, files in os.walk(directory):
        for f in files:
            if f.endswith(".md"):
                filepath = os.path.join(root, f)
                try:
                    entities = parse_markdown_tables(filepath)
                    all_entities.extend(entities)
                except Exception as e:
                    print(f"[-] Omitiendo {filepath}: {e}")

    print(f"[*] Ingestadas {len(all_entities)} entidades ontológicas en memoria.")

    # 1. Procesamiento de N-Grams e indexación libre de colisiones (P0)
    for ent in all_entities:
        bg = tokenize_ngrams(ent["content"], 2)
        tg = tokenize_ngrams(ent["content"], 3)
        ent["ngrams"] = bg.union(tg)
        ent["anergy"] = detect_anergy(ent["content"])

    purges_queue = {}  # filepath -> lista de IDs a remover
    files_to_mutate = set()
    total_anergy_score = 0
    anergy_fractures = []
    redundancies = []
    bands = {">=0.5": 0, "[0.2, 0.5)": 0, "[threshold, 0.2)": 0}

    print(f"[*] Analizando redundancias con umbral Jaccard >= {threshold}...")

    # 2. Bucle de Similitud Cruzada indexado (Evita colisiones de IDs redundantes)
    for i in range(len(all_entities)):
        ent_i = all_entities[i]
        total_anergy_score += ent_i["anergy"]
        if ent_i["anergy"] > 0:
            anergy_fractures.append((ent_i, ent_i["anergy"]))

        for j in range(i + 1, len(all_entities)):
            ent_j = all_entities[j]

            sim = get_jaccard_similarity(ent_i["ngrams"], ent_j["ngrams"])

            # Solo comparar si son IDs idénticos o tienen alta similitud semántica
            if ent_i["id"] == ent_j["id"] or sim >= threshold:
                cat1 = ent_i["id"].split("-")[0]
                cat2 = ent_j["id"].split("-")[0]
                is_symbiotic = cat1 != cat2

                if sim >= 0.5:
                    bands[">=0.5"] += 1
                elif sim >= 0.2:
                    bands["[0.2, 0.5)"] += 1
                else:
                    bands["[threshold, 0.2)"] += 1

                redundancies.append(
                    {
                        "score": round(sim, 3),
                        "node_A": ent_i["id"],
                        "node_B": ent_j["id"],
                        "filepath_B": ent_j["file"],
                        "filename_A": ent_i["filename"],
                        "filename_B": ent_j["filename"],
                        "symbiotic": is_symbiotic,
                    }
                )

                if not is_symbiotic:
                    # Mantener la primera ocurrencia, marcar la posterior para Apoptosis
                    presa = ent_j if ent_i["file"] <= ent_j["file"] else ent_i
                    if ID_SAFE.match(presa["id"]):
                        if presa["file"] not in purges_queue:
                            purges_queue[presa["file"]] = set()
                        purges_queue[presa["file"]].add(presa["id"])
                        files_to_mutate.add(presa["file"])

    redundancies.sort(key=lambda x: x["score"], reverse=True)

    # 3. Reporte de Métricas / Histograma Base
    print(
        f"[+] Alerta de Anergía: Se detectaron {total_anergy_score} marcadores de 'Green Theater' en el sistema."
    )
    print(
        f"[*] Entidades marcadas para apoptosis: {sum(len(v) for v in purges_queue.values())}"
    )
    print(f"    Histograma: {bands}  <- calibra --threshold con esto\n")

    yaml_out = os.path.join(directory, "apoptosis_target.yaml")
    with open(yaml_out, "w", encoding="utf-8") as f:
        f.write("Claim: Análisis Estructural y Apoptosis\n")
        f.write(
            "Proof: { Base: N-Gram Jaccard Index & Anergy Lexicon, Confidence: C5-REAL }\n"
        )
        f.write(f"Threshold: {threshold}\n")
        if anergy_fractures:
            f.write("Anergy_Infections:\n")
            for ent, score in anergy_fractures:
                f.write(f"  - node: {ent['id']}\n")
                f.write(f"    score: {score}\n")
        f.write("Fractures:\n")
        for r in redundancies:
            f.write(f"  - nodes: [{r['node_A']}, {r['node_B']}]\n")
            f.write(f"    score: {r['score']}\n")
            f.write(f"    files: [{r['filename_A']}, {r['filename_B']}]\n")
            f.write(f"    symbiotic: {str(r['symbiotic']).lower()}\n")

    print(f"[*] Reporte cristalizado en {yaml_out}.")

    if not purges_queue:
        print("[+] Red de CORTEX limpia. Sistema equilibrado. Termodinámica estable.")
        sys.exit(0)

    # 4. Fase de Mutación / Ejecución Atómica
    if is_dry_run:
        print("\n[!]--- SIMULACIÓN DE APOPTOSIS (DRY-RUN) ---")
        for filepath, ids in purges_queue.items():
            print(
                f"  [Presa] {os.path.basename(filepath)} -> IDs a purgar: {list(ids)}"
            )
        print("[!] No se realizaron cambios en disco. Añade --execute para mutar.")
        sys.exit(0)

    # 5. Ejecución Real con Seguro Criptográfico (Git Sentinel)
    print("\n[*] Ejecutando mutación atómica en disco...")

    # Git Pre-Anchor (Garantiza rollback si el árbol de trabajo está sucio)
    if not git_preanchor(directory, list(files_to_mutate)):
        print("[-] Abortando operación: Fallo en el seguro criptográfico previo.")
        sys.exit(1)

    total_purged = 0
    mutated_files = []

    for filepath, ids in purges_queue.items():
        purged_in_file = 0
        for entity_id in ids:
            purged_in_file += purge_entity(filepath, entity_id)

        if purged_in_file > 0:
            total_purged += purged_in_file
            mutated_files.append(filepath)
            print(
                f"  [MUTATED] {os.path.basename(filepath)}: {purged_in_file} filas purgadas."
            )

    # 6. Commit de Cierre (Regla Ω3 — Ouroboros)
    if total_purged > 0:
        print(f"[+] Mutación completada. {total_purged} filas eliminadas.")
        if git_sentinel_commit(directory, mutated_files + [yaml_out], total_purged):
            print(
                "[+] Bucle Ouroboros cerrado con éxito. Registro criptográfico fijado."
            )
        else:
            print(
                "[-] Alerta: Los cambios se guardaron pero el commit del Sentinel falló."
            )
    else:
        print(
            "[-] No se eliminaron filas. Las estructuras no coincidieron con el anclaje físico ^| ID |."
        )


if __name__ == "__main__":
    main()
