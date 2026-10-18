#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
# Causal-Determinist: Swarm Thread Dispatcher for TOP SECRET Auditing (ULTRATHINK P0 - ITERATION 3)
# Vector: BFT_STATE_LOOP, SARIF Integration, Delta Scanning, Zero-Anergy Whitelisting
import os
import re
import math
import hashlib
import json
import argparse
from pathlib import Path
from urllib.parse import quote
from concurrent.futures import ProcessPoolExecutor, as_completed
from typing import List, Dict, Any

# Exclusión de Ineficiencia (Directorios ruidosos o binarios)
EXCLUDE_DIRS = {
    ".git",
    ".venv",
    "__pycache__",
    "node_modules",
    "dist",
    "build",
    ".cortex",
    ".babylon60",
    ".mypy_cache",
    ".pytest_cache",
    ".ruff_cache",
    "c5_remotion_video",
    "scratch",
    "anvil_yung",
    "BABYLON-60-fixes",
    "target",
    "claude_code_local_logs",
    ".lake",
    ".jj",
    ".hypothesis",
    "site",
    "assets",
    ".audit",
    "babylon60.egg-info",
    ".worktrees",
    "Babylon60.app",
    "keys",
    "L1_sink",
}
EXCLUDE_EXTS = {
    ".png",
    ".jpg",
    ".jpeg",
    ".gif",
    ".pdf",
    ".db",
    ".sqlite",
    ".sqlite3",
    ".npz",
    ".pyc",
    ".so",
    ".dylib",
    ".zip",
    ".tar",
    ".gz",
    ".db-shm",
    ".db-wal",
    ".lock",
    ".rlib",
    ".rmeta",
}

# Patrones Top Secret
PATTERNS = {
    "AWS_ACCESS_KEY": r"AKIA[0-9A-Z]{16}",
    "PRIVATE_KEY": "-----BEGIN " + r"[A-Z0-9 ]*PRIVATE KEY-----",
    "JWT_TOKEN": r"eyJ[a-zA-Z0-9_-]{5,}\.eyJ[a-zA-Z0-9_-]{5,}\.[a-zA-Z0-9_-]{5,}",
    "GITHUB_TOKEN": r"(?:gh[pousr]_[A-Za-z0-9_]{20,}|github_pat_[A-Za-z0-9_]{20,})",
    "GOOGLE_API": r"AIza[0-9A-Za-z-_]{35}",
    "SLACK_TOKEN": r"xox[baprs]-[0-9]{12}-[0-9]{12}-[a-zA-Z0-9]{24}",
    "OPENAI_API_KEY": r"\bsk-(?:proj-)?[A-Za-z0-9_-]{20,}\b",
    "GENERIC_SECRET": (
        r"""(?i)\b(?:password|secret|api[_-]?key|access[_-]?token)\b\s*[:=]\s*(?:"(?P<double_quoted>[^"\r\n]{8,})"|'(?P<single_quoted>[^'\r\n]{8,})')"""
    ),
}

# Whitelist de Ineficiencia para Cadenas de Alta Entropía
WHITELIST_ENTROPY = [
    r"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwx",
    r"0123456789abcdefghijklmnopqrstuvwxyz",
    r"ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz",
    r"docs\.google\.com/[^\s]+",
    r"0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuv",
    r"0123456789abcdefghijkmnopqrstuvwxyzABCDEFGHIJKLMNPQRSTUVWXYZ",  # BASE60_ALPHABET (constante pública de diseño, utils/base60.py)
    r"\b[0-9a-fA-F]{40}\b",  # INV_C5_OPSEC_CALIBRATION: Ignorar hashes de commit SHA-1 de Git
    # Public fixtures are allowlisted exactly; broad signature-shaped patterns can hide tokens.
    r"BFiNkvkYQzaiIEyxHfmFi1I9kEP9JruokwtDpviRhSqffUdTyCPrLeIjyu5zjGNH28sRzI1vPgOzfDxd\+Z0H5RY=",  # Public key uncompressed point fixture
    r"\bME[UY]CI[a-zA-Z0-9+/=]{70,}\b",  # NIST P-256 DER signatures in Base64 (telemetría / atestación)
]

# Valores literales conocidos como NO-secretos (ejemplos oficiales de documentación
# o dummies de test auto-descritos). Causal-Determinist: cada entrada justificada inline.
WHITELIST_VALUES = {
    "AKIAIOSFODNN7EXAMPLE",  # Clave de ejemplo oficial de la documentación de AWS (no es real)
    "dummy_key_for_stress",  # Dummy auto-descrito: stress test (extensions/llm/fable_stress_test.py)
    "dummy_key_for_steerability",  # Dummy auto-descrito: PoC steerability (extensions/llm/fable_steerability_poc.py)
    "tu_clave_moonshot",  # Placeholder setup_nacho_cortex.sh / setup_nacho_cortex.ps1
    "tu_clave_secreta_super_segura",  # Placeholder docs/INBOUND_EMAIL_SETUP.md
    "test_secret_key_12345",  # Dummy test fixture tests/test_inbound_email.py
    "babylon-sovereign-airgapped",  # Dummy client example crates/eridu-infer/src/hud.rs
    "secret_key_1234567890_do_not_leak",  # Dummy test fixture tests/test_compliance_exporter.py
}


def shannon_entropy(data: str) -> float:
    if not data:
        return 0.0
    entropy = 0.0
    for x in set(data):
        p_x = float(data.count(x)) / len(data)
        if p_x > 0:
            entropy += -p_x * math.log2(p_x)
    return entropy


def mask_whitelisted_fragments(line: str) -> str:
    """Mask only known public fixtures before checking the rest of the line."""
    for w in WHITELIST_ENTROPY:
        line = re.sub(w, " ", line)
    return line


def _scan_line_for_patterns(filepath: str, line_no: int, line: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    for p_name, p_regex in PATTERNS.items():
        for match in re.finditer(p_regex, line):
            if p_name == "GENERIC_SECRET":
                secret_val = next(
                    value
                    for group in ("double_quoted", "single_quoted")
                    if (value := match.group(group)) is not None
                )
            else:
                secret_val = match.group(0)
            if secret_val in WHITELIST_VALUES:
                continue
            secret_hash = hashlib.sha3_256(secret_val.encode()).hexdigest()[:16]
            masked = secret_val[:4] + "..." + secret_val[-4:] if len(secret_val) > 8 else "***"
            findings.append(
                {
                    "file": filepath,
                    "line": line_no,
                    "type": p_name,
                    "masked_value": masked,
                    "hash": secret_hash,
                    "entropy": None,
                }
            )
    return findings


def _scan_line_for_entropy(filepath: str, line_no: int, line: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    scan_line = mask_whitelisted_fragments(line)
    for w in re.findall(r"\b[a-zA-Z0-9+/=]{20,}\b", scan_line):
        ent = shannon_entropy(w)
        if ent > 4.8:
            secret_hash = hashlib.sha3_256(w.encode()).hexdigest()[:16]
            masked = w[:4] + "..." + w[-4:]
            findings.append(
                {
                    "file": filepath,
                    "line": line_no,
                    "type": "HIGH_ENTROPY_STRING",
                    "entropy": round(ent, 2),
                    "masked_value": masked,
                    "hash": secret_hash,
                }
            )
    return findings


def scan_file(filepath: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    if not os.path.isfile(filepath) or os.path.islink(filepath):
        return findings
    if filepath.endswith("test_compliance_exporter.py") or filepath.endswith("secret_swarm_auditor.py"):
        return findings

    try:
        with open(filepath, "rb") as bf:
            chunk = bf.read(8192)
            if b"\x00" in chunk:
                return findings
        with open(filepath, "r", encoding="utf-8", errors="ignore") as f:
            for line_no, line in enumerate(f, start=1):
                findings.extend(_scan_line_for_patterns(filepath, line_no, line))
                findings.extend(_scan_line_for_entropy(filepath, line_no, line))
    except (UnicodeDecodeError, OSError):
        pass

    return findings


def _safe_target(path: Path, root: Path) -> Path | None:
    try:
        relative = path.relative_to(root) if path.is_absolute() else path
        candidate = root / relative
        resolved = candidate.resolve(strict=True)
        resolved.relative_to(root)
        if not resolved.is_file():
            return None

        current = root
        for part in relative.parts:
            current = current / part
            if current.is_symlink():
                return None

        if resolved.suffix.lower() in EXCLUDE_EXTS:
            return None
        if resolved.name in {"package-lock.json", "uv.lock", "Cargo.lock"}:
            return None
        if resolved.name.startswith(".env") or resolved.name.endswith(".canary") or resolved.name == ".github_token.canary":
            return None
        return resolved
    except (OSError, RuntimeError, ValueError):
        return None


def get_target_files(root_dir: str, explicit_files: List[str] | None = None) -> List[str]:
    root = Path(root_dir).resolve()
    targets = []
    if explicit_files is not None:
        for filename in explicit_files:
            candidate = Path(filename)
            safe_path = _safe_target(candidate, root)
            if safe_path is not None:
                targets.append(str(safe_path))
        return targets

    for dirpath, dirnames, filenames in os.walk(root, followlinks=False):
        current_dir = Path(dirpath)
        dirnames[:] = [
            name
            for name in dirnames
            if name not in EXCLUDE_DIRS and not (current_dir / name).is_symlink()
        ]
        for filename in filenames:
            safe_path = _safe_target(current_dir / filename, root)
            if safe_path is not None:
                targets.append(str(safe_path))
    return targets


def export_sarif(findings: List[Dict[str, Any]], root: str, output_path: str):
    sarif: Dict[str, Any] = {
        "$schema": "https://raw.githubusercontent.com/oasis-tcs/sarif-spec/master/Schemata/sarif-schema-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {
                "tool": {
                    "driver": {
                        "name": "C5 Secret Pattern Auditor",
                        "informationUri": "https://github.com/borjamoskv",
                        "rules": [
                            {
                                "id": "SECRET-01",
                                "name": "HardcodedSecret",
                                "shortDescription": {"text": "Hardcoded top secret string detected."},
                                "helpUri": "https://github.com/borjamoskv",
                            }
                        ],
                    }
                },
                "results": [],
            }
        ],
    }

    for f in findings:
        rel_path = Path(f["file"]).resolve().relative_to(Path(root).resolve()).as_posix()
        msg = f"Detectado secreto tipo {f['type']} con hash {f['hash']}"
        sarif["runs"][0]["results"].append(
            {
                "ruleId": "SECRET-01",
                "message": {"text": msg},
                "locations": [
                    {
                        "physicalLocation": {
                            "artifactLocation": {"uri": quote(rel_path, safe="/-._~")},
                            "region": {"startLine": f["line"], "startColumn": 1},
                        }
                    }
                ],
            }
        )

    with open(output_path, "w", encoding="utf-8") as out_file:
        json.dump(sarif, out_file, indent=2)


def main():
    parser = argparse.ArgumentParser(description="C5 secret pattern auditor")
    parser.add_argument("--files", nargs="*", help="Delta mode: specific files to scan")
    parser.add_argument("--root", default=os.getcwd(), help="Root directory containing files to scan")
    parser.add_argument("--sarif", action="store_true", help="Generate SARIF report")
    parser.add_argument("--sarif-output", help="SARIF output path (defaults to <root>/secret_audit.sarif)")
    args = parser.parse_args()

    root = str(Path(args.root).resolve())
    files = get_target_files(root, explicit_files=args.files)

    print(f"[*] Secret pattern scan: {len(files)} files selected.")

    all_findings = []
    with ProcessPoolExecutor() as executor:
        futures = {executor.submit(scan_file, f): f for f in files}
        for future in as_completed(futures):
            res = future.result()
            if res:
                all_findings.extend(res)

    # CI PR Annotations
    in_ci = os.environ.get("GITHUB_ACTIONS") == "true"
    if all_findings:
        for f in all_findings:
            rel_path = Path(f["file"]).resolve().relative_to(Path(root)).as_posix()
            if in_ci:
                command_path = (
                    rel_path.replace("%", "%25")
                    .replace("\r", "%0D")
                    .replace("\n", "%0A")
                    .replace(":", "%3A")
                    .replace(",", "%2C")
                )
                print(
                    f"::error file={command_path},line={f['line']}::Secret detected: {f['type']} ({f['hash']})"
                )

    # SARIF Output
    if args.sarif:
        output_path = Path(args.sarif_output or (Path(root) / "secret_audit.sarif"))
        if output_path.is_symlink():
            raise SystemExit("Refusing to write SARIF through a symbolic link.")
        export_sarif(all_findings, root, str(output_path))
        print(f"[*] SARIF report written: {output_path}")

    if all_findings:
        print("[!] Secret-like values detected.")
        raise SystemExit(1)
    else:
        print("[*] Scan completed: no configured secret patterns matched.")
        raise SystemExit(0)


if __name__ == "__main__":
    main()
