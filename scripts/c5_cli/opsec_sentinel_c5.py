#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import datetime
import hashlib
import ipaddress
import json
import os
import re
import signal
from babylon60.database.core import connect_sync
import sys
from pathlib import Path
from typing import Any

EXERGY_LEVEL: str = "1000/1000"
BFT_MIN_CONSENSUS: int = 3
TARGET_PATTERNS: dict[str, re.Pattern[str]] = {
    "PLAINTEXT_CREDIT_CARD": re.compile(
        "\\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\\d{3})\\d{11})\\b"
    ),
    "PRIVATE_KEY_HEADER": re.compile("-----BEGIN (?:RSA|OPENSSH|EC|DSA|PGP)?\\s*PRIVATE KEY-----"),
    "UNENCRYPTED_IRC_PORT": re.compile(":(?:6667|6668|6669)\\b"),
    "PLAIN_HTTP_C2": re.compile("http://[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}\\.[0-9]{1,3}"),
    "SQLI_ERROR_SIGNATURE": re.compile(
        "(?:You have an error in your SQL syntax|Warning: mysql_connect|SQLSTATE\\[\\d+\\]|Unclosed quotation mark after the character string)",
        re.IGNORECASE,
    ),
    "AWS_ACCESS_KEY": re.compile(r"(?<![A-Z0-9])[A-Z0-9]{20}(?![A-Z0-9])"), # A simplistic AWS key pattern (often starts with AKIA, ASIA, etc)
    "AWS_SECRET_KEY": re.compile(r"(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])"),
    "CANARY_WEBHOOK": re.compile(r"canarytokens\.com|webhook\.site"),
}

# Allowlist C5 (auditoría 2026-08): SOLO falsos positivos verificados por forma
# (SHA git, txid, hash pineado de Action, fixture dummy, constante, fingerprint),
# NUNCA por valor del secreto. Formato: (prefijo_de_ruta_relativa, regla | "*").
# Precedente jul-2026: fixtures dummy (fake_aws_credentials, CANARY_TOKENS.md).
PATH_RULE_ALLOWLIST: tuple[tuple[str, str], ...] = (
    (".git-blame-ignore-revs", "*"),                        # SHAs de commits git (40-hex)
    (".gitleaks.toml", "*"),                                # definiciones de patrones del escáner
    ("babylon60.egg-info/", "*"),                           # artefacto generado por pip install -e .
    ("tools/audit/snapshots/", "*"),                        # commit_sha en manifiestos de auditoría
    ("data/L1_sink/", "*"),                                 # txids Bitcoin (hex) en OP_RETURN
    ("docs/", "*"),                                         # hashes/ejemplos citados en prosa
    ("experiments/anvil_yung/lib/", "*"),                   # forge-std vendored (Foundry)
    ("experiments/1_Operaciones_Activas/verifiable_inference_suite/run_verifiable_suite.py", "AWS_SECRET_KEY"),  # banners repetitivos (uniq=1)
    ("tests/", "*"),                                        # fixtures dummy y endpoints loopback de test
    ("apps/", "PLAIN_HTTP_C2"),                             # defensa en profundidad (la regla ya ignora loopback/RFC1918)
    ("crates/strike-rs/src/bin/c5_cli.rs", "PLAIN_HTTP_C2"),
    ("packages/babylon60/extensions/", "PLAIN_HTTP_C2"),
    (".github/workflows/", "AWS_SECRET_KEY"),               # SHAs de Actions pineadas (pinning = buena práctica)
    ("scripts/runner.py", "CANARY_WEBHOOK"),                # canary intencional (tripwire documentado)
    ("scripts/c5_cli/babylon_mail_cli.py", "AWS_SECRET_KEY"),    # fingerprint ed25519 (hash, no clave)
    ("scripts/c5_demos/", "*"),                             # fixtures demo 'leaked_*' dummy
    ("scripts/c5_quality_gates/secret_swarm_auditor.py", "*"),   # patrones del propio detector
    ("scripts/c5_quality_gates/audit_100_agents.py", "AWS_SECRET_KEY"),  # constante en docstring
)


def _is_allowlisted(rel_path: str, rule: str) -> bool:
    rel: str = rel_path.replace(os.sep, "/")
    return any(
        (scope == "*" or scope == rule)
        and (rel == prefix.rstrip("/") or rel.startswith(prefix))
        for prefix, scope in PATH_RULE_ALLOWLIST
    )


def _is_local_http_endpoint(url_match: str) -> bool:
    """http://127.0.0.1 / RFC1918 son sockets locales de desarrollo, nunca C2 plaintext."""
    try:
        ip = ipaddress.ip_address(url_match.rsplit("//", 1)[-1])
    except ValueError:
        return False
    return ip.is_loopback or ip.is_private or ip.is_link_local


class OpsecSentinelC5:
    def __init__(self, workspace_path: str, db_path: str = "/tmp/opsec_sentinel_c5.db") -> None:
        self.workspace: Path = Path(workspace_path).resolve()
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with connect_sync(self.db_path) as conn:
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS opsec_audit_log (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    file_path TEXT NOT NULL,
                    violation_type TEXT NOT NULL,
                    snippet_hash TEXT NOT NULL,
                    severity TEXT NOT NULL,
                    timestamp TEXT NOT NULL
                );
                """
            )

    def audit_file(self, filepath: Path) -> list[dict[str, str]]:
        violations: list[dict[str, str]] = []
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            os.kill(os.getpid(), signal.SIGKILL)
            raise RuntimeError("FAIL-FAST: General Exception intercepted.")
        for v_type, pattern in TARGET_PATTERNS.items():
            matches: list[Any] = pattern.findall(content)
            if matches:
                if v_type == "PLAINTEXT_CREDIT_CARD":
                    valid_cards = [m for m in matches if self._luhn_check(m)]
                    if not valid_cards:
                        continue
                if v_type == "PLAIN_HTTP_C2":
                    matches = [m for m in matches if not _is_local_http_endpoint(m)]
                    if not matches:
                        continue
                hash_sig = hashlib.sha3_256(content[:1000].encode("utf-8")).hexdigest()[:16]
                severity = "CRITICAL_P0" if v_type in ("PLAINTEXT_CREDIT_CARD", "PRIVATE_KEY_HEADER") else "CRITICAL_P1"
                violations.append(
                    {
                        "file_path": str(filepath.relative_to(self.workspace)),
                        "violation_type": v_type,
                        "snippet_hash": hash_sig,
                        "severity": severity,
                        "timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
                    }
                )
        return violations

    @staticmethod
    def _luhn_check(card_number: str) -> bool:
        digits = [int(d) for d in card_number if d.isdigit()]
        if not digits or len(digits) < 13:
            return False
        checksum = 0
        reverse_digits = digits[::-1]
        for i, d in enumerate(reverse_digits):
            if i % 2 == 1:
                d *= 2
                if d > 9:
                    d -= 9
            checksum += d
        return checksum % 10 == 0

    def run_full_scan(self) -> dict[str, Any]:
        details: list[dict[str, str]] = []
        violations_found: int = 0
        ignore_dirs: set[str] = {".git", ".venv", "node_modules", "scratch", "__pycache__"}
        with connect_sync(self.db_path) as conn:
            for root, dirs, files in os.walk(self.workspace):
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                for file in files:
                    fpath = Path(root) / file
                    if fpath.name in ("opsec_sentinel_c5.py", "fake_aws_credentials", "CANARY_TOKENS.md", "gitleaks.yml") or fpath.stat().st_size > 2 * 1024 * 1024:
                        continue
                    if fpath.suffix in (".pyc", ".db", ".png", ".jpg", ".pdf", ".mp4", ".lock"):
                        continue
                    file_violations = self.audit_file(fpath)
                    rel_path: str = str(fpath.relative_to(self.workspace))
                    file_violations = [
                        v for v in file_violations
                        if not _is_allowlisted(rel_path, v["violation_type"])
                    ]
                    for v in file_violations:
                        conn.execute(
                            "\n                            INSERT INTO opsec_audit_log (file_path, violation_type, snippet_hash, severity, timestamp)\n                            VALUES (?, ?, ?, ?, ?)\n                        ",
                            (v["file_path"], v["violation_type"], v["snippet_hash"], v["severity"], v["timestamp"]),
                        )
                        details.append(v)
                        violations_found += 1
            conn.commit()
        report: dict[str, Any] = {
            "sys_id": "borjamoskv",
            "exergy": EXERGY_LEVEL,
            "scan_timestamp": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "target_workspace": str(self.workspace),
            "violations_found": violations_found,
            "details": details,
        }
        return report


def main() -> None:
    workspace = sys.argv[1] if len(sys.argv) > 1 else os.getcwd()
    sentinel = OpsecSentinelC5(workspace)
    report = sentinel.run_full_scan()
    print(json.dumps(report, indent=2))
    if report["violations_found"] > 0:
        print(f"\n[CRITICAL ALERT] {report['violations_found']} OPSEC/C2/Plaintext violations detected!")
        sys.exit(1)
    else:
        print("\n[SUCCESS] Causal-Determinist OPSEC Audit Clean. Zero plaintext secrets or unverified relays detected.")
        sys.exit(0)


if __name__ == "__main__":
    main()
