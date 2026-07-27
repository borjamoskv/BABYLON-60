"""
CORTEX-BOUNTY DAEMON — Autonomous Bounty Hunting Engine

Continuous loop:
1. HYDRA: Scan platforms for new targets
2. VENOM: Static analysis on downloaded repos
3. REAPER: Format + notarize high-value findings
4. LEDGER: Track all state transitions
5. Report generation for human review

C5-REAL — No simulation. Live data only.
"""

import asyncio
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from cortex_bounty.config import (
    TARGETS_DIR as CFG_TARGETS_DIR,
)
from cortex_bounty.hydra.aggregator import Aggregator
from cortex_bounty.jil.engine import JILEngine
from cortex_bounty.ledger.db import BountyDB
from cortex_bounty.reaper.notarizer import Notarizer
from cortex_bounty.venom.ast_walker import ASTWalker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("DAEMON")

# ── Configuration ──────────────────────────────────────
MIN_BOUNTY = 50_000
SCAN_INTERVAL = 3600  # 1 hour between full scans
CRITICAL_THRESHOLD = 3  # min criticals to auto-report
HIGH_THRESHOLD = 20  # min highs to flag for review
TARGETS_DIR = CFG_TARGETS_DIR
REPORTS_DIR = CFG_TARGETS_DIR.parent / "reports" / "auto"


class BountyDaemon:
    """Autonomous bounty hunting daemon."""

    def __init__(self):
        self.db = BountyDB()
        self.notarizer = Notarizer()
        self.running = False
        REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    async def run(self, cycles: int = 0):
        """
        Main daemon loop.

        Args:
            cycles: Number of cycles to run. 0 = infinite.
        """
        self.running = True
        cycle = 0
        log.info("DAEMON · Starting autonomous hunt engine")

        while self.running:
            cycle += 1
            log.info(f"═══ CYCLE {cycle} ═══")

            try:
                # Phase 1: HYDRA — Discover targets
                targets = await self._phase_hydra()

                # Phase 2: Clone — Download repos
                cloned = await self._phase_clone(targets)

                # Phase 3: VENOM — Scan for vulns
                findings = await self._phase_venom(cloned)

                # Phase 4: JIL — Enrich with protocol intel
                enriched = await self._phase_jil(findings)

                # Phase 5: REAPER — Generate reports
                _reports = await self._phase_reaper(enriched)

                # Phase 6: Dashboard
                self._phase_dashboard(cycle)

            except Exception as e:
                log.error(f"Cycle {cycle} error: {e}")

            if cycles > 0 and cycle >= cycles:
                break

            log.info(
                f"Sleeping {SCAN_INTERVAL}s until next cycle"
            )
            await asyncio.sleep(SCAN_INTERVAL)

        log.info("DAEMON · Shutdown complete")

    async def _phase_hydra(self) -> list:
        """Phase 1: Discover high-value targets."""
        log.info("HYDRA · Scanning platforms...")

        agg = Aggregator()
        targets = await agg.collect_all(
            min_payout=MIN_BOUNTY
        )

        log.info(f"HYDRA · Found {len(targets)} targets")

        # Record new targets in ledger
        existing = {
            h["target"]
            for h in self.db.get_hunts()
        }
        new_targets = []
        for t in targets:
            key = t.project
            if key not in existing:
                cat = t.category
                if isinstance(cat, list):
                    cat = ", ".join(str(c) for c in cat)
                hunt_id = self.db.create_hunt(
                    platform=t.platform or "unknown",
                    target=key,
                    category=str(cat) if cat else "",
                    max_payout=t.max_payout,
                )
                self.db.update_hunt(
                    hunt_id,
                    status="scouting",
                )
                new_targets.append(t)
                log.info(
                    f"  + NEW: {key} "
                    f"(${t.max_payout:,.0f})"
                )

        return targets

    async def _phase_clone(self, targets: list) -> list:
        """Phase 2: Clone repos that have GitHub URLs."""
        log.info("CLONE · Downloading repos...")
        cloned = []

        for t in targets[:30]:  # Top 30 by score
            repo_url = t.repo_url or ""
            name = t.project
            slug = (
                name.lower()
                .replace(" ", "-")
                .replace("/", "-")
            )
            target_path = TARGETS_DIR / slug

            if not repo_url or not repo_url.startswith(
                "http"
            ):
                # Check if already downloaded
                if target_path.exists():
                    cloned.append(
                        {
                            "name": name,
                            "path": str(target_path),
                            "target": t,
                        }
                    )
                continue

            if target_path.exists():
                cloned.append(
                    {
                        "name": name,
                        "path": str(target_path),
                        "target": t,
                    }
                )
                continue

            # Clone the repo
            try:
                log.info(f"  Cloning {name}...")
                subprocess.run(
                    [
                        "git",
                        "clone",
                        "--depth",
                        "1",
                        repo_url,
                        str(target_path),
                    ],
                    capture_output=True,
                    timeout=120,
                )
                if target_path.exists():
                    cloned.append(
                        {
                            "name": name,
                            "path": str(target_path),
                            "target": t,
                        }
                    )
                    log.info(f"  ✓ {name}")
            except (subprocess.TimeoutExpired, Exception) as e:
                log.warning(f"  ✗ {name}: {e}")

        log.info(f"CLONE · {len(cloned)} repos ready")
        return cloned

    async def _phase_venom(self, cloned: list) -> list:
        """Phase 3: Run static analysis on all targets."""
        log.info("VENOM · Scanning targets...")
        results = []

        for repo in cloned:
            name = repo["name"]
            path = repo["path"]

            try:
                walker = ASTWalker()
                findings = walker.scan(path)
                summary = walker.summary()

                total = summary["total"]
                crits = summary["by_severity"].get(
                    "critical", 0
                )
                highs = summary["by_severity"].get(
                    "high", 0
                )
                meds = summary["by_severity"].get(
                    "medium", 0
                )

                if total > 0:
                    log.info(
                        f"  {name}: {total} findings "
                        f"(C:{crits} H:{highs} M:{meds})"
                    )

                    # Update hunt status
                    hunts = self.db.get_hunts()
                    for h in hunts:
                        if h["target"] == name:
                            status = "analyzing"
                            if crits >= CRITICAL_THRESHOLD:
                                status = "writing"
                            self.db.update_hunt(
                                h["id"],
                                status=status,
                                notes=(
                                    f"VENOM: {total} "
                                    f"({crits}C/{highs}H/"
                                    f"{meds}M)"
                                ),
                            )
                            break

                results.append(
                    {
                        "name": name,
                        "path": path,
                        "findings": findings,
                        "summary": summary,
                        "target": repo.get("target", {}),
                    }
                )

            except Exception as e:
                log.warning(f"  ✗ {name}: {e}")

        log.info(f"VENOM · {len(results)} targets scanned")
        return results

    async def _phase_jil(self, findings: list) -> list:
        """Phase 4: Enrich high-value findings."""
        log.info("JIL · Enriching targets...")
        enriched = []

        async with JILEngine() as jil:
            for result in findings:
                crits = result["summary"]["by_severity"].get(
                    "critical", 0
                )
                highs = result["summary"]["by_severity"].get(
                    "high", 0
                )

                # Only enrich if findings are significant
                if (
                    crits >= CRITICAL_THRESHOLD
                    or highs >= HIGH_THRESHOLD
                ):
                    try:
                        name = result["name"]
                        intel = await jil.full_recon(name)
                        result["intel"] = {
                            "tvl": intel.tvl_current,
                            "category": intel.category,
                            "chains": intel.chains,
                            "risk_score": intel.risk_score,
                            "github": intel.github_org,
                        }
                        log.info(
                            f"  {name}: TVL="
                            f"${intel.tvl_current:,.0f} "
                            f"Risk={intel.risk_score}/100"
                        )
                    except Exception:
                        result["intel"] = {}

                enriched.append(result)

        log.info(f"JIL · {len(enriched)} targets enriched")
        return enriched

    async def _phase_reaper(self, enriched: list) -> list:
        """Phase 5: Generate reports for high-value finds."""
        log.info("REAPER · Generating reports...")
        reports = []

        for result in enriched:
            crits = result["summary"]["by_severity"].get(
                "critical", 0
            )
            highs = result["summary"]["by_severity"].get(
                "high", 0
            )

            if crits < CRITICAL_THRESHOLD and highs < HIGH_THRESHOLD:
                continue

            name = result["name"]
            slug = (
                name.lower()
                .replace(" ", "-")
                .replace("/", "-")
            )
            ts = datetime.now(timezone.utc).strftime(
                "%Y%m%d_%H%M"
            )
            report_path = REPORTS_DIR / f"{slug}_{ts}.md"

            # Group findings by pattern
            from collections import Counter

            pattern_counts = Counter(
                f.pattern_id for f in result["findings"]
            )
            crit_findings = [
                f
                for f in result["findings"]
                if f.severity == "critical"
            ]
            high_findings = [
                f
                for f in result["findings"]
                if f.severity == "high"
            ]

            # Generate report
            target_obj = result.get("target", None)
            bounty = (
                getattr(target_obj, "max_payout", 0)
                if target_obj else 0
            )
            platform = (
                getattr(target_obj, "platform", "unknown")
                if target_obj else "unknown"
            )
            intel = result.get("intel", {})

            lines = [
                f"# Auto-Generated Vulnerability Report: "
                f"{name}",
                "",
                f"**Generated:** {ts}",
                f"**Platform:** {platform}",
                f"**Max Bounty:** ${bounty:,}",
                f"**TVL:** "
                f"${intel.get('tvl', 0):,.0f}"
                if intel
                else "",
                "",
                "## Summary",
                "",
                f"- Total findings: "
                f"{result['summary']['total']}",
                f"- Critical: {crits}",
                f"- High: {highs}",
                f"- Files scanned: "
                f"{result['summary']['files']}",
                "",
                "## Critical Findings",
                "",
            ]

            for f in crit_findings[:20]:
                fp = Path(f.file).name
                lines.append(
                    f"### [{f.pattern_id}] "
                    f"{fp}:{f.line}"
                )
                lines.append(f"**{f.name}**")
                lines.append("```")
                lines.append(f.matched_text[:200])
                lines.append("```")
                lines.append("")

            lines.append("## High Findings (Top 20)")
            lines.append("")

            for f in high_findings[:20]:
                fp = Path(f.file).name
                lines.append(
                    f"- [{f.pattern_id}] "
                    f"{fp}:{f.line} — {f.name}"
                )

            lines.append("")
            lines.append("## Pattern Distribution")
            lines.append("")
            for pid, count in pattern_counts.most_common():
                lines.append(f"- {pid}: {count}")

            report_content = "\n".join(lines)
            report_path.write_text(report_content)

            # Notarize
            proof = self.notarizer.notarize_file(
                str(report_path)
            )
            sig = proof["sha256"]
            log.info(
                f"  ✓ {name} → {report_path.name} "
                f"(SHA:{sig[:16]}...)"
            )

            reports.append(
                {
                    "name": name,
                    "path": str(report_path),
                    "sha256": sig,
                }
            )

        log.info(
            f"REAPER · {len(reports)} reports generated"
        )
        return reports

    def _phase_dashboard(self, cycle: int):
        """Phase 6: Print dashboard summary."""
        from cortex_bounty.ledger.dashboard import (
            render_dashboard,
        )

        log.info(f"DASHBOARD · Cycle {cycle} complete")
        render_dashboard(self.db)

    def stop(self):
        """Signal daemon to stop."""
        self.running = False


async def run_daemon(cycles: int = 1):
    """Entry point for the daemon."""
    daemon = BountyDaemon()
    await daemon.run(cycles=cycles)


if __name__ == "__main__":
    asyncio.run(run_daemon(cycles=1))
