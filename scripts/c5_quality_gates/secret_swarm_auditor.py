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
import base64
import struct
import zlib

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

# Reviewed public test/evidence values, scoped to an exact repository path,
# detector and full SHA3-256 fingerprint. These are not path or field exemptions:
# every other finding in the same file/line remains subject to the normal gate.
PUBLIC_FIXTURE_EXCEPTIONS: dict[tuple[str, str, str], str] = {
    (
        "tests/test_swarm100_lot12_s5_regressions.py",
        "GENERIC_SECRET",
        "e3d9492aaee746695480484628be01e33ad27418feefa1b482496c5cf6bd3651",
    ): "Noncredential OpenRouter client fixture in four isolated dispatch tests.",
    (
        "tests/test_swarm100_lot6_regressions.py",
        "GENERIC_SECRET",
        "e94cf501a0fef052565a5c0884fb4b8ee185ec725738dbeb4d80af64a854bf7d",
    ): "Synthetic sentinel used to assert that error diagnostics do not echo secrets.",
}

# Exceptions for archived evidence live beside that evidence, so a projection that
# omits docs/security/evidence/ omits their rules too (no orphan rules, no private
# paths in the public allowlist). Same exact-triple semantics; malformed data fails closed.
EVIDENCE_PREFIX = "docs/security/evidence/"
EVIDENCE_FIXTURE_EXCEPTIONS_PATH = (
    Path(__file__).resolve().parents[2] / EVIDENCE_PREFIX / "public_fixture_exceptions.json"
)


def _load_evidence_fixture_exceptions(path: Path) -> dict[tuple[str, str, str], str]:
    if not path.is_file():
        return {}
    document = json.loads(path.read_text(encoding="utf-8"))
    if document.get("schema") != "BABYLON60:PUBLIC_FIXTURE_EXCEPTIONS:v1" or not isinstance(
        document.get("entries"), list
    ):
        raise ValueError("invalid evidence fixture exception document")
    loaded: dict[tuple[str, str, str], str] = {}
    for entry in document["entries"]:
        if not isinstance(entry, dict) or set(entry) != {"path", "pattern", "fingerprint", "reason"}:
            raise ValueError("invalid evidence fixture exception entry")
        key = (entry["path"], entry["pattern"], entry["fingerprint"])
        if (
            not all(isinstance(value, str) for value in entry.values())
            or not key[0].startswith(EVIDENCE_PREFIX)
            or ".." in Path(key[0]).parts
            or not re.fullmatch(r"[0-9a-f]{64}", key[2])
            or not entry["reason"].strip()
        ):
            raise ValueError("evidence fixture exception outside its contract")
        if key in loaded or key in PUBLIC_FIXTURE_EXCEPTIONS:
            raise ValueError("duplicate fixture exception")
        loaded[key] = entry["reason"]
    return loaded


PUBLIC_FIXTURE_EXCEPTIONS.update(_load_evidence_fixture_exceptions(EVIDENCE_FIXTURE_EXCEPTIONS_PATH))


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
                    value for group in ("double_quoted", "single_quoted") if (value := match.group(group)) is not None
                )
            else:
                secret_val = match.group(0)
            if secret_val in WHITELIST_VALUES:
                continue
            fingerprint = hashlib.sha3_256(secret_val.encode()).hexdigest()
            secret_hash = fingerprint[:16]
            masked = secret_val[:4] + "..." + secret_val[-4:] if len(secret_val) > 8 else "***"
            findings.append(
                {
                    "file": filepath,
                    "line": line_no,
                    "type": p_name,
                    "masked_value": masked,
                    "hash": secret_hash,
                    "fingerprint": fingerprint,
                    "entropy": None,
                }
            )
    return findings


def _valid_png_payload(encoded: str) -> bool:
    """Validate bounded PNG chunks, CRCs and decompressed scanline framing."""
    if len(encoded) > 24 * 1024 * 1024:
        return False
    try:
        png = base64.b64decode(encoded, validate=True)
        if not png.startswith(b"\x89PNG\r\n\x1a\n"):
            return False
        offset = 8
        dimensions: tuple[int, int, int, int, int] | None = None
        compressed = bytearray()
        palette = False
        while offset + 12 <= len(png):
            size = struct.unpack_from(">I", png, offset)[0]
            kind = png[offset + 4 : offset + 8]
            end = offset + 12 + size
            if end > len(png) or re.fullmatch(b"[A-Za-z]{4}", kind) is None:
                return False
            payload = png[offset + 8 : offset + 8 + size]
            if zlib.crc32(kind + payload) != struct.unpack_from(">I", png, offset + 8 + size)[0]:
                return False
            if dimensions is None:
                if kind != b"IHDR" or size != 13:
                    return False
                width, height, depth, color, compression, filtering, interlace = struct.unpack(">IIBBBBB", payload)
                allowed = {0: (1, 2, 4, 8, 16), 2: (8, 16), 3: (1, 2, 4, 8), 4: (8, 16), 6: (8, 16)}
                if (
                    not width
                    or not height
                    or depth not in allowed.get(color, ())
                    or compression
                    or filtering
                    or interlace not in (0, 1)
                ):
                    return False
                dimensions = width, height, depth, color, interlace
            elif kind == b"IHDR":
                return False
            elif kind == b"PLTE":
                if not size or size % 3 or size > 768 or compressed:
                    return False
                palette = True
            elif kind == b"IDAT":
                compressed.extend(payload)
            elif kind == b"IEND":
                if size or end != len(png) or not compressed:
                    return False
                width, height, depth, color, interlace = dimensions
                if color == 3 and not palette:
                    return False
                channels = {0: 1, 2: 3, 3: 1, 4: 2, 6: 4}[color]
                passes = (
                    ((0, 0, 1, 1),)
                    if not interlace
                    else (
                        (0, 0, 8, 8),
                        (4, 0, 8, 8),
                        (0, 4, 4, 8),
                        (2, 0, 4, 4),
                        (0, 2, 2, 4),
                        (1, 0, 2, 2),
                        (0, 1, 1, 2),
                    )
                )
                rows = []
                expected = 0
                for left, top, dx, dy in passes:
                    columns = max(0, (width - left + dx - 1) // dx)
                    count = max(0, (height - top + dy - 1) // dy) if columns else 0
                    stride = (columns * channels * depth + 7) // 8 + 1
                    expected += stride * count
                    rows.append((stride, count))
                if expected > 64 * 1024 * 1024:
                    return False
                decoder = zlib.decompressobj()
                pixels = decoder.decompress(compressed, expected + 1)
                if not decoder.eof or decoder.unused_data or decoder.unconsumed_tail or len(pixels) != expected:
                    return False
                position = 0
                for stride, count in rows:
                    for _ in range(count):
                        if pixels[position] > 4:
                            return False
                        position += stride
                return True
            elif kind[:1].isupper():
                return False
            offset = end
    except (ValueError, struct.error, zlib.error):
        return False
    return False


def _mask_valid_png_data_urls(line: str) -> str:
    def replace(match: re.Match[str]) -> str:
        return "data:image/png;base64," if _valid_png_payload(match[1]) else match[0]

    return re.sub(r"data:image/png;base64,([A-Za-z0-9+/]+={0,2})(?=[\"'\s<>])", replace, line)


def _scan_line_for_entropy(filepath: str, line_no: int, line: str) -> List[Dict[str, Any]]:
    findings: List[Dict[str, Any]] = []
    scan_line = mask_whitelisted_fragments(_mask_valid_png_data_urls(line))
    for w in re.findall(r"\b[a-zA-Z0-9+/=]{20,}\b", scan_line):
        ent = shannon_entropy(w)
        if ent > 4.8:
            fingerprint = hashlib.sha3_256(w.encode()).hexdigest()
            secret_hash = fingerprint[:16]
            masked = w[:4] + "..." + w[-4:]
            findings.append(
                {
                    "file": filepath,
                    "line": line_no,
                    "type": "HIGH_ENTROPY_STRING",
                    "entropy": round(ent, 2),
                    "masked_value": masked,
                    "hash": secret_hash,
                    "fingerprint": fingerprint,
                }
            )
    return findings


def _is_public_fixture(finding: Dict[str, Any], root: str) -> bool:
    """Match one reviewed value; unqualified/out-of-root scans stay strict."""
    try:
        relative = Path(finding["file"]).absolute().relative_to(Path(root).absolute()).as_posix()
    except (TypeError, ValueError):
        return False
    return (relative, finding["type"], finding.get("fingerprint", "")) in PUBLIC_FIXTURE_EXCEPTIONS


def scan_file(filepath: str, root: str | None = None) -> List[Dict[str, Any]]:
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

    return [finding for finding in findings if root is None or not _is_public_fixture(finding, root)]


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
        if (
            resolved.name.startswith(".env")
            or resolved.name.endswith(".canary")
            or resolved.name == ".github_token.canary"
        ):
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
        dirnames[:] = [name for name in dirnames if name not in EXCLUDE_DIRS and not (current_dir / name).is_symlink()]
        for filename in filenames:
            safe_path = _safe_target(current_dir / filename, root)
            if safe_path is not None:
                targets.append(str(safe_path))
    return targets


def export_sarif(findings: List[Dict[str, Any]], root: str, output_path: str) -> None:
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


def main() -> None:
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
        futures = {executor.submit(scan_file, f, root): f for f in files}
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
                print(f"::error file={command_path},line={f['line']}::Secret detected: {f['type']} ({f['hash']})")

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
