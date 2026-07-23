import babylon60.database.core
import datetime
import hashlib
import json
import os
import re
import signal
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
}


class OpsecSentinelC5:
    def __init__(self, workspace_path: str, db_path: str = "/tmp/opsec_sentinel_c5.db") -> None:
        self.workspace: Path = Path(workspace_path).resolve()
        self.db_path = db_path
        self._init_db()

    def _init_db(self) -> None:
        with babylon60.database.core.connect(self.db_path, timeout=5.0) as conn:
            conn.execute("PRAGMA journal_mode=WAL;")
            conn.execute("PRAGMA busy_timeout=5000;")
            conn.execute(
                "\n                CREATE TABLE IF NOT EXISTS opsec_audit_log (\n                    id INTEGER PRIMARY KEY AUTOINCREMENT,\n                    file_path TEXT NOT NULL,\n                    violation_type TEXT NOT NULL,\n                    snippet_hash TEXT NOT NULL,\n                    severity TEXT NOT NULL,\n                    timestamp TEXT NOT NULL\n                );\n            "
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
                if v_type == "PLAIN_HTTP_C2":
                    non_local = [m for m in matches if not (m.startswith("http://127.") or m.startswith("http://0.0.0.0") or m.startswith("http://10.") or m.startswith("http://192.168."))]
                    if not non_local:
                        continue
                if v_type == "PLAINTEXT_CREDIT_CARD":
                    valid_cards = [m for m in matches if self._luhn_check(m)]
                    if not valid_cards:
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
        ignore_dirs: set[str] = {".git", ".venv", "node_modules", "scratch", "__pycache__", "target", "build", "dist", ".mypy_cache", "cortex_persist.egg-info"}
        with babylon60.database.core.connect(self.db_path, timeout=5.0) as conn:
            for root, dirs, files in os.walk(self.workspace):
                dirs[:] = [d for d in dirs if d not in ignore_dirs]
                for file in files:
                    fpath = Path(root) / file
                    if fpath.name in ("opsec_sentinel_c5.py", "secret_swarm_auditor.py") or fpath.stat().st_size > 2 * 1024 * 1024:
                        continue
                    if fpath.suffix in (".pyc", ".db", ".png", ".jpg", ".pdf", ".mp4", ".lock", ".rmeta", ".rlib", ".bin", ".dylib", ".so"):
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
        print("\n[SUCCESS] C5-REAL OPSEC Audit Clean. Zero plaintext secrets or unverified relays detected.")
        sys.exit(0)


if __name__ == "__main__":
    main()
