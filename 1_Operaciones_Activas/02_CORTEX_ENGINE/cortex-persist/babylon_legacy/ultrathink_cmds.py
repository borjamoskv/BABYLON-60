# C5-REAL EXERGY CERTIFIED
from babylon60.cli.common import cli, console
import click
import subprocess

@cli.command(name="ultrathink")
def ultrathink():
    """Inicia el scheduler de Ultrathink dentro de BABYLON-60."""
    console.print("[bold cyan]🚀 Starting Ultrathink scheduler…[/]")
    subprocess.run([
        "python3",
        "1_Operaciones_Activas/02_CORTEX_ENGINE/BABYLON-60/ultrathink/ultrathink_scheduler.py"
    ], check=True)
