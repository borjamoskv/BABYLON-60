# C5-REAL EXERGY CERTIFIED
"""Cognitive Compaction CLI Commands."""
import click
from babylon60.cli.common import cli, console
from babylon60.memory.compactor import CognitiveCompactor

@cli.command(name="memory-compact")
@click.option("--dry-run", is_flag=True, help="Simulate compaction without mutating disk.")
@click.option("--threshold", default=10000, help="Token threshold before triggering compaction.")
def memory_compact(dry_run: bool, threshold: int):
    """Ejecutar poda de entropía (ZERO-DIOGENES)."""
    console.print("--- [bold magenta]C5-REAL COGNITIVE COMPACTOR (Ω16)[/bold magenta] ---")
    compactor = CognitiveCompactor(threshold_tokens=threshold)

    console.print(f"[dim]■ Analizando entropía semántica... Umbral: {threshold} tokens[/dim]")
    entropy = compactor.analyze_entropy()

    if entropy["is_critical"]:
        console.print(f"[bold red]■ [WARNING] Síndrome de Diógenes Semántico detectado: {entropy['current_tokens']} tokens.[/bold red]")
    else:
        console.print(f"[bold green]■ Entropía estable: {entropy['current_tokens']} tokens.[/bold green]")

    result = compactor.compact(dry_run=dry_run)

    if result["status"] == "DRY_RUN":
        console.print("[yellow]■ [DRY-RUN] Proyección de Poda Termodinámica:[/yellow]")
        console.print(f"  ├─ Deltas Extraídos a Estado Físico: {result['deltas_extracted']}")
        console.print(f"  └─ Tokens (Anergía) a Purgar: {result['tokens_purged']}")
    elif result["status"] == "COMPACTED":
        console.print("[bold green]■ [ACK] Colapso de Función de Onda Completado.[/bold green]")
        console.print(f"  ├─ Deltas Físicos Inyectados: {result['deltas_extracted']}")
        console.print(f"  └─ Tokens Purgados: {result['tokens_purged']}")
    else:
        console.print(f"[dim]■ Abortando: {result['msg']}[/dim]")
