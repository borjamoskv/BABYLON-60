#!/usr/bin/env python3
"""
C5-REAL Laboratory Validator
Audits experiment directories for content density.
Rejects placeholder stubs and measures exergy ratio.
"""

import math
import sys
from collections import Counter
from pathlib import Path


PLACEHOLDER_MARKERS: list[str] = [
    "[INJECT",
    "[TODO",
    "[PENDING",
    "[PLACEHOLDER",
    "pass\n",
    "exit 0\n",
]

REQUIRED_FILES: list[str] = [
    "01_experimento.yml",
    "02_hallazgo.md",
    "03_codigo.py",
    "04_demo.sh",
    "05_track.md",
    "06_reflexion.md",
    "manifest.json",
]


def shannon_entropy(text: str) -> float:
    """Calculate Shannon entropy in bits/char."""
    if not text:
        return 0.0
    freq = Counter(text)
    length = len(text)
    entropy = 0.0
    for count in freq.values():
        p = count / length
        if p > 0:
            entropy -= p * math.log2(p)
    return entropy


def validate_experiment(lab_dir: Path) -> dict[str, object]:
    """Validate a single experiment directory. Returns audit report."""
    report: dict[str, object] = {
        "experiment": lab_dir.name,
        "path": str(lab_dir),
        "valid": True,
        "files": {},
        "violations": [],
        "total_bytes": 0,
        "exergy_ratio": 0.0,
    }

    # Check required files
    for req in REQUIRED_FILES:
        fpath = lab_dir / req
        if not fpath.exists():
            report["valid"] = False
            violations = report["violations"]
            assert isinstance(violations, list)
            violations.append(f"MISSING: {req}")

    # Audit each file
    total_bytes = 0
    placeholder_bytes = 0
    file_reports: dict[str, dict[str, object]] = {}

    for fpath in sorted(lab_dir.iterdir()):
        if fpath.name == "manifest.json":
            continue
        if not fpath.is_file():
            continue

        try:
            content = fpath.read_text(encoding="utf-8")
        except OSError:
            continue

        fbytes = len(content.encode("utf-8"))
        total_bytes += fbytes
        entropy = shannon_entropy(content)

        has_placeholder = any(marker in content for marker in PLACEHOLDER_MARKERS)
        if has_placeholder:
            placeholder_bytes += fbytes
            report["valid"] = False
            violations = report["violations"]
            assert isinstance(violations, list)
            violations.append(f"PLACEHOLDER_DETECTED: {fpath.name}")

        file_reports[fpath.name] = {
            "bytes": fbytes,
            "entropy_bits_per_char": round(entropy, 3),
            "has_placeholder": has_placeholder,
            "lines": content.count("\n"),
        }

    report["files"] = file_reports
    report["total_bytes"] = total_bytes

    if total_bytes > 0:
        exergy = (total_bytes - placeholder_bytes) / total_bytes
        report["exergy_ratio"] = round(exergy, 4)
    else:
        report["exergy_ratio"] = 0.0

    return report


def main() -> None:
    if len(sys.argv) < 2:
        # Validate all experiments
        root = Path(".")
        lab_root = root / "cortex" / "laboratory"
    else:
        lab_root = Path(sys.argv[1])

    if not lab_root.is_dir():
        print(f"[FATAL] Laboratory directory not found: {lab_root}", file=sys.stderr)
        sys.exit(1)

    experiments = [d for d in sorted(lab_root.iterdir()) if d.is_dir()]
    if not experiments:
        print(f"[WARN] No experiments found in {lab_root}")
        sys.exit(0)

    all_valid = True
    for exp_dir in experiments:
        report = validate_experiment(exp_dir)
        status = "PASS" if report["valid"] else "FAIL"
        if not report["valid"]:
            all_valid = False

        print(f"\n{'=' * 60}")
        print(f"[{status}] {report['experiment']}")
        print(f"  Path: {report['path']}")
        print(f"  Total Bytes: {report['total_bytes']}")
        print(f"  Exergy Ratio: {report['exergy_ratio']}")

        violations = report["violations"]
        assert isinstance(violations, list)
        if violations:
            print("  Violations:")
            for v in violations:
                print(f"    - {v}")

        files = report["files"]
        assert isinstance(files, dict)
        for fname, fdata in files.items():
            assert isinstance(fdata, dict)
            print(
                f"  {fname}: {fdata['bytes']}B | H={fdata['entropy_bits_per_char']} bits/char | lines={fdata['lines']}"
            )

    if not all_valid:
        print("\n[SIGKILL] One or more experiments contain placeholder stubs.")
        sys.exit(1)
    else:
        print("\n[C5-REAL] All experiments validated. Exergy confirmed.")
        sys.exit(0)


if __name__ == "__main__":
    main()
