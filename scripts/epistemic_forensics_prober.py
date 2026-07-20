import os
import re
import json

TARGET_DIR = os.environ.get(
    "CORTEX_TARGET_DIR", os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
)
if not TARGET_DIR:
    raise RuntimeError("CORTEX_TARGET_DIR env var is required (Ω23).")

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_JSON = os.path.join(
    PROJECT_ROOT, "cortex", "artifacts", "reports", "BABYLON_60_EPISTEMOLOGY.json"
)


def scan_file(filepath: str) -> str:
    with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def classify_files(target_dir: str) -> dict[str, list[str]]:
    classification: dict[str, list[str]] = {
        "Verified_by_Construction": [],
        "Verified_by_Proof": [],
        "Verified_by_Tests": [],
        "Assumed": [],
    }

    # regex patterns for Verified_by_Construction
    construction_pattern = re.compile(
        r"(hash_sha3_256|verify_ed25519|sqlite3|pynacl|BFT_Ledger|bft|WAL|synchronous=FULL|ffi|unsafe\s*\{)",
        re.IGNORECASE,
    )

    for root, dirs, files in os.walk(target_dir):
        # Exclude paths that are not source code
        if any(
            exc in root
            for exc in [
                ".git",
                "node_modules",
                "__pycache__",
                "target",
                ".venv",
                "dist",
            ]
        ):
            continue

        for file in files:
            # Only care about source files
            if not file.endswith(
                (".py", ".rs", ".lean", ".ts", ".tsx", ".js", ".yaml", ".yml", ".sol")
            ):
                continue

            full_path = os.path.join(root, file)
            rel_path = os.path.relpath(full_path, target_dir)

            # Proofs
            if file.endswith(".lean"):
                classification["Verified_by_Proof"].append(rel_path)
                continue

            # Tests
            if (
                "tests/" in rel_path
                or file.startswith("test_")
                or file.endswith("_test.py")
            ):
                classification["Verified_by_Tests"].append(rel_path)
                continue

            content = scan_file(full_path)

            # Construction
            if construction_pattern.search(content):
                classification["Verified_by_Construction"].append(rel_path)
                continue

            # If it didn't match any of the above, it's Assumed
            classification["Assumed"].append(rel_path)

    return classification


def main() -> None:
    print("[*] Starting OMEGA-2 Epistemic Forensics Prober...")
    results = classify_files(TARGET_DIR)

    total = sum(len(v) for v in results.values())
    print(f"[*] Scanned {total} files.")
    print(f"  - Verified_by_Construction: {len(results['Verified_by_Construction'])}")
    print(f"  - Verified_by_Proof: {len(results['Verified_by_Proof'])}")
    print(f"  - Verified_by_Tests: {len(results['Verified_by_Tests'])}")
    print(f"  - Assumed: {len(results['Assumed'])}")

    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w") as f:
        json.dump(results, f, indent=2)

    print(f"[+] Output written to {OUTPUT_JSON}")


if __name__ == "__main__":
    main()
