"""
VENOM — Cross-Language AST Walker

Unified entry point that auto-detects language and dispatches
to the appropriate scanner.
"""
from pathlib import Path

from cortex_bounty.venom.solidity_scanner import SolidityScanner, Finding
from cortex_bounty.venom.rust_scanner import RustScanner
from cortex_bounty.venom.c_scanner import CScanner


class ASTWalker:
    """
    Auto-detecting scanner. Identifies the predominant language
    in a target directory and runs the appropriate scanner(s).
    """

    def __init__(self):
        self.findings: list[Finding] = []

    def scan(self, target_dir: str) -> list[Finding]:
        """Scan a directory, auto-detecting language."""
        self.findings = []
        target_path = Path(target_dir)
        if not target_path.exists():
            raise FileNotFoundError(f"Not found: {target_dir}")

        # Count files per language
        sol_count = len(list(target_path.rglob("*.sol")))
        rs_count = len(list(target_path.rglob("*.rs")))
        c_count = len(list(target_path.rglob("*.c"))) + len(list(target_path.rglob("*.h")))

        # Scan all detected languages
        if sol_count > 0:
            scanner = SolidityScanner()
            self.findings.extend(scanner.scan_directory(target_dir))

        if rs_count > 0:
            scanner = RustScanner()
            self.findings.extend(scanner.scan_directory(target_dir))

        if c_count > 0:
            scanner = CScanner()
            self.findings.extend(scanner.scan_directory(target_dir))

        # Sort by severity
        sev_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        self.findings.sort(key=lambda x: sev_order.get(x.severity, 5))

        return self.findings

    def summary(self) -> dict:
        by_sev = {}
        by_source = {}
        for f in self.findings:
            by_sev[f.severity] = by_sev.get(f.severity, 0) + 1
            by_source[f.source] = by_source.get(f.source, 0) + 1
        return {
            "total": len(self.findings),
            "by_severity": by_sev,
            "by_source": by_source,
            "files": len(set(f.file for f in self.findings)),
        }
