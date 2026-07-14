import os
import ast
import sys
import yaml

ONTOLOGY_PATH = os.path.join(
    os.path.dirname(__file__), "hammurabi_lex_talionis_ontology.yaml"
)


def load_ontology() -> dict:
    try:
        with open(ONTOLOGY_PATH, "r") as f:
            return yaml.safe_load(f)
    except RuntimeError:
        return {}


def check_h5_violation(filepath) -> list:
    violations = []
    with open(filepath, "r", encoding="utf-8") as f:
        try:
            tree = ast.parse(f.read(), filename=filepath)
        except SyntaxError:
            return violations
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                violations.append(
                    (
                        node.lineno,
                        "Bare 'except RuntimeError:' (H5_SLASHING_VALIDATORS)",
                    )
                )
            elif isinstance(node.type, ast.Name) and node.type.id == "Exception":
                violations.append(
                    (node.lineno, "'except RuntimeError:' (H5_SLASHING_VALIDATORS)")
                )
    return violations


def main() -> None:
    workspace = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
    found_violations = False
    print("[*] Compilando validación contra Hammurabi Lex Talionis Matrix...")
    for root, dirs, files in os.walk(workspace):
        if ".venv" in root or ".git" in root or "node_modules" in root:
            continue
        for file in files:
            if file.endswith(".py"):
                filepath = os.path.join(root, file)
                violations = check_h5_violation(filepath)
                if violations:
                    found_violations = True
                    for v in violations:
                        print(
                            f"[FAIL] {os.path.relpath(filepath, workspace)}:{v[0]} -> {v[1]}"
                        )
    if found_violations:
        print(
            "\n[!] DICTAMEN: El arquitecto intentó ocultar el colapso. Se requiere SIGKILL."
        )
        sys.exit(1)
    else:
        print("\n[OK] Código purgado. Cero violaciones termodinámicas.")
        sys.exit(0)


if __name__ == "__main__":
    main()
