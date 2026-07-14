# C5-REAL: Convergencias y Redundancias Ontológicas
import os
import glob
import yaml
import re
import sys

ONTOLOGY_DIR: str = "$CORTEX_ROOT/borjamoskv/Teorema-Robinson-Moskv/cortex/agents/ontology"


def get_artifact_path(filename: str) -> str:
    base_brain_dir: str = os.path.expanduser("~/.gemini/antigravity/brain")
    target_dir: str = base_brain_dir
    if os.path.exists(base_brain_dir):
        subdirs: list[str] = [
            os.path.join(base_brain_dir, d)
            for d in os.listdir(base_brain_dir)
            if os.path.isdir(os.path.join(base_brain_dir, d)) and not d.startswith(".")
        ]
        if subdirs:
            target_dir = max(subdirs, key=os.path.getmtime)
    return os.path.join(target_dir, filename)


def extract_entities() -> list[dict[str, str]]:
    entities: list[dict[str, str]] = []

    prim1000_path: str = os.path.join(ONTOLOGY_DIR, "06_MATRIZ_1000.yaml")
    assert os.path.exists(prim1000_path), f"Falta el archivo: {prim1000_path}"

    with open(prim1000_path, "r", encoding="utf-8") as f:
        data: dict = yaml.safe_load(f)
        for t_key, t_val in data.items():
            if not isinstance(t_val, dict):
                continue
            for d_key, d_list in t_val.get("dimensions", {}).items():
                for prim in d_list:
                    entities.append(
                        {
                            "id": f"{t_key}:{prim}",
                            "text": f"{t_key} {d_key} {prim}",
                            "source": "MATRIZ_1000",
                        }
                    )

    yaml_pattern: str = os.path.join(ONTOLOGY_DIR, "*.yaml")
    for yf in glob.glob(yaml_pattern):
        basename: str = os.path.basename(yf)
        if basename == "CATALOGO_ENTIDADES_CORTEX.yaml":
            with open(yf, "r", encoding="utf-8") as f:
                data_cat: dict = yaml.safe_load(f) or {}
                for cat, items in data_cat.items():
                    for item in items:
                        entities.append(
                            {
                                "id": item.get("id", ""),
                                "text": item.get("name", ""),
                                "source": basename,
                            }
                        )
        elif basename[0].isdigit() and basename.endswith(".yaml"):
            with open(yf, "r", encoding="utf-8") as f:
                data_item: dict = yaml.safe_load(f) or {}
                for item in data_item.get("entities", []):
                    text: str = " ".join(str(v) for v in item.values())
                    item_id: str = item.get("id", text[:10])
                    entities.append({"id": item_id, "text": text, "source": basename})

    return entities


def tokenize(text: str) -> set[str]:
    words: list[str] = re.findall(r"\b\w+\b", str(text).lower())
    stop_words: set[str] = {
        "para",
        "como",
        "este",
        "esta",
        "pero",
        "todo",
        "nada",
        "algo",
    }
    return set([w for w in words if len(w) > 3 and w not in stop_words])


def jaccard(set1: set[str], set2: set[str]) -> float:
    if not set1 or not set2:
        return 0.0
    return len(set1.intersection(set2)) / len(set1.union(set2))


def main() -> None:
    entities: list[dict[str, str]] = extract_entities()
    sys.stdout.write(f"[*] Extracting tokens from {len(entities)} entities...\n")

    for e in entities:
        e["tokens"] = tokenize(e["text"])

    convergences: list[tuple[float, dict[str, str], dict[str, str]]] = []
    seen_pairs: set[tuple[str, str]] = set()

    for i in range(len(entities)):
        for j in range(i + 1, len(entities)):
            e1: dict[str, str] = entities[i]
            e2: dict[str, str] = entities[j]
            if e1["id"] == e2["id"]:
                continue

            score: float = jaccard(e1["tokens"], e2["tokens"])
            if score >= 0.40:
                pair: tuple[str, str] = tuple(sorted([e1["id"], e2["id"]]))
                if pair not in seen_pairs:
                    convergences.append((score, e1, e2))
                    seen_pairs.add(pair)

    convergences.sort(key=lambda x: x[0], reverse=True)

    artifact_path: str = get_artifact_path("redundancias_convergencias.md")
    os.makedirs(os.path.dirname(artifact_path), exist_ok=True)

    with open(artifact_path, "w", encoding="utf-8") as f:
        f.write("# 🌀 Convergencias y Redundancias Ontológicas\n\n")
        f.write("> [!CAUTION]\n")
        f.write(
            "> **Directiva C5-REAL (Ω6)**: La redundancia de estado es pudrición de contexto. Se exponen los nodos con colisión topológica superior al 40%.\n\n"
        )
        f.write(
            "Estas entidades exhiben isomorfismo parcial y deben purgarse o fusionarse (Nexus Bridging).\n\n"
        )
        f.write("| Score | Entidad A | Origen A | Entidad B | Origen B |\n")
        f.write("|---|---|---|---|---|\n")

        count: int = 0
        for score, e1, e2 in convergences:
            if count > 150:
                break
            f.write(
                f"| {score:.2f} | {e1['id']} | {e1['source']} | {e2['id']} | {e2['source']} |\n"
            )
            count += 1

    sys.stdout.write(
        f"[+] Análisis completo. Se encontraron {len(convergences)} convergencias. Artefacto generado en: {artifact_path}\n"
    )


if __name__ == "__main__":
    main()
