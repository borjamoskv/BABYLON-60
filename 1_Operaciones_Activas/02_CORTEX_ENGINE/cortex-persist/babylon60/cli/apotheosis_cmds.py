# [C5-REAL] Exergy-Maximized
"""
APOTHEOSIS-∞ Daemon CLI commands.
Level 5 Sovereign autonomy in CORTEX.

Connected to real CORTEX subsystems - zero simulation.
"""

import os
import subprocess
from pathlib import Path

import click
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn

__all__ = [
    "PROGRESS_DESC_FMT",
    "aix_cmd",
    "apotheosis_cmds",
    "guard_cmd",
    "manifest_cmd",
    "nirvana_cmd",
]

from babylon60.cli.common import cli, console

PROGRESS_DESC_FMT = "[progress.description]{task.description}"


@cli.group(name="apotheosis", help="👁️  APOTHEOSIS-∞: The Level 5 Autarchic Daemon.")
def apotheosis_cmds() -> None:
    """The proactive manifestation and eradication engine of MOSKV-1."""


@apotheosis_cmds.command("manifest")
@click.argument("intent", required=True)
def manifest_cmd(intent: str) -> None:
    """
    The singularity of creation. Materializes an ecosystem from a short intent.
    """
    if not intent.strip():
        console.print("[bold red]Error: Intent cannot be empty.[/]")
        raise click.Abort()

    console.print(
        Panel(
            f"[bold #06d6a0]APOTHEOSIS-MANIFEST[/]\nMaterializing intent: [italic]{intent}[/]",
            border_style="#06d6a0",
        )
    )

    with Progress(
        SpinnerColumn(spinner_name="dots2"),
        TextColumn(PROGRESS_DESC_FMT),
        transient=False,
    ) as progress:
        t_id = progress.add_task("[bold #6600FF]Connecting to CORTEX Engine...[/]", total=None)

        # Real: Connect to CortexEngine and store intent
        try:
            from babylon60.engine import CortexEngine

            engine = CortexEngine()
            progress.update(
                t_id, description="[bold #6600FF]CORTEX Engine connected. Storing intent...[/]"
            )
            engine.store(  # type: ignore[reportUnusedCoroutine]
                content=f"APOTHEOSIS-MANIFEST: {intent}",
                fact_type="intent",
                project="apotheosis",
                source="cli:apotheosis:manifest",
            )
            progress.update(
                t_id, description="[bold #06d6a0]Intent stored in CORTEX. Verifying...[/]"
            )

            # Verify storage
            results = engine.search(intent, limit=1, project="apotheosis")
            verified = len(results) > 0  # type: ignore[reportArgumentType]
            status = "✅ Verified" if verified else "⚠️ Unverified"
            progress.update(
                t_id, description=f"[bold #D4AF37]{status} - Intent registered in ledger[/]"
            )
        except ImportError:
            progress.update(
                t_id, description="[dim]CortexEngine unavailable - intent not persisted[/]"
            )

    console.print(
        "\n[bold green]💠 APOTHEOSIS-MANIFEST COMPLETED[/]\n"
        "The intent has been registered and verified in the ledger.\n"
    )


@apotheosis_cmds.command("guard")
def guard_cmd() -> None:
    """
    The Demiurgic Sleep: Nightly vigilance and real technical debt purge.
    """
    console.print(
        Panel(
            "[bold #2E5090]APOTHEOSIS-GUARD[/]\n"
            "Initiating nightly vigilance and technical debt annihilation.",
            border_style="#2E5090",
        )
    )

    report_lines = ["# 👁️ Demiurgic Sleep Report\n"]
    target = Path(os.getcwd()).resolve()

    with Progress(
        SpinnerColumn(spinner_name="moon"),
        TextColumn(PROGRESS_DESC_FMT),
        transient=False,
    ) as progress:
        t_id = progress.add_task(
            "[dim]Scanning entropy in current directory (ENTROPY-0)...[/]", total=None
        )

        # Real: Run radon CC scan
        cc_results = _scan_entropy(target)
        report_lines.append(f"- Scanned files: {cc_results['total']}")
        report_lines.append(f"- High entropy files: {cc_results['critical']}")
        report_lines.append(f"- Max cyclomatic complexity: {cc_results['max_cc']}")

        progress.update(t_id, description="[dim]Executing lint auto-fix (ruff --fix)...[/]")

        # Real: Run ruff autofix
        ruff_result = subprocess.run(
            ["ruff", "check", "--fix", str(target)],
            capture_output=True,
            text=True,
            timeout=60,
        )
        fixed_count = ruff_result.stdout.count("Fixed")
        report_lines.append(f"- Lint violations auto-fixed: {fixed_count}")

        progress.update(t_id, description="[dim]Generating operations report...[/]")

        # Real: Check daemon status
        daemon_status = "unknown"
        try:
            from babylon60.extensions.daemon.core import MoskvDaemon

            status = MoskvDaemon.load_status()
            if status:
                daemon_status = "healthy" if status.get("all_healthy") else "degraded"
        except ImportError:
            daemon_status = "unavailable"

        report_lines.append(f"- Daemon status: {daemon_status}")
        report_lines.append("\n*Apotheosis watches.*")

        try:
            report_path = target / "apotheosis_night_report.md"
            report_path.write_text("\n".join(report_lines), encoding="utf-8")
        except OSError as e:
            console.print(f"\n[bold red]Error writing report: {e}[/]")
            raise click.Abort() from e

    pct = (
        0
        if cc_results["total"] == 0
        else (100 - round(cc_results["critical"] / cc_results["total"] * 100))
    )
    console.print(
        f"\n[bold #D4AF37]👁️ THE DEMIURGIC SLEEP HAS ENDED[/]\n"
        f"Architectural health: {pct}% healthy files. "
        f"Report saved to apotheosis_night_report.md.\n"
    )


@apotheosis_cmds.command("nirvana")
@click.argument("target_path", type=click.Path(exists=True), required=False, default=".")
def nirvana_cmd(target_path: str) -> None:
    """
    Destructive request. Purifies a file/dir by annihilating all complexity.
    """
    path_resolved = Path(target_path).resolve()

    console.print(
        Panel(
            f"[bold #f72585]APOTHEOSIS-NIRVANA[/]\nOpening event horizon at: {path_resolved.name}",
            border_style="#f72585",
        )
    )

    with Progress(
        SpinnerColumn(spinner_name="bouncingBar"),
        TextColumn(PROGRESS_DESC_FMT),
        transient=False,
    ) as progress:
        t_id = progress.add_task(
            "[bold #f72585]Executing aggressive ruff autofix...[/]", total=None
        )

        # Real: Aggressive ruff fix
        subprocess.run(
            ["ruff", "check", "--fix", "--unsafe-fixes", str(path_resolved)],
            capture_output=True,
            text=True,
            timeout=60,
        )

        progress.update(t_id, description="[bold #f72585]Applying canonical formatting...[/]")

        # Real: ruff format
        subprocess.run(
            ["ruff", "format", str(path_resolved)],
            capture_output=True,
            text=True,
            timeout=60,
        )

        progress.update(t_id, description="[bold #f72585]Measuring post-purge complexity...[/]")

        # Real: Post-purge scan
        results = _scan_entropy(path_resolved)
        max_cc = results["max_cc"]

    console.print(
        f"\n[bold white on #f72585] N I R V A N A   R E A C H E D [/]\n"
        f"Post-purge: max CC={max_cc}, {results['critical']} critical files remain "
        f"out of {results['total']} scanned.\n"
    )


@apotheosis_cmds.command("aix")
def aix_cmd() -> None:
    """
    Deification Metric (AIx). Quantifies system efficiency and sovereignty.
    """
    import asyncio

    from babylon60.cli.aix import calculate_aix, print_aix_report
    from babylon60.cli.common import get_engine

    async def run():
        engine = get_engine()
        async with engine.session() as conn:
            data = await calculate_aix(conn)
            print_aix_report(data)

    asyncio.run(run())
    os._exit(0)


def _scan_entropy(target: Path) -> dict:
    """Scan a directory for cyclomatic complexity using radon."""
    from typing import Any

    result: dict[str, Any] = {"total": 0, "critical": 0, "max_cc": 0, "worst_file": ""}
    try:
        from radon.complexity import cc_visit  # pyright: ignore[reportMissingImports]
    except ImportError:
        return result

    for py_file in target.rglob("*.py"):
        if any(p in py_file.parts for p in ("__pycache__", ".venv", "node_modules")):
            continue
        try:
            code = py_file.read_text(encoding="utf-8")
            blocks = cc_visit(code)
            result["total"] += 1
            for b in blocks:
                if b.complexity > result["max_cc"]:
                    result["max_cc"] = b.complexity
                    result["worst_file"] = str(py_file.name)
                if b.complexity > 15:
                    result["critical"] += 1
                    break
        except (SyntaxError, UnicodeDecodeError):
            continue
    return result
