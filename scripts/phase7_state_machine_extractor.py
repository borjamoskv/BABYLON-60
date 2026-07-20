import os
import json
import re


def extract_state_machine_graphs(target_dir):
    graphs = {
        "StateGraph": [],
        "MutationGraph": [],
        "TrustGraph": [],
        "EvidenceGraph": [],
    }

    for root, dirs, files in os.walk(target_dir):
        if any(
            x in root
            for x in [".venv", "node_modules", "__pycache__", ".git", "dist", "build"]
        ):
            continue
        for file in files:
            if file.endswith(".py") or file.endswith(".rs") or file.endswith(".sql"):
                filepath = os.path.join(root, file)
                rel_path = os.path.relpath(filepath, target_dir)
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        source = f.read()

                    # 1. StateGraph (Data models, schemas, state representation)
                    if re.search(
                        r"(class\s+\w+\(.*BaseModel.*\):|@dataclass|CREATE TABLE)",
                        source,
                    ):
                        graphs["StateGraph"].append(rel_path)

                    # 2. MutationGraph (State transitions, DB writes, disk writes)
                    if re.search(
                        r"(\.commit\(\)|UPDATE\s+\w+|INSERT\s+INTO|\.write\(|os\.remove)",
                        source,
                    ):
                        graphs["MutationGraph"].append(rel_path)

                    # 3. TrustGraph (Boundaries, auth, routers, FFI boundaries)
                    if re.search(
                        r"(@router\.|FastAPI\(|Depends\(get_current_user\)|unsafe\s*\{)",
                        source,
                    ):
                        graphs["TrustGraph"].append(rel_path)

                    # 4. EvidenceGraph (Hashing, BFT signatures, cryptographic proofs, Git Sentinel)
                    if re.search(
                        r"(hashlib\.sha3_256|hashlib\.sha256|\.hexdigest\(\)|git\s+commit|CORTEX-TAINT|BFT)",
                        source,
                    ):
                        graphs["EvidenceGraph"].append(rel_path)

                except (OSError, ValueError, SyntaxError, TypeError):
                    pass

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    out_json = os.path.join(
        project_root, "cortex", "artifacts", "reports", "BABYLON_60_STATE_MACHINE.json"
    )
    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w") as f:
        json.dump(graphs, f, indent=2)
    print(f"Extraction complete. Saved to {out_json}")


if __name__ == "__main__":
    extract_state_machine_graphs(os.path.expanduser("~/BABYLON-60"))
