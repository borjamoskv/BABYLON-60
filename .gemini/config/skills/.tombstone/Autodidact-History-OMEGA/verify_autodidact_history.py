# C5-REAL
# Verification script for Autodidact-History-OMEGA v3.0
import sys
import json
import subprocess
from pathlib import Path


def verify():
    base_dir = Path(__file__).parent
    skill_md = base_dir / "SKILL.md"
    schema_json = base_dir / "schema.json"
    script_py = base_dir / "scripts" / "retrieve_history.py"

    # ── 1. File existence ──
    for f, label in [(skill_md, "SKILL.md"), (schema_json, "schema.json"), (script_py, "retrieve_history.py")]:
        if not f.exists():
            sys.exit(f"Claim: Verification Failed\nProof: {{ Base: [{label}_missing], Confidence: [C5-REAL] }}")

    # ── 2. Schema integrity ──
    try:
        schema_data = json.loads(schema_json.read_text())
        required_props = {"query", "search", "timeline", "markdown", "range", "era", "dot", "stats"}
        actual_props = set(schema_data.get("properties", {}).keys())
        missing = required_props - actual_props
        if missing:
            sys.exit(f"Claim: Verification Failed\nProof: {{ Base: [schema_missing_properties: {missing}], Confidence: [C5-REAL] }}")
    except Exception as e:
        sys.exit(f"Claim: Verification Failed\nProof: {{ Base: [schema_json_invalid: {e}], Confidence: [C5-REAL] }}")

    # ── 3. Functional runtime verification ──
    py = sys.executable

    # 3a. --list
    r = subprocess.run([py, str(script_py), "--list"], capture_output=True, text=True, check=True)
    if "turing" not in r.stdout or "cortex_mesh" not in r.stdout or "backprop" not in r.stdout:
        sys.exit("Claim: Verification Failed\nProof: { Base: [missing_core_nodes_in_list], Confidence: [C5-REAL] }")

    # 3b. Single query
    r = subprocess.run([py, str(script_py), "turing"], capture_output=True, text=True, check=True)
    if "EXEC: TURING" not in r.stdout:
        sys.exit("Claim: Verification Failed\nProof: { Base: [query_turing_output_corrupt], Confidence: [C5-REAL] }")

    # 3c. Search
    r = subprocess.run([py, str(script_py), "--search", "cortex"], capture_output=True, text=True, check=True)
    if "EXEC: CORTEX_MESH" not in r.stdout:
        sys.exit("Claim: Verification Failed\nProof: { Base: [search_cortex_output_corrupt], Confidence: [C5-REAL] }")

    # 3d. --range filter
    r = subprocess.run([py, str(script_py), "--range", "2020-2024", "--list"], capture_output=True, text=True, check=True)
    if "gpt3" not in r.stdout or "chatgpt_moment" not in r.stdout:
        sys.exit("Claim: Verification Failed\nProof: { Base: [range_filter_failed], Confidence: [C5-REAL] }")

    # 3e. --era filter
    r = subprocess.run([py, str(script_py), "--era", "deep_learning", "--list"], capture_output=True, text=True, check=True)
    if "alexnet" not in r.stdout or "transformers" not in r.stdout:
        sys.exit("Claim: Verification Failed\nProof: { Base: [era_filter_failed], Confidence: [C5-REAL] }")

    # 3f. --stats
    r = subprocess.run([py, str(script_py), "--stats"], capture_output=True, text=True, check=True)
    if "Total nodes:" not in r.stdout:
        sys.exit("Claim: Verification Failed\nProof: { Base: [stats_output_corrupt], Confidence: [C5-REAL] }")

    # 3g. --dot
    r = subprocess.run([py, str(script_py), "--dot"], capture_output=True, text=True, check=True)
    if "digraph" not in r.stdout or "turing" not in r.stdout:
        sys.exit("Claim: Verification Failed\nProof: { Base: [dot_output_corrupt], Confidence: [C5-REAL] }")

    # 3h. --markdown
    r = subprocess.run([py, str(script_py), "--markdown"], capture_output=True, text=True, check=True)
    if "| Era |" not in r.stdout or "backprop" not in r.stdout:
        sys.exit("Claim: Verification Failed\nProof: { Base: [markdown_output_corrupt], Confidence: [C5-REAL] }")

    # 3i. JSON output
    r = subprocess.run([py, str(script_py), "turing", "--json"], capture_output=True, text=True, check=True)
    try:
        data = json.loads(r.stdout)
        assert data["id"] == "turing"
        assert data["year"] == 1950
        assert "era" in data
        assert "protagonists" in data
    except (json.JSONDecodeError, AssertionError, KeyError) as e:
        sys.exit(f"Claim: Verification Failed\nProof: {{ Base: [json_output_invalid: {e}], Confidence: [C5-REAL] }}")

    # 3j. Alias resolution
    r = subprocess.run([py, str(script_py), "kasparov"], capture_output=True, text=True, check=True)
    if "EXEC: DEEP_BLUE" not in r.stdout:
        sys.exit("Claim: Verification Failed\nProof: { Base: [alias_kasparov_failed], Confidence: [C5-REAL] }")

    # 3k. Node count
    r = subprocess.run([py, str(script_py), "--list"], capture_output=True, text=True, check=True)
    node_count = len([line for line in r.stdout.strip().split("\n") if "•" in line])
    if node_count < 36:
        sys.exit(f"Claim: Verification Failed\nProof: {{ Base: [insufficient_nodes: {node_count}/36], Confidence: [C5-REAL] }}")

    print(f"Claim: Verification Passed (v3.0 · {node_count} nodes)\nProof: {{ Base: [Autodidact-History-OMEGA_fully_validated], Confidence: [C5-REAL] }}")
    sys.exit(0)


if __name__ == "__main__":
    verify()
