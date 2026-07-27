"""
VENOM — C/C++ Static Scanner

Pattern matching for memory safety vulnerabilities in C codebases
(Firedancer, low-level infrastructure).
"""
import re
from pathlib import Path

from cortex_bounty.venom.patterns import C_PATTERNS
from cortex_bounty.venom.solidity_scanner import Finding


class CScanner:
    def __init__(self):
        self.findings: list[Finding] = []

    def scan_directory(self, target_dir: str) -> list[Finding]:
        self.findings = []
        target_path = Path(target_dir)
        if not target_path.exists():
            raise FileNotFoundError(f"Not found: {target_dir}")

        c_files = list(target_path.rglob("*.c")) + list(target_path.rglob("*.h"))
        if not c_files:
            return []

        for cf in c_files:
            rel = str(cf.relative_to(target_path))
            if any(s in rel.lower() for s in ["test", "build/", "cmake"]):
                continue
            self.findings.extend(self._scan_file(cf))

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

    def _scan_file(self, filepath: Path) -> list[Finding]:
        findings = []
        try:
            content = filepath.read_text(encoding="utf-8", errors="ignore")
        except OSError:
            return findings

        for pat in C_PATTERNS:
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
        }
