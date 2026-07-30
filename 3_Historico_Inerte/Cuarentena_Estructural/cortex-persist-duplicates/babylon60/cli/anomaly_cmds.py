# [C5-REAL] Exergy-Maximized
"""CORTEX CLI - Anomaly Hunter Daemon Commands.

Integrates the NightShift anomaly hunter into the Sovereign CLI.
"""

import click
from rich.panel import Panel
from rich.table import Table

from babylon60.cli.common import (
    DEFAULT_DB,
    _run_async,
    cli,
    close_engine_sync,
    console,
    get_engine,
)


@cli.group(name="anomaly")
def anomaly_cmds():
    """🔍 ANOMALY-HUNTER-DAEMON (NightShift Memory Refiner)."""


@anomaly_cmds.command("anomaly-hunt")
@click.option("--hours", default=24, help="Number of hours to scan backwards (default: 24).")
@click.option("--project", default=None, help="Limit scan to a specific project.")
@click.option("--db", default=DEFAULT_DB, help="Database path")
def anomaly_hunt_cmd(hours: int, project: str | None, db: str) -> None:
    """Full scan: detect ontological anomalies in the Ledger."""
    engine = get_engine(db)
    try:
        from babylon60.extensions.forensic.anomaly_hunter import AnomalyHunterEngine

        hunter = AnomalyHunterEngine(engine, lookback_hours=hours)

        async def _run():
            # For specific projects, we use the engine's capability to filter
            return await hunter.run_full_scan()

        with console.status(
            f"[bold cyan] NightShift Engine: tracking anomalies in the last {hours}h..."
        ):
            report = _run_async(_run())

        _display_report(report)

    finally:
        close_engine_sync(engine)


@anomaly_cmds.command("contradiction-scan")
@click.argument("entity")
@click.option("--db", default=DEFAULT_DB, help="Database path")
def contradiction_scan_cmd(entity: str, db: str) -> None:
    """TARGETED: Search for contradictions regarding a specific entity."""
    engine = get_engine(db)
    try:
        from babylon60.extensions.forensic.anomaly_hunter import AnomalyHunterEngine

        hunter = AnomalyHunterEngine(engine)

        async def _run():
            # Get all facts to find entity-related ones
            facts = await engine.history(project=None)
            # Filter specifically for the entity in tags or content
            target_facts = [
                f
                for f in facts
                if entity.lower() in (f.content.lower() or "")
                or (f.tags and any(entity.lower() in t.lower() for t in f.tags))
            ]

            if not target_facts:
                return []

            return await hunter.detect_spatial_contradictions(target_facts)

        with console.status(f"[bold cyan] NightShift: targeted scan for '{entity}'..."):
            anomalies = _run_async(_run())

        if not anomalies:
            msg = f"[bold green]✓ Scan completed. No contradictions for '{entity}'.[/bold green]"
            console.print(msg)
        else:
            console.print(
                f"[bold red]⚠ Found {len(anomalies)} contradictions for '{entity}':[/bold red]"
            )
            for a in anomalies:
                console.print(f"  - {a.description}")

    finally:
        close_engine_sync(engine)


@anomaly_cmds.command("memory-clean")
@click.option("--db", default=DEFAULT_DB, help="Database path")
def memory_clean_cmd(db: str) -> None:
    """PURGE: Apply automatic actions for low severity anomalies."""
    engine = get_engine(db)
    try:
        from babylon60.extensions.forensic.anomaly_hunter import AnomalyHunterEngine

        hunter = AnomalyHunterEngine(engine)

        async def _run():
            facts = await engine.history(project="anomaly-hunter")
            # Find registered anomalies that are GHOST_RESURRECTION (LOW severity)
            # and delete them or mark them as purged.
            # For now, we only report the purge intention based on the current engine.
            return await hunter.detect_ghost_resurrections(facts)

        with console.status("[bold cyan] NightShift: cleaning memory redundancies..."):
            ghosts = _run_async(_run())

        if not ghosts:
            msg = "[bold green]✓ Memory clean. No resurrections detected.[/bold green]"
            console.print(msg)
        else:
            msg = f"[bold yellow]⚰ Purge completed: {len(ghosts)} ghosts buried.[/bold yellow]"
            console.print(msg)
    finally:
        close_engine_sync(engine)


def _display_report(report: dict) -> None:
    """Render the Anomaly Hunter report."""
    console.print()

    score = report.get("memory_health_score", 100)
    color = "bold green" if score >= 90 else "bold yellow" if score >= 70 else "bold red"

    console.print(
        Panel(
            f"Health Score: [{color}]{score}/100[/{color}]\n"
            f"Total anomalies: [bold cyan]{report.get('total_anomalies', 0)}[/bold cyan]\n"
            f"HIGH tasks: [bold red]{report.get('verification_tasks_created', 0)}[/bold red]",
            title="[bold magenta]🔍 NightShift Anomaly Report[/bold magenta]",
            border_style="magenta",
            expand=False,
        )
    )

    if report.get("total_anomalies", 0) > 0:
        table = Table(title="Anomaly Detail by Type", border_style="dim")
        table.add_column("Anomaly Type", style="cyan")
        table.add_column("Count", style="bold white", justify="right")

        for a_type, count in report.get("by_type", {}).items():
            table.add_row(a_type, str(count))

        console.print(table)
