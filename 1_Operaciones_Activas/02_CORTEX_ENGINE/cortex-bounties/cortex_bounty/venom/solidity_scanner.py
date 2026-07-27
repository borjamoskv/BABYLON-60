"""
VENOM — Solidity Static Scanner

Slither integration + VENOM regex patterns for Solidity vulnerability detection.
"""
import json
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path

from cortex_bounty.venom.patterns import SOLIDITY_PATTERNS


@dataclass
class Finding:
    id: str = ""
    pattern_id: str = ""
    file: str = ""
    line: int = 0
    severity: str = ""
    name: str = ""
    description: str = ""
    recommendation: str = ""
    matched_text: str = ""
    source: str = ""


class SolidityScanner:
    def __init__(self):
        self.findings: list[Finding] = []
        self.slither_available = self._check_slither()

    @staticmethod
    def _check_slither() -> bool:
        try:
            r = subprocess.run(["slither", "--version"], capture_output=True, timeout=10)
            return r.returncode == 0
        except (FileNotFoundError, subprocess.TimeoutExpired):
            return False

    def scan_directory(self, target_dir: str, use_slither: bool = True) -> list[Finding]:
        self.findings = []
        target_path = Path(target_dir)
        if not target_path.exists():
            raise FileNotFoundError(f"Not found: {target_dir}")

        sol_files = list(target_path.rglob("*.sol"))
        if not sol_files:
            return []

        if use_slither and self.slither_available:
            self.findings.extend(self._run_slither(target_dir))

        for sf in sol_files:
            rel = str(sf.relative_to(target_path))
            if any(s in rel.lower() for s in ["test/", "mock/", "node_modules/"]):
                continue
            self.findings.extend(self._scan_file(sf))

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

    def _run_slither(self, target_dir: str) -> list[Finding]:
        findings = []
        try:
            result = subprocess.run(
                ["slither", target_dir, "--json", "-", "--exclude-informational", "--exclude-low"],
                capture_output=True, text=True, timeout=300, cwd=target_dir,
            )
            if result.stdout:
                data = json.loads(result.stdout)
                for det in data.get("results", {}).get("detectors", []):
                    sev = det.get("impact", "info").lower()
                    if sev not in ("critical", "high", "medium"):
                        continue
                    els = det.get("elements", [{}])
                    src = els[0].get("source_mapping", {}) if els else {}
                    findings.append(Finding(
                        id=f"SLITHER-{det.get('check', '?')}",
                        pattern_id=det.get("check", ""),
                        file=src.get("filename_relative", ""),
                        line=(src.get("lines", [0]) or [0])[0],
                        severity=sev, name=det.get("check", ""),
                        description=det.get("description", ""),
                        source="slither",
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

        for pat in SOLIDITY_PATTERNS:
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
                    recommendation=pat["recommendation"],
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
            "slither_used": self.slither_available,
        }
