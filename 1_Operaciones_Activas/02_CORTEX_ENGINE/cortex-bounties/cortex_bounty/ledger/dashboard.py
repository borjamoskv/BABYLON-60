"""
LEDGER — Rich Terminal Dashboard

Pipeline funnel, hit rate, P&L, active hunts — all in the terminal.
"""
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.columns import Columns
from rich.text import Text

from cortex_bounty.ledger.db import BountyDB


def render_dashboard(db: BountyDB):
    """Render the full portfolio dashboard."""
    console = Console()
    stats = db.get_stats()
    pipeline = db.get_pipeline()

    # ─── Header ─────────────────────────────────────────
    console.print()
    console.print(Panel(
        "[bold white]CORTEX-BOUNTY · SOVEREIGN PORTFOLIO[/bold white]",
        style="blue", width=70
    ))

    # ─── Stats Cards ────────────────────────────────────
    cards = [
        Panel(
            f"[bold green]${stats['total_payout_usd']:,.0f}[/bold green]\n[dim]Total Payout[/dim]",
            width=20, style="green"
        ),
        Panel(
            f"[bold cyan]{stats['hit_rate']:.1f}%[/bold cyan]\n[dim]Hit Rate[/dim]",
            width=20, style="cyan"
        ),
        Panel(
            f"[bold yellow]${stats['hourly_rate_usd']:,.0f}/hr[/bold yellow]\n[dim]Hourly Rate[/dim]",
            width=20, style="yellow"
        ),
    ]
    console.print(Columns(cards, equal=True, expand=True))

    # ─── Pipeline Funnel ────────────────────────────────
    funnel_table = Table(title="Pipeline Funnel", show_header=True)
    funnel_table.add_column("Stage", style="bold")
    funnel_table.add_column("Count", justify="right")
    funnel_table.add_column("Bar")

    max_count = max(pipeline.values()) if pipeline.values() else 1
    stages = ["scouting", "analyzing", "writing", "submitted", "accepted", "paid", "rejected"]
    colors = ["blue", "cyan", "yellow", "magenta", "green", "bold green", "red"]

    for stage, color in zip(stages, colors):
        count = pipeline.get(stage, 0)
        bar_len = int((count / max_count) * 30) if max_count > 0 else 0
        bar = "█" * bar_len
        funnel_table.add_row(
            stage.upper(),
            str(count),
            Text(bar, style=color),
        )

    console.print(funnel_table)

    # ─── Active Hunts ───────────────────────────────────
    active_hunts = db.get_hunts()
    if active_hunts:
        hunt_table = Table(title="Recent Hunts", show_header=True)
        hunt_table.add_column("ID", style="dim")
        hunt_table.add_column("Platform", style="magenta")
        hunt_table.add_column("Target", style="cyan")
        hunt_table.add_column("Status")
        hunt_table.add_column("Hours", justify="right")
        hunt_table.add_column("Max Payout", justify="right", style="green")

        for h in active_hunts[:15]:
            status_style = {
                "scouting": "blue", "analyzing": "cyan",
                "writing": "yellow", "submitted": "magenta",
                "accepted": "green", "paid": "bold green",
                "rejected": "red",
            }.get(h["status"], "dim")

            hunt_table.add_row(
                h["id"],
                h["platform"],
                h["target"][:30],
                Text(h["status"].upper(), style=status_style),
                f"{h['hours_spent']:.1f}",
                f"${h['max_payout']:,.0f}" if h["max_payout"] else "—",
            )
        console.print(hunt_table)

    # ─── Recent Submissions ─────────────────────────────
    subs = db.get_submissions()
    if subs:
        sub_table = Table(title="Recent Submissions", show_header=True)
        sub_table.add_column("ID", style="dim")
        sub_table.add_column("Title", style="cyan")
        sub_table.add_column("Severity")
        sub_table.add_column("Status")
        sub_table.add_column("Payout", justify="right", style="green")

        for s in subs[:10]:
            sev_style = {"critical": "bold red", "high": "red", "medium": "yellow"}.get(s["severity"], "dim")
            sub_table.add_row(
                s["id"],
                s["title"][:40],
                Text(s["severity"].upper(), style=sev_style),
                s["status"],
                f"${s['payout_usd']:,.0f}" if s["payout_usd"] else "—",
            )
        console.print(sub_table)

    console.print()


def main():
    db = BountyDB()
    try:
        render_dashboard(db)
    finally:
        db.close()


if __name__ == "__main__":
    main()
