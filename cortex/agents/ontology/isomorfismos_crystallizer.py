# C5-REAL: Isomorfismos Crystallizer
import os
import json
import yaml
import sys

ONTOLOGY_DIR: str = "$CORTEX_ROOT/borjamoskv/Teorema-Robinson-Moskv/cortex/agents/ontology"

def parse_isomorfismos() -> None:
    md_file: str = os.path.join(ONTOLOGY_DIR, "07_ISOMORFISMOS_BIO_SILICIO.md")
    assert os.path.exists(md_file), f"MD file does not exist: {md_file}"

    data: dict[str, list[dict[str, str]]] = {}
    current_category: str | None = None

    with open(md_file, "r", encoding="utf-8") as f:
        for line in f:
            line_str: str = line.strip()
            if not line_str:
                continue
            if line_str.startswith("## ") or (line_str[0].isdigit() and ". " in line_str and not line_str.startswith("1. Cognición")):
                current_category = line_str.replace("## ", "").strip()
                data[current_category] = []
            elif line_str.startswith("|") and not line_str.startswith("|-"):
                parts: list[str] = [p.strip() for p in line_str.split("|")[1:-1]]
                if len(parts) == 2:
                    if all(all(c in "- " for c in part) for part in parts):
                        continue
                    dom_a: str = parts[0].lower()
                    if dom_a not in ["humano", "biológico/social (humano)", "físico / mecánico (relevo 4x4)", "biológico/social humano"]:
                        if current_category:
                            data[current_category].append({
                                "domain_a": parts[0],
                                "domain_b": parts[1]
                             })

    json_file: str = os.path.join(ONTOLOGY_DIR, "07_ISOMORFISMOS_BIO_SILICIO.json")
    with open(json_file, "w", encoding="utf-8") as jf:
        json.dump(data, jf, indent=2, ensure_ascii=False)

    yaml_file: str = os.path.join(ONTOLOGY_DIR, "07_ISOMORFISMOS_BIO_SILICIO.yaml")
    with open(yaml_file, "w", encoding="utf-8") as yf:
        yaml.dump(data, yf, allow_unicode=True, sort_keys=False)

    total_mappings: int = sum(len(mappings) for mappings in data.values())
    sys.stdout.write(f"[*] Cristalizado 07_ISOMORFISMOS_BIO_SILICIO.md -> JSON/YAML ({total_mappings} mappings extraídos)\n")

def main() -> None:
    sys.stdout.write("[*] Iniciando cristalización de Isomorfismos a JSON/YAML...\n")
    parse_isomorfismos()
    sys.stdout.write("[+] Colapso a JSON completado.\n")

if __name__ == '__main__':
    main()
