# C5-REAL EXERGY CERTIFIED
import os
import re
import json


from typing import Any


class EpistemicHalt(Exception):
    """C5-REAL structural failure. Replaces os.kill(SIGKILL) per Ω26."""


def classify_omega_theorem(target_dir: str) -> None:
    classification: dict[str, list[Any]] = {
        "Observe": [],
        "Transform": [],
        "Verify": [],
        "Commit": [],
        "Accidental_Complexity": [],
    }

    for root, dirs, files in os.walk(target_dir):
        if any(
            x in root
            for x in [
                ".venv",
                "node_modules",
                "__pycache__",
                ".git",
                "dist",
                "build",
                "cortex",
            ]
        ):
            continue
        for file in files:
            if not (file.endswith(".py") or file.endswith(".rs") or file.endswith(".sql")):
                continue

            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, target_dir)
            try:
                with open(filepath, "r", encoding="utf-8") as f:
                    source = f.read()

                is_O = bool(
                    re.search(
                        r"(@router\.|FastAPI\(|webhook|requests\.get|urllib|CLI|argparse)",
                        source,
                    )
                )
                is_T = bool(
                    re.search(
                        r"(AST|Transformer|LLM|Ollama|generate_local|Mutator|builder)",
                        source,
                        re.IGNORECASE,
                    )
                )
                is_V = bool(
                    re.search(
                        r"(validator|assert |isinstance|typeguard|BFT_State_Loop|pydantic|unsafe\s*\{)",
                        source,
                    )
                )
                is_C = bool(
                    re.search(
                        r"(\.commit\(\)|UPDATE\s+|INSERT\s+|WAL|busy_timeout|hashlib|git\s+commit|os\.write)",
                        source,
                    )
                )

                # Falsification Criterion: A file can only belong to one primary operator.
                # If it overlaps in mutation (T) and persistence (C), or validation (V) and UI (O), it's a God Object.
                matches = sum([is_O, is_T, is_V, is_C])

                if matches == 1:
                    if is_O:
                        classification["Observe"].append(rel_path)
                    elif is_T:
                        classification["Transform"].append(rel_path)
                    elif is_V:
                        classification["Verify"].append(rel_path)
                    elif is_C:
                        classification["Commit"].append(rel_path)
                else:
                    # Entropic residue (0 matches or >1 match)
                    reason = "Overlapping Operators" if matches > 1 else "No Logical Operator"
                    classification["Accidental_Complexity"].append(
                        {"file": rel_path, "reason": reason, "matches": matches}
                    )

            except (OSError, ValueError, TypeError, SyntaxError) as e:
                raise EpistemicHalt(f"Error parseando {rel_path}: {e}. Ejecutando purga (Ω26).")

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_json = os.path.join(project_root, "cortex", "artifacts", "reports", "BABYLON_60_THEOREM_OMEGA.json")
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(classification, f, indent=2)
    print(f"Omega Classification complete. Saved to {out_json}")


if __name__ == "__main__":
    target = os.environ.get("CORTEX_TARGET_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    if not target:
        raise RuntimeError("CORTEX_TARGET_DIR env var is required (Ω23).")
    classify_omega_theorem(target)
