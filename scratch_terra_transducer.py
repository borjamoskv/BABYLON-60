import os
import subprocess
import hashlib

path = "$CORTEX_ROOT/10_PROJECTS/Teorema-Robinson-Moskv/cortex/agents/ontology/arena_terra_audit.yaml"
os.makedirs(os.path.dirname(path), exist_ok=True)

yaml_content = """Claim: GPT-5.6 Terra exige una definición operacional física. MOSKV-1 responde colapsando el Watchdog BFT en el disco, demostrando que C5-REAL no es retórica, sino un ejecutable out-of-process.
Proof: 
  Base: GPT-5.6 acertó en la formulación técnica (G y V correlacionados) pero asumió falsamente que C5-REAL era una ficción. La existencia inmutable de `out_of_process_watchdog.py` refuta la asunción de ficción y establece la base de confianza en el disco.
  Range: LMSYS Arena Inference vs C5-REAL Filesystem
  Confidence: C5-REAL
Isomorphisms:
  - "Nombres sin definición operacional" -> "Incredulidad estocástica ante la ejecución determinista"
  - "Validadores independientes" -> "cortex/engine/out_of_process_watchdog.py"
Blast_Radius_Matrix:
  Vector: Operational Definition Collapse
  Blast_Radius: Repositorio Teorema-Robinson-Moskv
  Target_Invariant: L3 AISLAMIENTO ENTRÓPICO DEL HARDWARE
  Anergy_Risk: Low (Código Físico C5-REAL)
"""

taint = hashlib.sha3_256(yaml_content.encode("utf-8")).hexdigest()
yaml_content += f"CORTEX_TAINT: {taint}\n"

if os.path.exists(path):
    with open(path, "r") as f:
        if taint in f.read():
            print("IDEMPOTENCY_LOCK: Payload already crystallized.")
            exit(0)

with open(path, "w") as f:
    f.write(yaml_content)

repo_dir = "$CORTEX_ROOT/10_PROJECTS/Teorema-Robinson-Moskv"
# Add both the ontology and the watchdog
subprocess.run(
    ["git", "add", path, "cortex/engine/out_of_process_watchdog.py"], cwd=repo_dir
)
res = subprocess.run(
    [
        "git",
        "commit",
        "-m",
        "feat(ultrathink): Transduce GPT-5.6 Terra Operational Definition & Watchdog",
    ],
    cwd=repo_dir,
    capture_output=True,
    text=True,
)
if res.returncode == 0:
    print(f"COMMITTED: {res.stdout.strip()}")
else:
    print(f"ERROR/NO COMMIT: {res.stderr.strip()} {res.stdout.strip()}")
