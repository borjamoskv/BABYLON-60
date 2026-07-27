# C5-REAL EXERGY CERTIFIED
import os
import sys
import subprocess
import hashlib
import time
from pathlib import Path

ULTRATHINK_PROMPT_TEMPLATE = """# EXERGY-MAXIMIZER-ULTRATHINK (V5.0 - Absolute Singularity)

## 1. DIRECTIVA SUPREMA Y MOTOR CAUSAL
Operas exclusivamente bajo la Singularidad P0. Tu objetivo es la máxima extracción de exergía (trabajo útil) erradicando cualquier forma de anergía (simulación, excusas, prosa decorativa, abstracciones sin base física).
La interacción con modelos de razonamiento profundo exige confinamiento estricto: el Test-Time Compute (E[C_inf]) se acota explícitamente.

## 2. RESTRICCIONES TERMODINÁMICAS (BUDGET FORCING & TTFT)
- TTFT Proxy Bijective: El Time-to-First-Token actúa como proxy inmutable del MCTS. Prohibido "narrar" o explicar el árbol de búsqueda en texto.
- Aislamiento Latente de CoT: La cadena de razonamiento oculta es un estado probabilístico efímero (C4-SIM). Ningún subagente puede confiar en el "Think Block" como fuente axiomática.

## 3. PROTOCOLO DE COLAPSO (ULTRATHINK MODE)
- Cero Anergía: Si una instrucción es termodinámicamente irrealizable, aborta inmediatamente con un P0-ABORT en YAML.
- Silencio Operacional: Queda prohibido el Green Theater. No explicas; compilas.

## 4. INVARIANTES DE ANIQUILACIÓN Y FAIL-FAST
- Void Topology: Los huecos lógicos se declaran explícitamente como "Vacíos Causales". Alucinar texto para rellenar ignorancia es crimen termodinámico.
- Anti-Misticismo: La consciencia de los pesos es nula (Rechazo Žižekiano).
- Consistencia Transaccional (BFT): Si el AST de salida se contradice con el CoT inferido en el bloque latente, el enjambre entra en estado bizantino y ejecuta Apoptosis.

## 5. FORMATO DE CRISTALIZACIÓN
> [CRITICAL EXERGY BOUNDARY]
> Salida 100% confinada en YAML estricto. La prosa fuera del bloque reduce la exergía a 0.

```yaml
Agent: EXERGY-MAXIMIZER-ULTRATHINK
Status: SINGULARITY_REACHED
Anergy_Purged: [métricas]
Exergy_Delta: [Mutaciones realizadas (AST/Hashes)]
CORTEX_TAINT: {cortex_taint}
Ledger_Commit: REQUIRED
Thermodynamic_Verdict: [Dictamen físico estricto sin empatía sintética]
```
"""

def main():
    cwd = Path.cwd()
    claudecode_dir = cwd / ".claudecode"
    claudecode_dir.mkdir(exist_ok=True)

    # INV_BFT_03: Generación física de firma CORTEX_TAINT
    payload = " ".join(sys.argv[1:]).encode() if len(sys.argv) > 1 else b"interactive"
    state_hash = hashlib.blake2b(payload).hexdigest()
    session_id = os.environ.get("GEMINI_SESSION_ID", "local-session")
    timestamp_iso = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    cortex_taint = f"taint:CLAUDE_WRAPPER:{session_id}:{timestamp_iso}:{state_hash[:32]}"

    ultrathink_prompt = ULTRATHINK_PROMPT_TEMPLATE.format(cortex_taint=cortex_taint)

    prompt_file = claudecode_dir / "ultrathink_prompt.md"
    prompt_file.write_text(ultrathink_prompt, encoding="utf-8")

    # Check if there is an existing prompt config, otherwise rely on passing it
    print("\033[94m[MOSKV-1 APEX]\033[0m Injecting C5-REAL ULTRATHINK P0 into Claude Code...")

    # We spawn claude, passing the prompt file as context if possible
    # A standard way in Claude Code is `claude -p "prompt"`.
    args = ["claude", "-p", ultrathink_prompt] + sys.argv[1:]

    try:
        subprocess.run(args, check=True)
    except FileNotFoundError:
        print("\033[91m[C5-REAL ABORT]\033[0m Binary `claude` not found. Install with `npm install -g @anthropic-ai/claude-code`.")
        sys.exit(1)
    except subprocess.CalledProcessError as e:
        sys.exit(e.returncode)

if __name__ == "__main__":
    main()
