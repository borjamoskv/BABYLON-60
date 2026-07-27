"""
VENOM — Rust Static Scanner

cargo-audit integration + VENOM regex patterns for Rust/Soroban/Anchor.
"""
import re
import subprocess
import json
from pathlib import Path

from cortex_bounty.venom.patterns import RUST_PATTERNS
from cortex_bounty.venom.solidity_scanner import Finding


class RustScanner:
    def __init__(self):
        self.findings: list[Finding] = []
        self.cargo_audit_available = self._check_cargo_audit()

    @staticmethod
    def _check_cargo_audit() -> bool:
        try:
            r = subprocess.run(["cargo", "audit", "--version"], capture_output=True, timeout=10)
            return r.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def scan_directory(self, target_dir: str) -> list[Finding]:
        self.findings = []
        target_path = Path(target_dir)
        if not target_path.exists():
            raise FileNotFoundError(f"Not found: {target_dir}")

        rs_files = list(target_path.rglob("*.rs"))
        if not rs_files:
            return []

        # cargo audit for known CVEs
        if self.cargo_audit_available and (target_path / "Cargo.toml").exists():
            self.findings.extend(self._run_cargo_audit(target_dir))

        for rs_file in rs_files:
            rel = str(rs_file.relative_to(target_path))
            if any(s in rel.lower() for s in ["test", "target/", "examples/"]):
                continue
            self.findings.extend(self._scan_file(rs_file))

        seen = set()
        unique = []
        for f in self.findings:
            key = (f.file, f.line, f.pattern_id)
            if key not in seen:
                seen.add(key)
                unique.append(f)
        self.findings = unique
        sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        self.findings.sort(key=lambda x: sev_order.get(x.severity, 5))
        return self.findings

    def _run_cargo_audit(self, target_dir: str) -> list[Finding]:
        findings = []
        try:
            result = subprocess.run(
                ["cargo", "audit", "--json"],
                capture_output=True, text=True, timeout=120, cwd=target_dir,
            )
            if result.stdout:
                data = json.loads(result.stdout)
                vulns = data.get("vulnerabilities", {}).get("list", [])
                for v in vulns:
                    advisory = v.get("advisory", {})
                    findings.append(Finding(
                        id=f"CVE-{advisory.get('id', '?')}",
                        pattern_id=advisory.get("id", ""),
                        file="Cargo.toml",
                        severity="high",
                        name=advisory.get("title", ""),
                        description=advisory.get("description", "")[:300],
                        source="cargo-audit",
                    ))
        except (subprocess.TimeoutExpired, json.JSONDecodeError, FileNotFoundError):
            pass
        return findings

    def _scan_file(self, filepath: Path) -> list[Finding]:
        findings = []
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return findings

        for pat in RUST_PATTERNS:
            try:
                regex = re.compile(pat["pattern"], re.MULTILINE | re.DOTALL)
            except re.error:
                continue
            for match in regex.finditer(content):
                line_num = content[:match.start()].count("\n") + 1
                mt = match.group(0)[:200]
                findings.append(Finding(
                    id=f"VENOM-{pat['id']}", pattern_id=pat["id"],
                    file=str(filepath), line=line_num, severity=pat["severity"],
                    name=pat["name"], description=pat["description"],
                    recommendation=pat.get("recommendation", ""),
                    matched_text=mt.strip(), source="venom",
                ))
        return findings

    def summary(self) -> dict:
        by_sev = {}
        for f in self.findings:
            by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
        return {
            "total": len(self.findings),
            "critical": by_sev.get("critical", 0),
            "high": by_sev.get("high", 0),
            "medium": by_sev.get("medium", 0),
            "cargo_audit_used": self.cargo_audit_available,
        }
