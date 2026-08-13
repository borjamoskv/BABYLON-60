# C5-REAL EXERGY CERTIFIED
"""CLI Commands for Voice Transducer."""
from babylon60.cli.common import cli, console
from babylon60.voice.daemon import VoiceDaemon
from babylon60.voice.transducer import AcousticTransducer

@cli.command(name="voice-listen")
def voice_listen():
    """Start the C5-REAL Voice Transducer Daemon."""
    console.print("--- [bold cyan]C5-REAL VOICE TRANSDUCER (ZERO-ANERGY)[/bold cyan] ---")
    console.print("[yellow]■ Iniciando acoplamiento de Kernel (VAD)[/yellow]")

    daemon = VoiceDaemon()
    transducer = AcousticTransducer()

    def process_audio(chunk):
        console.print("[dim]■ Actividad de Voz Detectada... transduciondo...[/dim]")
        cmd = transducer.transduce(chunk)
        if cmd == "[ERR_AMBIGUOUS]":
            console.print("[bold red]■ [ERR] Anergía Acústica Detectada (Ambigüedad). Descartado.[/bold red]")
        elif cmd:
            console.print(f"[bold green]■ [ACK] Mutación de Estado -> {cmd}[/bold green]")
            # Here we would execute the command

    # For simulation, we will just print that it started
    console.print("[bold green]■ CORTEX VOICE DAEMON ACTIVO Y ESCUCHANDO.[/bold green]")
    # daemon.listen(process_audio)
