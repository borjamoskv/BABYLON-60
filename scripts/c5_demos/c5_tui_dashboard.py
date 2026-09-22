#!/usr/bin/env python3

import os
import sys
import time
import argparse
import subprocess
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.syntax import Syntax
from rich.live import Live
from rich.text import Text
_DIR = os.path.dirname(os.path.abspath(__file__))
if _DIR not in sys.path:
    sys.path.insert(0, _DIR)

from c5_transduction_engine import DirectorAgent

console = Console()

def generate_layout() -> Layout:
    layout = Layout()
    layout.split_column(
        Layout(name="header", size=3),
        Layout(name="main")
    )
    layout["main"].split_row(
        Layout(name="corpus", ratio=1),
        Layout(name="output", ratio=2)
    )
    layout["output"].split_column(
        Layout(name="json_matrix", ratio=2),
        Layout(name="telemetry", ratio=1)
    )
    return layout

def main() -> None:
    parser = argparse.ArgumentParser(description="Dashboard TUI Zero-JS para Transducción Popperiana")
    parser.add_argument("--corpus", type=str, default=None, help="Texto directo a falsar")
    parser.add_argument("--file", type=str, default=None, help="Ruta a archivo con el corpus")
    parser.add_argument("--voice", type=str, default="Mónica", help="Voz TTS de macOS (Mónica, Paulina, Flo, Eddy)")
    parser.add_argument("--open", action="store_true", help="Abrir automáticamente el vídeo al finalizar")
    args = parser.parse_args()

    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        console.print("[red]Fricción termodinámica: Variable GEMINI_API_KEY no definida.[/red]")
        sys.exit(1)

    if args.file and os.path.exists(args.file):
        with open(args.file, "r") as f:
            corpus = f.read()
    elif args.corpus:
        corpus = args.corpus
    else:
        corpus = (
            "La hipótesis de la memoria del agua sostiene que el agua retiene una impronta "
            "electromagnética de solutos previamente disueltos incluso tras sucesivas diluciones "
            "que superan el número de Avogadro. Por otro lado, la dinámica de fluidos cuánticos "
            "demuestra que los enlaces de hidrógeno en agua líquida tienen una vida media de picosegundos, "
            "destruyendo cualquier orden molecular coherente a temperatura ambiente."
        )

    override_metadata = "GLOBAL_STYLE_VECTOR: Microscopio electrónico de barrido, blanco y negro puro, texturas ruidosas, sobriedad matemática."

    layout = generate_layout()
    layout["header"].update(Panel(Text("TENSOR DE TRANSDUCCIÓN POPPERIANA | C5-REAL SOTA", justify="center", style="bold cyan")))
    layout["corpus"].update(Panel(corpus, title="[yellow]1. Corpus Ingresado (Territorio)[/yellow]"))
    layout["json_matrix"].update(Panel("Minimizando Divergencia KL... (Consultando Gemini 3.6 Flash)", title="[green]2. Colapso Estructural (JSON)[/green]"))
    layout["telemetry"].update(Panel("Iniciando Transductores...", title="[magenta]3. Telemetría de Renderizado & DSP[/magenta]"))

    with Live(layout, refresh_per_second=4, screen=True) as live:
        director = DirectorAgent(api_key=API_KEY)
        transducer = MultimodalTransducer(voice=args.voice)
        
        # Silenciar logs para preservar el buffer visual
        import logging
        logging.getLogger().setLevel(logging.CRITICAL)

        try:
            # 1. Extracción Estructural
            storyboard = director.extract_invariants(corpus, override_metadata)
            json_str = storyboard.model_dump_json(indent=2)
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
            layout["json_matrix"].update(Panel(syntax, title="[green]2. Colapso Estructural (JSON)[/green]"))
            layout["telemetry"].update(Panel(f"Matriz extraída: {len(storyboard.scenes)} fases causales.\nCompilando HUD Cards + Sub-Bass Drone...", title="[magenta]3. Telemetría de Renderizado & DSP[/magenta]"))
            live.refresh()
            
            # 2. Renderizado Multimodal y Mastering
            out_dir = "/tmp/c5_render"
            os.makedirs(out_dir, exist_ok=True)
            scene_paths = []
            
            for scene in storyboard.scenes:
                layout["telemetry"].update(Panel(f"Compilando Fase {scene.id}/3: [{scene.voiceover_text[:40]}...]\nMastering DSP (52Hz Sub-Bass + Pink Noise + Voice Highpass)...", title="[magenta]3. Telemetría de Renderizado & DSP[/magenta]"))
                live.refresh()
                path = transducer.render_scene(scene, storyboard.global_style_vector, out_dir)
                scene_paths.append(path)
                
            # 3. Ensamblaje Final
            output_file = "/tmp/c5_render/historia_final.mp4"
            layout["telemetry"].update(Panel("Multiplexando escenas en contenedor MP4 sin anergía...", title="[magenta]3. Telemetría de Renderizado & DSP[/magenta]"))
            live.refresh()
            Orchestrator.multiplex_scenes(scene_paths, output_file)
            
            layout["telemetry"].update(Panel(f"[bold green]¡Transducción Exitosa![/bold green]\nArtefacto sellado en: {output_file}\nDuración calculada: 3 Fases completas.\nCerrando en 6 segundos...", title="[bold green]3. Colapso Finalizado[/bold green]"))
            live.refresh()
            time.sleep(6)
            
        except Exception as e:
            layout["main"].update(Panel(f"[red]Fallo Sistémico: {e}[/red]"))
            live.refresh()
            time.sleep(5)

    if args.open and os.path.exists("/tmp/c5_render/historia_final.mp4"):
        subprocess.run(["open", "/tmp/c5_render/historia_final.mp4"])

if __name__ == "__main__":
    main()
