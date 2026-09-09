#!/usr/bin/env python3

import os
import sys
import time
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.syntax import Syntax
from rich.live import Live
from rich.text import Text
from c5_transduction_engine import DirectorAgent, MultimodalTransducer, Orchestrator

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
        Layout(name="json_matrix"),
        Layout(name="dag_matrix", size=8)
    )
    return layout

def main():
    API_KEY = os.environ.get("GEMINI_API_KEY")
    if not API_KEY:
        console.print("[red]Fricción termodinámica detectada: Variable de entorno GEMINI_API_KEY no definida.[/red]")
        sys.exit(1)

    corpus_ejemplo = "La memoria del agua es un mito refutado, pero en dinámica de fluidos cuánticos observamos efectos de memoria a corto plazo en vórtices."
    override_metadata = "GLOBAL_STYLE_VECTOR: Renderizado de microscopio electrónico, blanco y negro puro, texturas ruidosas, científico."

    layout = generate_layout()
    layout["header"].update(Panel(Text("TENSOR DE TRANSDUCCIÓN | MOTOR POPPERIANO (C5-REAL)", justify="center", style="bold cyan")))
    layout["corpus"].update(Panel(corpus_ejemplo, title="[yellow]1. Corpus Ingresado (Territorio)[/yellow]"))
    layout["json_matrix"].update(Panel("Minimizando Divergencia KL... (Esperando a Gemini)", title="[green]2. Colapso Estructural (JSON)[/green]"))
    layout["dag_matrix"].update(Panel("En espera de fotogramas...", title="[magenta]3. Grafo Acíclico FFmpeg (DAG)[/magenta]"))

    with Live(layout, refresh_per_second=4, screen=True) as live:
        director = DirectorAgent(api_key=API_KEY)
        transducer = MultimodalTransducer()
        
        # Ocultar temporalmente el logging estricto para no romper la UI
        import logging
        logging.getLogger().setLevel(logging.CRITICAL)

        try:
            # 1. Llamada al LLM
            storyboard = director.extract_invariants(corpus_ejemplo, override_metadata)
            json_str = storyboard.model_dump_json(indent=2)
            syntax = Syntax(json_str, "json", theme="monokai", line_numbers=True)
            layout["json_matrix"].update(Panel(syntax, title="[green]2. Colapso Estructural (JSON)[/green]"))
            live.refresh()
            
            # 2. Transducción
            v_paths, a_paths = [], []
            out_dir = "/tmp/c5_render"
            os.makedirs(out_dir, exist_ok=True)
            
            for scene in storyboard.scenes:
                v, a = transducer.render_scene(scene, storyboard.global_style_vector, out_dir)
                v_paths.append(v)
                a_paths.append(a)
                
            # 3. Construir String del DAG para visualizarlo
            filter_complex = ""
            for i, scene in enumerate(storyboard.scenes):
                dur = float(scene.duration_sec)
                filter_complex += f"[{i*2}:v]trim={dur},setpts=PTS-STARTPTS[v{i}]; "
                filter_complex += f"[{i*2+1}:a]atrim={dur},asetpts=PTS-STARTPTS[a{i}]; "
            
            filter_text = Text(filter_complex, style="bold red")
            layout["dag_matrix"].update(Panel(filter_text, title="[magenta]3. Grafo Acíclico FFmpeg (DAG)[/magenta]"))
            live.refresh()
            
            # Mantener la UI abierta 10 segundos para admirar el resultado
            time.sleep(10)
            
        except Exception as e:
            layout["main"].update(Panel(f"[red]Error Crítico: {e}[/red]"))
            live.refresh()
            time.sleep(5)

if __name__ == "__main__":
    main()
