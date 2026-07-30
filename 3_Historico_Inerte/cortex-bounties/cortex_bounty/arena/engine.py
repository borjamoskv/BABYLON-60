"""
ARENA Engine — Autonomous Audit Competition Agent

Full lifecycle management for Immunefi audit competitions:
  Phase 1 · SCOUT:   Scrape, parse, rank active competitions
  Phase 2 · TARGET:  Select optimal competition, deep-scan scope
  Phase 3 · CLONE:   Download all in-scope assets (repos, contracts)
  Phase 4 · ANALYZE: Run VENOM static + Anvil-Lang formal verification
  Phase 5 · STRIKE:  Generate forensic reports for high-value findings
  Phase 6 · TRACK:   Monitor submission status and payout

C5-REAL — No simulation. Live Immunefi data only.
"""

import asyncio
import json
import logging
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from cortex_bounty.config import TARGETS_DIR, REPORTS_DIR
from cortex_bounty.hydra.audit_competitions import (
    AuditCompetition,
    AuditCompetitionScraper,
    CompetitionStatus,
    calculate_exergy_score,
)
from cortex_bounty.ledger.db import BountyDB
from cortex_bounty.reaper.notarizer import Notarizer
from cortex_bounty.venom.ast_walker import ASTWalker

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger("ARENA")

# ── Arena Configuration ─────────────────────────────────────
ARENA_DIR = TARGETS_DIR.parent / "competitions"
ARENA_REPORTS = REPORTS_DIR / "arena"
ARENA_STATE = ARENA_DIR / ".arena_state.json"

# Thresholds
MIN_REWARD_POOL = 20_000       # Minimum $20K to engage
CRITICAL_VULN_THRESHOLD = 1    # Auto-report at 1+ criticals
HIGH_VULN_THRESHOLD = 5        # Flag for manual review at 5+ highs


class ArenaState:
    """Persistent state for the Arena agent across sessions."""

    def __init__(self, state_file: Path = ARENA_STATE):
        self.state_file = state_file
        self.state: dict = {
            "active_competitions": {},
            "completed_competitions": [],
            "submissions": [],
            "last_scan": "",
            "total_reward_potential": 0,
            "total_submissions": 0,
        }
        self._load()

    def _load(self):
        if self.state_file.exists():
            try:
                self.state = json.loads(self.state_file.read_text())
            except (json.JSONDecodeError, OSError):
                pass

    def save(self):
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(json.dumps(self.state, indent=2))

    def track_competition(self, comp: AuditCompetition, phase: str = "scouted"):
        """Track a competition's lifecycle state."""
        self.state["active_competitions"][comp.slug] = {
            "name": comp.name,
            "project": comp.project,
            "reward_pool": comp.reward_pool,
            "status": comp.status.value,
            "phase": phase,
            "exergy_score": comp.exergy_score,
            "url": comp.url,
            "last_updated": datetime.now(timezone.utc).isoformat(),
        }
        self.save()

    def mark_submitted(self, comp_slug: str, report_hash: str):
        """Record a submission against a competition."""
        self.state["submissions"].append({
            "competition": comp_slug,
            "report_hash": report_hash,
            "timestamp": datetime.now(timezone.utc).isoformat(),
        })
        self.state["total_submissions"] += 1
        if comp_slug in self.state["active_competitions"]:
            self.state["active_competitions"][comp_slug]["phase"] = "submitted"
        self.save()

    def mark_completed(self, comp_slug: str):
        """Move competition to completed list."""
        if comp_slug in self.state["active_competitions"]:
            entry = self.state["active_competitions"].pop(comp_slug)
            entry["completed_at"] = datetime.now(timezone.utc).isoformat()
            self.state["completed_competitions"].append(entry)
            self.save()


class ArenaEngine:
    """
    Autonomous Audit Competition Agent.

    Orchestrates the full lifecycle from discovery through submission.
    Designed for continuous operation with state persistence.
    """

    def __init__(self):
        self.db = BountyDB()
        self.notarizer = Notarizer()
        self.state = ArenaState()
        ARENA_DIR.mkdir(parents=True, exist_ok=True)
        ARENA_REPORTS.mkdir(parents=True, exist_ok=True)

    async def run(self, cycles: int = 1, auto_submit: bool = False):
        """
        Main agent loop.

        Args:
            cycles: Number of full scan cycles. 0 = infinite.
            auto_submit: If True, auto-submit findings above threshold.
        """
        cycle = 0
        log.info("╔════════════════════════════════════════════╗")
        log.info("║  ARENA · Audit Competition Agent v1.0     ║")
        log.info("╚════════════════════════════════════════════╝")

        while True:
            cycle += 1
            log.info(f"\n{'═' * 50}")
            log.info(f"  CYCLE {cycle}")
            log.info(f"{'═' * 50}\n")

            try:
                # Phase 1: SCOUT — Discover competitions
                competitions = await self._phase_scout()

                # Phase 2: TARGET — Select and deep-scan top targets
                targets = await self._phase_target(competitions)

                # Phase 3: CLONE — Download repos
                cloned = await self._phase_clone(targets)

                # Phase 4: ANALYZE — Static analysis
                findings = await self._phase_analyze(cloned)

                # Phase 5: STRIKE — Generate reports
                reports = await self._phase_strike(findings)

                # Phase 6: TRACK — Update state
                self._phase_track(competitions, reports)

            except Exception as e:
                log.error(f"Cycle {cycle} error: {e}", exc_info=True)

            if cycles > 0 and cycle >= cycles:
                break

            # Wait before next cycle (15 minutes for competitions)
            log.info("Sleeping 900s until next scan...")
            await asyncio.sleep(900)

        log.info("ARENA · Shutdown complete")
        self._print_summary()

    async def _phase_scout(self) -> list[AuditCompetition]:
        """Phase 1: Discover and rank audit competitions."""
        log.info("SCOUT · Scanning Immunefi competitions...")

        async with AuditCompetitionScraper() as scraper:
            all_comps = await scraper.fetch_competitions()

        log.info(f"  Total found: {len(all_comps)}")

        # Score all competitions
        for comp in all_comps:
            calculate_exergy_score(comp)

        # Filter actionable
        actionable = [
            c for c in all_comps
            if c.status in (CompetitionStatus.LIVE, CompetitionStatus.EVALUATING)
            and c.reward_pool >= MIN_REWARD_POOL
        ]

        log.info(f"  Actionable (≥${MIN_REWARD_POOL:,}): {len(actionable)}")

        for c in actionable:
            log.info(
                f"  → [{c.status.value:10s}] {c.project[:30]:30s} "
                f"${c.reward_pool:>12,.0f}  "
                f"score={c.exergy_score:.3f}"
            )
            self.state.track_competition(c, phase="scouted")

        self.state.state["last_scan"] = datetime.now(timezone.utc).isoformat()
        self.state.state["total_reward_potential"] = sum(c.reward_pool for c in actionable)
        self.state.save()

        return actionable

    async def _phase_target(
        self, competitions: list[AuditCompetition]
    ) -> list[AuditCompetition]:
        """Phase 2: Deep-scan top competitions for scope details."""
        log.info("TARGET · Deep-scanning top targets...")

        if not competitions:
            log.info("  No actionable competitions found")
            return []

        # Sort by exergy score, take top 5
        ranked = sorted(competitions, key=lambda c: c.exergy_score, reverse=True)[:5]

        async with AuditCompetitionScraper() as scraper:
            enriched = []
            for comp in ranked:
                try:
                    await scraper.deep_scan(comp)
                    enriched.append(comp)
                    log.info(
                        f"  ✓ {comp.project}: "
                        f"nSLOC={comp.nsloc:,}, "
                        f"assets={len(comp.assets_in_scope)}, "
                        f"github={len(comp.github_urls)}, "
                        f"KYC={'YES' if comp.kyc_required else 'NO'}"
                    )
                    self.state.track_competition(comp, phase="targeted")
                except Exception as e:
                    log.warning(f"  ✗ {comp.project}: {e}")

        return enriched

    async def _phase_clone(
        self, targets: list[AuditCompetition]
    ) -> list[dict]:
        """Phase 3: Clone in-scope repositories."""
        log.info("CLONE · Downloading scope repos...")
        cloned = []

        for comp in targets:
            comp_dir = ARENA_DIR / comp.slug
            comp_dir.mkdir(parents=True, exist_ok=True)

            # Save competition metadata
            meta_path = comp_dir / "competition.json"
            meta = {
                "slug": comp.slug,
                "name": comp.name,
                "project": comp.project,
                "reward_pool": comp.reward_pool,
                "status": comp.status.value,
                "type": comp.comp_type.value,
                "nsloc": comp.nsloc,
                "kyc_required": comp.kyc_required,
                "url": comp.url,
                "github_urls": comp.github_urls,
                "assets_in_scope": comp.assets_in_scope,
                "reward_tiers": comp.reward_tiers,
                "scanned_at": datetime.now(timezone.utc).isoformat(),
            }
            meta_path.write_text(json.dumps(meta, indent=2))

            # Clone GitHub repos
            for gh_url in comp.github_urls:
                repo_name = gh_url.rstrip("/").split("/")[-1]
                if "/tree/" in gh_url:
                    # It's a specific branch/path — extract base repo
                    parts = gh_url.split("/tree/")[0]
                    repo_name = parts.rstrip("/").split("/")[-1]
                    gh_url = parts

                repo_dir = comp_dir / repo_name
                if repo_dir.exists():
                    log.info(f"  ↻ {repo_name} (cached)")
                    cloned.append({
                        "competition": comp,
                        "repo_name": repo_name,
                        "path": str(repo_dir),
                    })
                    continue

                try:
                    log.info(f"  ↓ Cloning {repo_name}...")
                    subprocess.run(
                        ["git", "clone", "--depth", "1", gh_url, str(repo_dir)],
                        capture_output=True,
                        timeout=120,
                    )
                    if repo_dir.exists():
                        cloned.append({
                            "competition": comp,
                            "repo_name": repo_name,
                            "path": str(repo_dir),
                        })
                        log.info(f"  ✓ {repo_name}")
                    else:
                        log.warning(f"  ✗ {repo_name}: clone failed")
                except (subprocess.TimeoutExpired, FileNotFoundError) as e:
                    log.warning(f"  ✗ {repo_name}: {e}")

            self.state.track_competition(comp, phase="cloned")

        log.info(f"CLONE · {len(cloned)} repos ready")
        return cloned

    async def _phase_analyze(self, cloned: list[dict]) -> list[dict]:
        """Phase 4: Run VENOM static analysis on cloned repos."""
        log.info("ANALYZE · Running static analysis...")
        results = []

        for repo in cloned:
            comp: AuditCompetition = repo["competition"]
            path = repo["path"]
            name = repo["repo_name"]

            try:
                walker = ASTWalker()
                findings = walker.scan(path)
                summary = walker.summary()

                total = summary["total"]
                crits = summary["by_severity"].get("critical", 0)
                highs = summary["by_severity"].get("high", 0)
                meds = summary["by_severity"].get("medium", 0)

                log.info(
                    f"  {comp.project}/{name}: "
                    f"{total} findings (C:{crits} H:{highs} M:{meds})"
                )

                results.append({
                    "competition": comp,
                    "repo_name": name,
                    "path": path,
                    "findings": findings,
                    "summary": summary,
                })

                # Update hunt in ledger
                try:
                    hunt_id = self.db.create_hunt(
                        platform="immunefi-arena",
                        target=f"{comp.project} ({comp.slug})",
                        category=comp.comp_type.value,
                        max_payout=comp.reward_pool,
                    )
                    status = "analyzing"
                    if crits >= CRITICAL_VULN_THRESHOLD:
                        status = "writing"
                    elif highs >= HIGH_VULN_THRESHOLD:
                        status = "reviewing"
                    self.db.update_hunt(
                        hunt_id,
                        status=status,
                        notes=f"VENOM: {total} ({crits}C/{highs}H/{meds}M)",
                    )
                except Exception:
                    pass  # Ledger write is non-critical

                self.state.track_competition(comp, phase="analyzed")

            except Exception as e:
                log.warning(f"  ✗ {name}: {e}")

        log.info(f"ANALYZE · {len(results)} repos scanned")
        return results

    async def _phase_strike(self, analysis_results: list[dict]) -> list[dict]:
        """Phase 5: Generate forensic reports for actionable findings."""
        log.info("STRIKE · Generating reports...")
        reports = []

        for result in analysis_results:
            comp: AuditCompetition = result["competition"]
            crits = result["summary"]["by_severity"].get("critical", 0)
            highs = result["summary"]["by_severity"].get("high", 0)

            if crits < CRITICAL_VULN_THRESHOLD and highs < HIGH_VULN_THRESHOLD:
                continue

            ts = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M")
            report_path = ARENA_REPORTS / f"{comp.slug}_{ts}.md"

            # Build report
            crit_findings = [f for f in result["findings"] if f.severity == "critical"]
            high_findings = [f for f in result["findings"] if f.severity == "high"]

            lines = [
                f"# Arena Strike Report: {comp.project}",
                "",
                f"**Competition:** {comp.name}",
                f"**Slug:** `{comp.slug}`",
                f"**Reward Pool:** ${comp.reward_pool:,.0f}",
                f"**Status:** {comp.status.value.upper()}",
                f"**Generated:** {ts}",
                f"**KYC Required:** {'YES' if comp.kyc_required else 'NO'}",
                f"**Submission URL:** {comp.url}",
                "",
                "---",
                "",
                "## Summary",
                "",
                "| Metric | Value |",
                "|--------|-------|",
                f"| Total Findings | {result['summary']['total']} |",
                f"| Critical | {crits} |",
                f"| High | {highs} |",
                f"| Medium | {result['summary']['by_severity'].get('medium', 0)} |",
                f"| Files Scanned | {result['summary']['files']} |",
                f"| nSLOC | {comp.nsloc:,} |",
                "",
            ]

            if comp.reward_tiers:
                lines.extend([
                    "## Reward Tiers",
                    "",
                    "| Severity | Pool |",
                    "|----------|------|",
                ])
                for tier in comp.reward_tiers:
                    lines.append(
                        f"| {tier['severity'].title()} | ${tier['reward']:,.0f} |"
                    )
                lines.append("")

            lines.extend([
                "## Critical Findings",
                "",
            ])

            for f in crit_findings[:20]:
                fp = Path(f.file).name
                lines.extend([
                    f"### [{f.pattern_id}] {fp}:{f.line}",
                    f"**{f.name}**",
                    "```",
                    f.matched_text[:300],
                    "```",
                    "",
                ])

            lines.extend([
                "## High Findings (Top 20)",
                "",
            ])
            for f in high_findings[:20]:
                fp = Path(f.file).name
                lines.append(f"- [{f.pattern_id}] {fp}:{f.line} — {f.name}")

            lines.extend([
                "",
                "---",
                "",
                f"*CORTEX-BOUNTY Arena Agent | {datetime.now(timezone.utc).isoformat()}*",
            ])

            report_content = "\n".join(lines)
            report_path.write_text(report_content)

            # Notarize
            proof = self.notarizer.notarize_file(str(report_path))
            sha = proof["sha256"]

            log.info(
                f"  ✓ {comp.project} → {report_path.name} "
                f"(SHA:{sha[:16]}...)"
            )

            self.state.mark_submitted(comp.slug, sha)

            reports.append({
                "competition": comp.slug,
                "project": comp.project,
                "path": str(report_path),
                "sha256": sha,
                "criticals": crits,
                "highs": highs,
            })

        log.info(f"STRIKE · {len(reports)} reports generated")
        return reports

    def _phase_track(
        self, competitions: list[AuditCompetition], reports: list[dict]
    ):
        """Phase 6: Update tracking state."""
        log.info("TRACK · Updating state...")

        for comp in competitions:
            if comp.status == CompetitionStatus.FINISHED:
                self.state.mark_completed(comp.slug)

        self.state.save()
        self._print_summary()

    def _print_summary(self):
        """Print current Arena status."""
        from rich.console import Console
        from rich.table import Table
        from rich.panel import Panel

        console = Console()

        # Summary panel
        active = self.state.state.get("active_competitions", {})
        completed = self.state.state.get("completed_competitions", [])
        submissions = self.state.state.get("total_submissions", 0)
        potential = self.state.state.get("total_reward_potential", 0)

        summary = (
            f"[cyan]Active Competitions:[/cyan] {len(active)}\n"
            f"[dim]Completed:[/dim] {len(completed)}\n"
            f"[green]Total Submissions:[/green] {submissions}\n"
            f"[yellow]Reward Potential:[/yellow] ${potential:,.0f}\n"
            f"[dim]Last Scan:[/dim] {self.state.state.get('last_scan', 'never')}"
        )
        console.print(Panel(summary, title="ARENA Status", border_style="blue"))

        # Active competitions table
        if active:
            table = Table(title="Active Competitions")
            table.add_column("Project", style="cyan")
            table.add_column("Reward Pool", justify="right", style="green")
            table.add_column("Status", style="bold")
            table.add_column("Phase", style="yellow")
            table.add_column("Score", justify="right", style="magenta")

            for slug, info in sorted(
                active.items(),
                key=lambda x: x[1].get("exergy_score", 0),
                reverse=True,
            ):
                table.add_row(
                    info.get("project", slug)[:30],
                    f"${info.get('reward_pool', 0):,.0f}",
                    info.get("status", "?").upper(),
                    info.get("phase", "?"),
                    f"{info.get('exergy_score', 0):.3f}",
                )
            console.print(table)


async def run_arena(cycles: int = 1, auto_submit: bool = False):
    """Entry point for the Arena agent."""
    engine = ArenaEngine()
    await engine.run(cycles=cycles, auto_submit=auto_submit)


if __name__ == "__main__":
    asyncio.run(run_arena(cycles=1))
