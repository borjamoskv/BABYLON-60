#!/usr/bin/env python3
import sys
import time
import json
import random
import threading
import os
import signal

STATE_FILE = ".cortex/topology_state.json"

# ANSI Colors & Control
C_RESET = "\033[0m"
C_BOLD = "\033[1m"
C_RED = "\033[91m"
C_BLUE = "\033[94m"
C_CYAN = "\033[96m"
C_GREEN = "\033[92m"

ALT_SCREEN_ON = "\033[?1049h"
ALT_SCREEN_OFF = "\033[?1049l"
CURSOR_HIDE = "\033[?25l"
CURSOR_SHOW = "\033[?25h"
CURSOR_HOME = "\033[H"
CLEAR_SCREEN = "\033[2J"

def simulate_swarm():
    os.makedirs(os.path.dirname(STATE_FILE), exist_ok=True)
    models = [
        ("Gemini 3.8 Flash", "Low", "tau_fast", C_BLUE),
        ("Gemini 3.1 Pro", "High", "tau_slow", C_RED),
        ("GPT-OSS 120B", "Medium", "tau_med", C_CYAN)
    ]
    
    while True:
        active_workers = random.randint(1, 15)
        dominant_model = random.choice(models)
        brake_active = random.random() > 0.9 
        
        if brake_active:
            dominant_model = ("Claude Opus 4.6", "High", "tau_max", C_RED)
            active_workers = 1 
            
        state = {
            "topology": {
                "active_model": dominant_model[0],
                "regime": dominant_model[1],
                "thermodynamic_state": dominant_model[2],
                "epistemic_brake": brake_active,
                "color_code": dominant_model[3],
                "active_swarm_workers": active_workers,
                "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
            }
        }
        with open(STATE_FILE, "w") as f:
            json.dump(state, f)
        time.sleep(1.5)

def cleanup(signum=None, frame=None):
    sys.stdout.write(ALT_SCREEN_OFF + CURSOR_SHOW)
    sys.stdout.flush()
    if signum:
        sys.exit(0)

def render_tui():
    sys.stdout.write(ALT_SCREEN_ON + CURSOR_HIDE)
    sys.stdout.flush()
    signal.signal(signal.SIGINT, cleanup)
    signal.signal(signal.SIGTERM, cleanup)
    
    while True:
        try:
            with open(STATE_FILE, "r") as f:
                data = json.load(f).get("topology", {})
                
            model = data.get("active_model", "N/A")
            regime = data.get("regime", "N/A")
            tau = data.get("thermodynamic_state", "N/A")
            brake = data.get("epistemic_brake", False)
            workers = data.get("active_swarm_workers", 0)
            c = data.get("color_code", C_RESET)
            
            # Reposicionar el cursor al inicio sin hacer scrollback
            sys.stdout.write(CURSOR_HOME + CLEAR_SCREEN)
            
            out = f"{C_BOLD}{C_CYAN}=== CORTEX-TOP v3: MONITOR DE EXERGÍA (ALT-SCREEN) ==={C_RESET}\n\n"
            out += f"  MODELO DOMINANTE : {c}{C_BOLD}{model}{C_RESET}\n"
            out += f"  RÉGIMEN ASIGNADO : {c}{regime}{C_RESET}\n"
            out += f"  DISIPACIÓN (tau) : {c}{tau}{C_RESET}\n"
            out += f"  WORKERS (Swarm)  : {C_BOLD}{workers} hilos concurrentes{C_RESET}\n\n"
            
            if brake:
                out += f"  {C_BOLD}{C_RED}[ ⚠ FRENO EPISTÉMICO ACTIVADO: Mutación Crítica en Progreso ]{C_RESET}\n"
            else:
                out += f"  {C_GREEN}[ ✓ Flujo Estocástico Libre ]{C_RESET}\n"
                
            out += f"\n{C_BOLD}(Ctrl+C para salir){C_RESET}\n"
            
            sys.stdout.write(out)
            sys.stdout.flush()
            
        except Exception:
            sys.stdout.write(CURSOR_HOME + CLEAR_SCREEN + "Esperando sincronización del Causal Ledger...\n")
            sys.stdout.flush()
            
        time.sleep(0.1)

if __name__ == "__main__":
    t = threading.Thread(target=simulate_swarm, daemon=True)
    t.start()
    
    try:
        if sys.stdout.isatty():
            render_tui()
        else:
            print("Headless mode.")
            while True: time.sleep(1)
    except KeyboardInterrupt:
        pass
    finally:
        cleanup()
