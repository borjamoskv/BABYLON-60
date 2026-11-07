#!/usr/bin/env python3
import curses
import json
import time
import os
import threading
import random

STATE_FILE = ".cortex/topology_state.json"
_STOP_EVENT = threading.Event()

def simulate_dynamic_routing() -> None:
    """Simulates the Swarm Router dynamically changing the topology."""
    models = [
        {"active_model": "Gemini 3.8 Flash", "regime": "Low", "thermodynamic_state": "tau_fast", "color": "BLUE"},
        {"active_model": "Gemini 3.1 Pro", "regime": "High", "thermodynamic_state": "tau_slow", "color": "RED"}
    ]
    while not _STOP_EVENT.is_set():
        m = random.choice(models)
        state = {
            "topology": {
                "active_model": m["active_model"],
                "regime": m["regime"],
                "thermodynamic_state": m["thermodynamic_state"],
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
                "epistemic_brake_enabled": True,
                "color": m["color"]
            }
        }
        os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
        time.sleep(2.5)

def main(stdscr: curses.window) -> None:
    curses.curs_set(0)
    stdscr.nodelay(True)
    
    curses.start_color()
    curses.init_pair(1, curses.COLOR_CYAN, curses.COLOR_BLACK)
    curses.init_pair(2, curses.COLOR_RED, curses.COLOR_BLACK)
    curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_BLACK)

    # Start simulation thread
    t = threading.Thread(target=simulate_dynamic_routing, daemon=True)
    t.start()

    while not _STOP_EVENT.is_set():
        stdscr.clear()
        stdscr.addstr(1, 2, "=== CORTEX-TOP: MONITOR DE EXERGÍA (TUI) ===", curses.A_BOLD)
        
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f)["topology"]
                
            model = data.get("active_model", "UNKNOWN")
            regime = data.get("regime", "UNKNOWN")
            tau = data.get("thermodynamic_state", "UNKNOWN")
            brake = data.get("epistemic_brake_enabled", False)
            color_str = data.get("color", "BLUE")
            
            color = curses.color_pair(2) if color_str == "RED" else curses.color_pair(1)
            
            stdscr.addstr(3, 2, f"MODELO ACTIVO : {model} ", color | curses.A_BOLD)
            stdscr.addstr(4, 2, f"RÉGIMEN       : {regime} ", color)
            stdscr.addstr(5, 2, f"DISIPACIÓN    : {tau} ", color)
            
            brake_color = curses.color_pair(3) if brake else curses.color_pair(2)
            stdscr.addstr(7, 2, f"FRENO EPISTÉMICO: {'ACTIVADO' if brake else 'INACTIVO'}", brake_color)
            
            stdscr.addstr(9, 2, "Presione 'q' para salir. Simulando saltos termodinámicos...")
            
        except Exception as e:
            stdscr.addstr(3, 2, f"Esperando sincronización del Ledger... {e}")
            
        stdscr.refresh()
        
        c = stdscr.getch()
        if c == ord('q'):
            break
        time.sleep(0.1)

if __name__ == "__main__":
    curses.wrapper(main)
