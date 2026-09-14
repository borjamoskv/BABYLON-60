#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import os
import sys
from pathlib import Path

# Bootstrap sys.path para resolución determinista de babylon60 (Invariante Clone & Run)
_repo_root = Path(__file__).resolve().parent.parent.parent
_orchestrator = _repo_root / "01_ORCHESTRATOR"
if str(_orchestrator) not in sys.path:
    sys.path.insert(0, str(_orchestrator))

import datetime
import hashlib
import json
import re
import signal
from babylon60.database.core import connect_sync
from typing import Any

EXERGY_LEVEL: str = "1000/1000"
BFT_MIN_CONSENSUS: int = 3
TARGET_PATTERNS: dict[str, re.Pattern[str]] = {
    "PLAINTEXT_CREDIT_CARD": re.compile(
        "\\b(?:4[0-9]{12}(?:[0-9]{3})?|5[1-5][0-9]{14}|3[47][0-9]{13}|3(?:0[0-5]|[68][0-9])[0-9]{11}|6(?:011|5[0-9]{2})[0-9]{12}|(?:2131|1800|35\\d{3})\\d{11})\\b"
    ),
    "PRIVATE_KEY_HEADER": re.compile("-----BEGIN (?:RSA|OPENSSH|EC|DSA|PGP)?\\s*PRIVATE KEY-----"),
    "UNENCRYPTED_IRC_PORT": re.compile(":(?:6667|6668|6669)\\b"),
    "PLAIN_HTTP_C2": re.compile(r"http://(?!127\.0\.0\.1|0\.0\.0\.0|localhost)[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3}"),
    "SQLI_ERROR_SIGNATURE": re.compile(
        "(?:You have an error in your SQL syntax|Warning: mysql_connect|SQLSTATE\\[\\d+\\]|Unclosed quotation mark after the character string)",
        re.IGNORECASE,
    ),
    "AWS_ACCESS_KEY": re.compile(r"(?<![A-Z0-9])(AKIA|ASIA|ABIA|ACCA)[A-Z0-9]{16}(?![A-Z0-9])"),
    "AWS_SECRET_KEY": re.compile(r"(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])"),
    "CANARY_WEBHOOK": re.compile(r"canarytokens\.com|webhook\.site"),
}


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
                elif v_type == "AWS_SECRET_KEY":
                    non_sha = [m for m in matches if not re.match(r"^[0-9a-fA-F]{40}$", m)]
                    if not non_sha:
                        continue
                elif v_type == "AWS_ACCESS_KEY":
                    non_dummy = [m for m in matches if m != "AKIAIOSFODNN7EXAMPLE"]
                    if not non_dummy:
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
        ignore_dirs: set[str] = {
            ".git", ".venv", "node_modules", "scratch", "__pycache__",
            "target", ".lake", ".cortex", ".babylon60", ".mypy_cache",
            ".pytest_cache", ".ruff_cache", "c5_remotion_video", "dist", "build",
            ".jj", ".hypothesis", "site", "assets", ".audit", "babylon60.egg-info"
        }
        with connect_sync(self.db_path) as conn:
            for root, dirs, files in os.walk(self.workspace):
                dirs[:] = [d for d in dirs if d not in ignore_dirs and not d.endswith(".egg-info")]
                for file in files:
                    fpath = Path(root) / file
                    if fpath.name in (
                        "opsec_sentinel_c5.py", "fake_aws_credentials", "CANARY_TOKENS.md",
                        "gitleaks.yml", "secret_swarm_auditor.py", "runner.py", "test_compliance_exporter.py",
                        ".gitleaks.toml", ".env.canary"
                    ) or fpath.stat().st_size > 2 * 1024 * 1024:
                        continue
                    if fpath.suffix in (".pyc", ".db", ".png", ".jpg", ".pdf", ".mp4", ".lock", ".wav", ".mp3", ".ogg", ".map", ".sarif"):
                        continue
                    file_violations = self.audit_file(fpath)
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
