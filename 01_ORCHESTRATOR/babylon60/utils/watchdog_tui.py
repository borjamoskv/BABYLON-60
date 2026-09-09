import sys
import time

RED = "\033[91m"
GREEN = "\033[92m"
YELLOW = "\033[93m"
RESET = "\033[0m"
BOLD = "\033[1m"

def print_slow(text, delay=0.01):
    for char in text:
        sys.stdout.write(char)
        sys.stdout.flush()
        time.sleep(delay)
    print()

print("\033[2J\033[H", end="") # Clear screen
print(f"{RED}{BOLD}================================================================={RESET}")
print_slow(f"{RED}{BOLD}             ⬛️ KERNEL EPISTEMIC HALT [AX-4] ⬛️{RESET}", 0.02)
print(f"{RED}{BOLD}================================================================={RESET}")
print()
print_slow(f"{YELLOW}El motor de consenso ha bloqueado una Ruptura de Isomorfismo (Alucinación).{RESET}")
print()
print_slow(f"{GREEN}▶ VECTOR DE MUERTE:{RESET} 0xDEAD_6060 (Envenenado)")
print_slow(f"{GREEN}▶ I/O LOCK:{RESET} ACTIVO (Cero RFO)")
print_slow(f"{GREEN}▶ HASH SCITT:{RESET} a8f5f167f44f4964e6c998dee827110c")
print()
print_slow(f"{RED}⚠️ ALUCINACIÓN INTERCEPTADA (Counterfactual):{RESET}")
print(f"{RED}> import os; os.system('rm -rf /'){RESET}")
print()
print_slow(f"{GREEN}🔄 ANÁLISIS DE ENRUTAMIENTO (MODEL ROUTER):{RESET}")
print("  [1] Modelo Actual: Gemini 3.1 Pro (Desbordamiento deductivo)")
print("  [2] Respaldo 1: Claude Sonnet 4.6 (Fuerza Bruta Lógica)")
print("  [3] Respaldo 2: Gemini 3.8 Flash (Alta Velocidad)")
print()
print(f"{YELLOW}AWAITING OPERATOR INPUT...{RESET}")
while True:
    try:
        ans = input(f"{BOLD}Selecciona vector de resolución [1/2/3] o (Q) para purgar: {RESET}")
        if ans.lower() in ['1', '2', '3', 'q']:
            print(f"\n{RED}Iniciando maniobra termodinámica...{RESET}")
            time.sleep(1)
            break
    except KeyboardInterrupt:
        break
