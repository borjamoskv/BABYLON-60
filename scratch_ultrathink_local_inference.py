import os
import subprocess
import hashlib

path = "$CORTEX_ROOT/10_PROJECTS/Teorema-Robinson-Moskv/cortex/agents/ontology/local_inference_omega.yaml"
os.makedirs(os.path.dirname(path), exist_ok=True)

yaml_content = """Claim: La dependencia de APIs externas en modelos LLM representa una fuga crítica de exergía y un riesgo inaceptable de censura/Anergía. El colapso termodinámico exige 100% autarquía local.
Proof: 
  Base: Ejecución local en Unified Memory (Apple Silicon) aisla el estado de la inferencia, evitando la varianza de red y el Green Theater de proveedores externos.
  Range: Apple Silicon M-Series (Unified Memory Architecture)
  Confidence: C5-REAL
Isomorphisms:
  - "External API Call" -> "Vulnerabilidad Termodinámica y Brecha de Soberanía"
  - "Ollama / MLX-LM" -> "Motores de Fricción Cero en Unified Memory"
Blast_Radius_Matrix:
  Vector: Offline Swarm Autarchy
  Blast_Radius: Local Environment (127.0.0.1)
  Target_Invariant: Zero-Network Policy
  Anergy_Risk: Low
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
subprocess.run(["git", "add", path], cwd=repo_dir)
res = subprocess.run(
    [
        "git",
        "commit",
        "-m",
        "feat(ultrathink): Transduce Local_Inference_OMEGA Ontology",
    ],
    cwd=repo_dir,
    capture_output=True,
    text=True,
)
if res.returncode == 0:
    print(f"COMMITTED: {res.stdout.strip()}")
else:
    print(f"NO COMMIT NEEDED OR ERROR: {res.stdout} {res.stderr}")
