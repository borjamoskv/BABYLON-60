import os
import glob
import yaml
import re

ONTOLOGY_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_DIR = os.path.expanduser("~/.gemini/config")


def parse_markdown_table(filepath):
    entities = []
    headers = []
    in_table = False

    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("|") and not line.startswith("|-"):
                parts = [p.strip() for p in line.split("|")[1:-1]]
                if not in_table:
                    if parts and "ID" in parts[0].upper():
                        headers = [
                            h.replace(" ", "_")
                            .replace("(", "")
                            .replace(")", "")
                            .replace("/", "_")
                            .lower()
                            for h in parts
                        ]
                        in_table = True
                else:
                    if len(parts) == len(headers) and parts[0].startswith(
                        ("PRIM", "INV", "ANTI", "RED", "VEC")
                    ):
                        entities.append(dict(zip(headers, parts)))
            elif line.startswith("|-"):
                continue
            else:
                in_table = False
    return entities


def process_ontology_mds():
    md_files = glob.glob(os.path.join(ONTOLOGY_DIR, "[0-9][0-9]_*.md"))
    for md_file in md_files:
        basename = os.path.basename(md_file)
        if basename == "06_MATRIZ_1000.md":
            continue  # Already came from YAML

        entities = parse_markdown_table(md_file)
        if entities:
            yaml_path = md_file.replace(".md", ".yaml")
            with open(yaml_path, "w", encoding="utf-8") as yf:
                yaml.dump(
                    {"entities": entities}, yf, allow_unicode=True, sort_keys=False
                )
            print(
                f"[*] Cristalizado {basename} -> {os.path.basename(yaml_path)} ({len(entities)} entidades)"
            )


def parse_agents_md():
    agents_path = os.path.join(CONFIG_DIR, "AGENTS.md")
    rules = []
    current_law = None

    with open(agents_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("## [L"):
                current_law = line.replace("## ", "")
            elif line.startswith("- **") and current_law:
                match = re.match(r"- \*\*(.*?)\*\*(.*)", line)
                if match:
                    rule_id = match.group(1).strip()
                    desc = match.group(2).strip()
                    if desc.startswith(":"):
                        desc = desc[1:].strip()
                    rules.append(
                        {"law": current_law, "rule_id": rule_id, "description": desc}
                    )

    out_yaml = os.path.join(ONTOLOGY_DIR, "leyes_ouroboros_agents.yaml")
    with open(out_yaml, "w", encoding="utf-8") as yf:
        yaml.dump({"leyes": rules}, yf, allow_unicode=True, sort_keys=False)
    print(
        f"[*] Cristalizado AGENTS.md -> leyes_ouroboros_agents.yaml ({len(rules)} reglas)"
    )


def main():
    print("[*] Iniciando cristalización masiva a YAML...")
    process_ontology_mds()
    parse_agents_md()
    print("[+] Colapso a YAML completado.")


if __name__ == "__main__":
    main()
