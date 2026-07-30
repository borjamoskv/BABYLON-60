from pathlib import Path

import click
from rich.table import Table

from babylon60.cli.common import cli, console
from babylon60.engine.macrofago_ontologico import OntologicalMacrophage


@cli.command("ouroboros")
@click.option("--path", default=".", help="Ruta de exploración para el Macrófago.")
@click.option("--dry-run", is_flag=True, help="Ejecutar análisis sin purga termodinámica.")
@click.option(
    "--annihilate", is_flag=True, help="Purga forzosa OP_ANNIHILATE si se detecta entropía."
)
def ouroboros(path: str, dry_run: bool, annihilate: bool):
    """
    Invoca al Macrófago Ontológico (OP_OUROBOROS_INIT).
    Escanea la base de código buscando desviaciones de la Ontología CORTEX.
    """
    console.print(
        f"[bold red]\\[OP_OUROBOROS_INIT][/bold red] Iniciando escaneo C5-REAL en: {path}"
    )

    root_dir = Path(path).resolve()
    macrophage = OntologicalMacrophage(root_dir)
    report = macrophage.scan()

    console.print(
        f"Archivos analizados: [bold]{report.total_files_scanned}[/bold] | LOC Total: [bold]{report.total_loc}[/bold]"
    )

    if report.violations:
        table = Table(title="Anomalías Termodinámicas Detectadas")
        table.add_column("Archivo", style="cyan")
        table.add_column("Línea", justify="right", style="magenta")
        table.add_column("Violación", style="red")
        table.add_column("Descripción")

        # Limitar la salida a las primeras 50 para no inundar el terminal
        for i, v in enumerate(report.violations):
            if i >= 50:
                table.add_row("...", "...", "...", f"...y {len(report.violations) - 50} más")
                break
            table.add_row(v.file_path, str(v.line_number), v.violation_type, v.description)

        console.print(table)
    else:
        console.print(
            "[bold green]Zero Anergia. El sistema está alineado con la Matriz 135.[/bold green]"
        )

    if report.is_compromised:
        if annihilate and not dry_run:
            console.print("[bold red]Ejecutando OP_ANNIHILATE...[/bold red]")
            macrophage.annihilate(report)
        else:
            console.print(
                "[yellow]Modo Dry-Run o falta flag --annihilate. La entropía persiste en disco.[/yellow]"
            )
