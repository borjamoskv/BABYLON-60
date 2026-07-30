import time
from rich.console import Console
from rich.layout import Layout
from rich.panel import Panel
from rich.live import Live
from rich.table import Table
from rich.text import Text

console = Console()

def generate_layout() -> Layout:
    layout = Layout()
    layout.split(
        Layout(name="header", size=3),
        Layout(ratio=1, name="main")
    )
    layout["main"].split_row(
        Layout(name="left", ratio=2),
        Layout(name="right", ratio=1)
    )
    return layout

def generate_status_table() -> Table:
    table = Table(title="Swarm Nodes (Apoptosis Monitor)")
    table.add_column("Node ID", justify="left", style="cyan")
    table.add_column("Status", justify="center", style="magenta")
    table.add_column("Entropy (bits/char)", justify="right", style="green")
    
    table.add_row("Patxi", "VERIFIED", "1.24")
    table.add_row("Ander", "VERIFIED", "2.10")
    table.add_row("Sergio_Diana_Node", "VERIFIED_CONSOLIDATED", "0.98")
    table.add_row("Iñaki Garcia", "PURGED", "0.00")
    return table

def generate_exergy_panel() -> Panel:
    text = Text("C5-REAL EXERGY TELEMETRY\n", style="bold blue")
    text.append("CPU Entropy: ", style="white")
    text.append("Optimal\n", style="bold green")
    text.append("Global Anergy: ", style="white")
    text.append("385 -> 0 (Purging)\n", style="bold red")
    return Panel(text, title="Thermodynamic Kernel")

def main():
    layout = generate_layout()
    layout["header"].update(Panel("MOSKV-1 APEX: Singular Dashboard", style="bold white on blue"))
    
    with Live(layout, refresh_per_second=4) as live:
        for _ in range(10): # Mocking a 10 tick dashboard lifecycle for testing
            layout["left"].update(Panel(generate_status_table(), border_style="cyan"))
            layout["right"].update(generate_exergy_panel())
            time.sleep(1)

if __name__ == "__main__":
    main()
