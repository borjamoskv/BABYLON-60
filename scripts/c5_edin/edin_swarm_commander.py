#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import ast
import glob
import json
import os

WORKSPACE: str = os.environ.get("BABYLON_WORKSPACE", os.path.dirname(os.path.abspath(__file__)))
SHARDS_FILE: str = os.path.join(os.path.dirname(WORKSPACE), "data", "shards.json")


def _extract_node_vectors(fpath: str) -> list[dict[str, str]]:
    results: list[dict[str, str]] = []
    try:
        with open(fpath, "r", encoding="utf-8") as f:
            content = f.read()
        tree = ast.parse(content)
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                results.append(
                    {
                        "type": "AST_Function",
                        "target": f"{os.path.basename(fpath)}::{node.name}",
                        "directive": "Audit cyclomatic complexity and deterministic closure.",
                    }
                )
            elif isinstance(node, ast.ClassDef):
                results.append(
                    {
                        "type": "AST_Class",
                        "target": f"{os.path.basename(fpath)}::{node.name}",
                        "directive": "Audit memory footprint and state mutability.",
                    }
                )
    except (SyntaxError, FileNotFoundError):
        pass
    return results


def generate_100_vectors() -> list[dict[str, str]]:
    print("[CENTURIA] Initiating Surface Mapping...")
    vectors: list[dict[str, str]] = []
    py_files = glob.glob(f"{WORKSPACE}/**/*.py", recursive=True)
    for fpath in py_files:
        vectors.extend(_extract_node_vectors(fpath))
    vectors.extend(
        [
            {"type": "DB_Schema", "target": "L1_primitive_nodes", "directive": "Verify indexing and constraint rigor."},
            {
                "type": "DB_Schema",
                "target": "L2_isomorphism_edges",
                "directive": "Verify foreign key simulation and cascade.",
            },
            {
                "type": "DB_Schema",
                "target": "L3_inference_cache",
                "directive": "Verify hit/miss distribution and entropy.",
            },
            {
                "type": "Network",
                "target": "server.js",
                "directive": "Audit async event loop blocking and IPC overhead.",
            },
            {
                "type": "YAML_Config",
                "target": "cortex_inference_engine.yaml",
                "directive": "Audit structural integrity of trigger definitions.",
            },
        ]
    )
    print(f"[CENTURIA] Generated {len(vectors)} Deep Research Vectors (Pure Exergy).")
    shards: dict[str, list[dict[str, str]]] = {
        "Titan-1": vectors[:33],
        "Titan-2": vectors[33:66],
        "Titan-3": vectors[66:],
    }
    with open(SHARDS_FILE, "w", encoding="utf-8") as f:
        json.dump(shards, f, indent=2)
    print(f"[CENTURIA] Shards crystallized to {SHARDS_FILE}")
    return vectors


def main() -> None:
    generate_100_vectors()


if __name__ == "__main__":
    main()
