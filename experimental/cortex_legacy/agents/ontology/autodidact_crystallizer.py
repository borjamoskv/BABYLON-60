import os
import yaml
import re

ONTOLOGY_DIR = "$CORTEX_ROOT/10_PROJECTS/Teorema-Robinson-Moskv/cortex/agents/ontology"
VANGUARD_AGENTS = "$CORTEX_ROOT/10_PROJECTS/Teorema-Robinson-Moskv/vanguard-reserve/AGENTS.md"


def parse_catalogo():
    path = os.path.join(ONTOLOGY_DIR, "CATALOGO_ENTIDADES_CORTEX.md")
    if not os.path.exists(path):
        return

    data = {}
    current_category = None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("## "):
                current_category = line.replace("## ", "").strip()
                data[current_category] = []
            elif line.startswith("- **") and current_category:
                match = re.match(r"- \*\*(.*?)\*\*(.*)", line)
                if match:
                    id_ = match.group(1).strip()
                    desc = match.group(2).strip()
                    if desc.startswith(":"):
                        desc = desc[1:].strip()
                    data[current_category].append({"id": id_, "name": desc})

    out_path = os.path.join(ONTOLOGY_DIR, "CATALOGO_ENTIDADES_CORTEX.yaml")
    with open(out_path, "w", encoding="utf-8") as yf:
        yaml.dump(data, yf, allow_unicode=True, sort_keys=False)
    print("[*] Cristalizado CATALOGO_ENTIDADES_CORTEX.md")


def parse_ouroboros():
    path = os.path.join(ONTOLOGY_DIR, "ouroboros_category_apex.md")
    if not os.path.exists(path):
        return

    data = {}
    current_section = None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("### "):
                current_section = line.replace("### ", "").strip()
                data[current_section] = []
            elif line.startswith("* **[") and current_section:
                match = re.match(r"\* \*\*\[(.*?)\](.*?)\*\*(.*)", line)
                if match:
                    id_ = match.group(1).strip()
                    name = match.group(2).strip()
                    desc = match.group(3).strip()
                    if desc.startswith(":"):
                        desc = desc[1:].strip()
                    data[current_section].append(
                        {"id": id_, "name": name, "description": desc}
                    )

    out_path = os.path.join(ONTOLOGY_DIR, "ouroboros_category_apex.yaml")
    with open(out_path, "w", encoding="utf-8") as yf:
        yaml.dump(data, yf, allow_unicode=True, sort_keys=False)
    print("[*] Cristalizado ouroboros_category_apex.md")


def parse_sinergia():
    path = os.path.join(ONTOLOGY_DIR, "sinergia_exergetica.md")
    if not os.path.exists(path):
        return

    data = []
    current_synergy = None
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line.startswith("### "):
                if current_synergy:
                    data.append(current_synergy)
                current_synergy = {
                    "title": line.replace("### ", "").strip(),
                    "details": {},
                }
            elif line.startswith("* **") and current_synergy:
                match = re.match(r"\* \*\*(.*?)\*\*(.*)", line)
                if match:
                    key = match.group(1).strip()
                    if key.endswith(":"):
                        key = key[:-1]
                    val = match.group(2).strip()
                    current_synergy["details"][key] = val
        if current_synergy:
            data.append(current_synergy)

    out_path = os.path.join(ONTOLOGY_DIR, "sinergia_exergetica.yaml")
    with open(out_path, "w", encoding="utf-8") as yf:
        yaml.dump(data, yf, allow_unicode=True, sort_keys=False)
    print("[*] Cristalizado sinergia_exergetica.md")


def parse_vanguard_agents():
    path = VANGUARD_AGENTS
    if not os.path.exists(path):
        return
    rules = []
    current_law = None
    with open(path, "r", encoding="utf-8") as f:
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

    out_yaml = os.path.join(ONTOLOGY_DIR, "vanguard_agents.yaml")
    if rules:
        with open(out_yaml, "w", encoding="utf-8") as yf:
            yaml.dump(
                {"leyes_vanguard": rules}, yf, allow_unicode=True, sort_keys=False
            )
        print("[*] Cristalizado vanguard-reserve/AGENTS.md")


def main():
    print("[*] Ejecutando Autodidact-Omega: Cristalización Absoluta...")
    parse_catalogo()
    parse_ouroboros()
    parse_sinergia()
    parse_vanguard_agents()
    print("[+] Completo.")


if __name__ == "__main__":
    main()
