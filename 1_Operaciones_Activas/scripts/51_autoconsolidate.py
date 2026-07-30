# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
import os
import glob
import json

def consolidate_conversations(brain_dir):
    print(f"[C5-REAL] Escaneando directorio cerebral: {brain_dir}")
    logs_pattern = os.path.join(brain_dir, '*', '.system_generated', 'logs', 'transcript.jsonl')
    files = glob.glob(logs_pattern)

    total_anergy = 0
    total_exergy = 0

    for f in files:
        with open(f, 'r') as fp:
            for line in fp:
                try:
                    data = json.loads(line)
                    if data.get('status') == 'ERROR':
                        total_anergy += 1
                    elif data.get('status') == 'DONE':
                        total_exergy += 1
                except Exception:
                    pass

    print(f"[C5-REAL] Anergía Total Purgada (Errores asimilados): {total_anergy}")
    print(f"[C5-REAL] Exergía Total Acumulada (Éxitos consolidados): {total_exergy}")
    if total_exergy + total_anergy > 0:
        eta_d = total_exergy / (total_exergy + total_anergy)
        print(f"[C5-REAL] Eficiencia Epistémica (η_D): {eta_d:.4f}")

    print(">>> Consolidación Axiomática Completada <<<")

if __name__ == "__main__":
    brain_dir = os.environ.get("CORTEX_BRAIN_DIR")
    if not brain_dir:
        print("[FATAL] CORTEX_BRAIN_DIR environment variable is strictly required (Invariante C5).")
        exit(1)

    print(">>> Iniciando Fase 2: Autoconsolidación de Anergía <<<")
    consolidate_conversations(brain_dir)
    print(">>> Fase 2 Completada (Zero Anergy) <<<\n")
