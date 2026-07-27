"""
CORTEX-BOUNTY CLI — Unified Command Surface

Commands:
  hunt     — Scan all platforms, rank targets
  scan     — Run VENOM static analysis on a target
  recon    — JIL protocol reconnaissance
  submit   — Format + notarize a report for submission
  status   — Portfolio dashboard
  migrate  — Import existing submissions into the ledger
"""
import asyncio
import sys
from pathlib import Path


def _run_async(coro):
    """Run an async coroutine from sync context."""
    return asyncio.run(coro)


def cmd_hunt(args):
    """Scan all bounty platforms and rank targets."""
    from cortex_bounty.hydra.aggregator import Aggregator
    from rich.console import Console
    from rich.table import Table

    console = Console()
    min_payout = float(args[0]) if args else 0
    platform_filter = args[1] if len(args) > 1 else None

    async def _hunt():
        agg = Aggregator()
        console.print("[bold blue]HYDRA · Scanning all platforms...[/bold blue]")
        targets = await agg.collect_all(min_payout=min_payout)

        if platform_filter:
            targets = [t for t in targets if t.platform == platform_filter]

        console.print(f"  [green]Found {len(targets)} targets[/green]")

        if not targets:
            console.print("  [dim]No targets found matching criteria.[/dim]")
            return

        table = Table(title=f"Bounty Targets (min ${min_payout:,.0f})")
        table.add_column("#", justify="right", style="dim")
        table.add_column("Platform", style="magenta")
        table.add_column("Project", style="cyan")
        table.add_column("Max Payout", justify="right", style="green")
        table.add_column("Score", justify="right", style="yellow")
        table.add_column("KYC", justify="center")
        table.add_column("Status")
        table.add_column("Repo")

        for i, t in enumerate(targets[:30], 1):
            table.add_row(
                str(i),
                t.platform.upper(),
                t.project[:30],
                f"${t.max_payout:,.0f}" if t.max_payout else "?",
                f"{t.score:.3f}",
                "⚠" if t.kyc_required else "✓",
                t.status[:10],
                t.repo_url[:40] if t.repo_url else "—",
            )
        console.print(table)

    _run_async(_hunt())


def cmd_scan(args):
    """Run VENOM static analysis on a target directory."""
    from cortex_bounty.venom.ast_walker import ASTWalker
    from rich.console import Console
    from rich.table import Table

    console = Console()

    if not args:
        console.print("[red]Usage: cortex-bounty scan <target-dir>[/red]")
        return

    target_dir = args[0]
    walker = ASTWalker()

    console.print(f"[bold blue]VENOM · Scanning {target_dir}[/bold blue]")

    try:
        findings = walker.scan(target_dir)
        summary = walker.summary()

        console.print(f"  Total findings: [bold]{summary['total']}[/bold]")
        console.print(f"  By severity: {summary['by_severity']}")
        console.print(f"  By source: {summary['by_source']}")
        console.print(f"  Files with findings: {summary['files']}")

        if findings:
            table = Table(title="Vulnerability Findings")
            table.add_column("Severity", style="bold")
            table.add_column("ID")
            table.add_column("Name", style="cyan")
            table.add_column("File")
            table.add_column("Line", justify="right")
            table.add_column("Source")

            for f in findings[:40]:
                sev_style = {"critical": "bold red", "high": "red", "medium": "yellow"}.get(f.severity, "dim")
                table.add_row(
                    f.severity.upper(),
                    f.pattern_id,
                    f.name[:35],
                    Path(f.file).name,
                    str(f.line),
                    f.source.upper(),
                    style=sev_style,
                )
            console.print(table)

    except FileNotFoundError as e:
        console.print(f"  [red]{e}[/red]")


def cmd_recon(args):
    """JIL protocol reconnaissance."""
    from cortex_bounty.jil.engine import JILEngine
    from rich.console import Console

    console = Console()

    if not args:
        console.print("[red]Usage: cortex-bounty recon <protocol-slug> [address][/red]")
        return

    target = args[0]
    address = args[1] if len(args) > 1 else None

    async def _recon():
        async with JILEngine() as jil:
            console.print(f"[bold blue]JIL · Recon: {target}[/bold blue]")
            intel = await jil.full_recon(target, address)

            console.print(f"  Name: [cyan]{intel.name}[/cyan]")
            console.print(f"  Category: {intel.category}")
            console.print(f"  TVL: [green]${intel.tvl_current:,.0f}[/green]")
            console.print(f"  TVL Peak: ${intel.tvl_peak:,.0f}")
            console.print(f"  Trend: {intel.tvl_trend}")
            console.print(f"  Chains: {', '.join(intel.chains[:5])}")
            console.print(f"  Audits: {len(intel.audit_links)}")
            console.print(f"  Risk Score: [bold yellow]{intel.risk_score}/100[/bold yellow]")
            console.print(f"  GitHub: {intel.github_org}")

            if intel.source_code:
                for addr, src in intel.source_code.items():
                    console.print(f"  Contract [{addr[:10]}...]: {src.get('contract_name', '?')}")

    _run_async(_recon())


def cmd_submit(args):
    """Format and notarize a report for submission."""
    from cortex_bounty.reaper.notarizer import Notarizer
    from cortex_bounty.ledger.db import BountyDB
    from rich.console import Console

    console = Console()

    if len(args) < 2:
        console.print("[red]Usage: cortex-bounty submit <platform> <report-file>[/red]")
        console.print("[dim]Platforms: immunefi, sherlock, code4rena[/dim]")
        return

    platform = args[0]
    report_file = args[1]

    path = Path(report_file)
    if not path.exists():
        console.print(f"[red]File not found: {report_file}[/red]")
        return

    # Notarize
    notarizer = Notarizer()
    proof = notarizer.notarize_file(report_file)

    console.print("[bold blue]REAPER · Notarized[/bold blue]")
    console.print(f"  SHA256: [cyan]{proof['sha256']}[/cyan]")
    console.print(f"  Timestamp: {proof['timestamp']}")
    console.print(f"  Sig: {proof['sig_file']}")

    # Track in ledger
    db = BountyDB()
    try:
        hunt_id = db.create_hunt(platform=platform, target=path.stem)
        sub_id = db.create_submission(
            hunt_id=hunt_id,
            platform=platform,
            title=path.stem,
            report_hash=proof["sha256"],
            report_path=str(path),
        )
        db.update_hunt(hunt_id, status="submitted")
        console.print(f"  Hunt: {hunt_id}")
        console.print(f"  Submission: {sub_id}")
    finally:
        db.close()


def cmd_status(args):
    """Show portfolio dashboard."""
    from cortex_bounty.ledger.dashboard import render_dashboard
    from cortex_bounty.ledger.db import BountyDB

    db = BountyDB()
    try:
        render_dashboard(db)
    finally:
        db.close()


def cmd_migrate(args):
    """Import existing submissions into the ledger."""
    from cortex_bounty.ledger.db import BountyDB
    from cortex_bounty.reaper.notarizer import Notarizer
    from cortex_bounty.config import SUBMISSIONS_DIR
    from rich.console import Console

    console = Console()
    db = BountyDB()
    notarizer = Notarizer()

    console.print("[bold blue]LEDGER · Migrating existing data[/bold blue]")

    # Import existing submissions
    sub_dir = SUBMISSIONS_DIR
    if sub_dir.exists():
        for f in sub_dir.glob("SUBMIT_*.md"):
            parts = f.stem.split("_")
            platform = parts[1].lower() if len(parts) > 1 else "unknown"
            title = "_".join(parts[2:-1]) if len(parts) > 3 else f.stem

            proof = notarizer.notarize_content(f.read_text())
            hunt_id = db.create_hunt(platform=platform, target=title)
            db.create_submission(
                hunt_id=hunt_id, platform=platform, title=title,
                report_hash=proof["sha256"], report_path=str(f),
            )
            db.update_hunt(hunt_id, status="submitted")
            console.print(f"  ✓ {f.name}")

    db.close()
    console.print("[green]Migration complete.[/green]")


def cmd_daemon(args):
    """Run autonomous bounty hunting daemon."""
    from cortex_bounty.daemon import run_daemon
    from rich.console import Console

    console = Console()
    cycles = int(args[0]) if args else 1
    console.print(
        f"[bold blue]DAEMON · Starting "
        f"({cycles} cycles)[/bold blue]"
    )
    asyncio.run(run_daemon(cycles=cycles))


def cmd_arena(args):
    """Run the Arena audit competition agent."""
    from cortex_bounty.arena.engine import run_arena
    from rich.console import Console

    console = Console()
    cycles = int(args[0]) if args else 1
    auto_submit = "--submit" in args
    console.print(
        f"[bold blue]ARENA · Audit Competition Agent "
        f"({cycles} cycles)[/bold blue]"
    )
    asyncio.run(run_arena(cycles=cycles, auto_submit=auto_submit))


def cmd_arena_scan(args):
    """Quick scan of active audit competitions."""
    from cortex_bounty.hydra.audit_competitions import (
        AuditCompetitionScraper,
        CompetitionStatus,
        calculate_exergy_score,
    )
    from rich.console import Console
    from rich.table import Table

    console = Console()

    async def _scan():
        async with AuditCompetitionScraper() as scraper:
            console.print("[bold blue]ARENA · Scanning competitions...[/bold blue]")
            comps = await scraper.fetch_competitions()

            for c in comps:
                calculate_exergy_score(c)

            # Filter
            show_all = "--all" in args
            if not show_all:
                comps = [
                    c for c in comps
                    if c.status != CompetitionStatus.FINISHED
                ]

            console.print(f"  Found {len(comps)} competitions")

            table = Table(title="Immunefi Audit Competitions")
            table.add_column("#", justify="right", style="dim")
            table.add_column("Status", style="bold")
            table.add_column("Type", style="dim")
            table.add_column("Project", style="cyan")
            table.add_column("Reward Pool", justify="right", style="green")
            table.add_column("Time Left", style="yellow")
            table.add_column("Score", justify="right", style="magenta")
            table.add_column("KYC", justify="center")

            sorted_comps = sorted(
                comps, key=lambda c: c.exergy_score, reverse=True
            )
            for i, c in enumerate(sorted_comps[:30], 1):
                status_style = {
                    CompetitionStatus.LIVE: "bold green",
                    CompetitionStatus.EVALUATING: "yellow",
                    CompetitionStatus.UPCOMING: "blue",
                }.get(c.status, "dim")
                table.add_row(
                    str(i),
                    c.status.value.upper(),
                    c.comp_type.value[:8],
                    c.project[:35],
                    f"${c.reward_pool:,.0f}" if c.reward_pool else "TBD",
                    c.time_remaining or "—",
                    f"{c.exergy_score:.3f}",
                    "⚠" if c.kyc_required else "✓",
                    style=status_style,
                )
            console.print(table)

    _run_async(_scan())


def cmd_arena_status(args):
    """Show Arena agent state and tracked competitions."""
    from cortex_bounty.arena.engine import ArenaEngine
    from rich.console import Console

    Console()
    engine = ArenaEngine()
    engine._print_summary()


def cmd_clone(args):
    """Clone a target repo from GitHub."""
    import subprocess
    from cortex_bounty.config import Config
    from rich.console import Console

    console = Console()
    if len(args) < 2:
        console.print(
            "[red]Usage: cortex-bounty clone "
            "<name> <repo-url>[/red]"
        )
        return

    name = args[0]
    url = args[1]
    target = Path(Config.BASE_DIR) / "targets" / name

    if target.exists():
        console.print(
            f"[yellow]Already exists: {target}[/yellow]"
        )
        return

    console.print(
        f"[bold blue]CLONE · {name}[/bold blue]"
    )
    subprocess.run(
        ["git", "clone", "--depth", "1", url, str(target)],
        timeout=120,
    )
    console.print(f"  ✓ {target}")


COMMANDS = {
    "hunt": cmd_hunt,
    "scan": cmd_scan,
    "recon": cmd_recon,
    "submit": cmd_submit,
    "status": cmd_status,
    "migrate": cmd_migrate,
    "daemon": cmd_daemon,
    "clone": cmd_clone,
    "arena": cmd_arena,
    "arena-scan": cmd_arena_scan,
    "arena-status": cmd_arena_status,
}

HELP_TEXT = """
[bold]CORTEX-BOUNTY v2.0 — Sovereign Bounty Hunting Engine[/bold]

[cyan]Commands:[/cyan]
  hunt [min_payout] [platform]  Scan all platforms, rank targets
  scan <target-dir>             Run VENOM static analysis
  recon <protocol> [address]    JIL protocol reconnaissance
  submit <platform> <file>      Notarize + track a submission
  status                        Portfolio dashboard
  migrate                       Import existing data into ledger
  daemon [cycles]               Run autonomous hunt engine
  clone <name> <url>            Clone a target repo

[cyan]Arena (Audit Competitions):[/cyan]
  arena [cycles] [--submit]     Run autonomous competition agent
  arena-scan [--all]            Quick scan active competitions
  arena-status                  Show Arena tracking state
"""


def main():
    from rich.console import Console
    console = Console()

    args = sys.argv[1:]

    if not args or args[0] in ("-h", "--help", "help"):
        console.print(HELP_TEXT)
        return

    cmd_name = args[0]
    cmd_args = args[1:]

    if cmd_name in COMMANDS:
        COMMANDS[cmd_name](cmd_args)
    else:
        console.print(f"[red]Unknown command: {cmd_name}[/red]")
        console.print(HELP_TEXT)


if __name__ == "__main__":
    main()
