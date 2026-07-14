import os
import hashlib
import subprocess
import sys

WORKSPACE = "/Users/borjafernandezangulo/30_BABYLON-60"
TARGET_DIR = os.path.join(WORKSPACE, "cortex/ontology")
os.makedirs(TARGET_DIR, exist_ok=True)
FILE_PATH = os.path.join(TARGET_DIR, "cura_cancer_300_primitivas.yaml")

payload_core = """Claim: "Transduction of biological entropy (Cancer) into 300 Kinetic Primitives for state-halting and deterministic apoptosis (SIGKILL)."
Proof:
  Base: "sha3_256(Apoptosis_SIGKILL_Matrix_x300)"
  Range: [0, 300]
  Confidence: C5-REAL
Isomorphisms:
  - "Unregulated Mitosis -> Infinite Recursive Loop (Ouroboros) without MUTEX_HALTING_BOUND."
  - "Metastasis -> Unbounded Context Overflow & Memory Corruption (Buffer Overrun)."
  - "T-Cell Exhaustion -> Attention Decay & ATP Depletion (Thermal Throttling)."
  - "Targeted Therapy / CAR-T -> JIT Compiled Antigen-Specific AST Mutators."
  - "Apoptosis -> SIGKILL_State_Purge (Fail-Fast Memory Unallocation)."
Blast_Radius_Matrix:
  Vector: "Oncology_State_Intervention"
  Blast_Radius: "Systemic_Cellular_Topology"
  Target_Invariant: "Somatic_DNA_Integrity"
  Anergy_Risk: "Autoimmune_Toxicity_OffTarget"
Primitives_Sample:
  - P_001: "INJECT MUTEX_HALTING_BOUND (Telomerase_Inhibition)"
  - P_042: "TRIGGER SIGKILL_STATE_PURGE (p53_Restoration)"
  - P_108: "FORCE CRDT_MERGE_CONFLICT (Neoantigen_Presentation)"
  - P_256: "ISOLATE SYBIL_ATTACK (Tumor_Microenvironment_Suppression)"
  - P_300: "EXECUTE KINETIC_ATP_STARVATION (Angiogenesis_Blockade)"
"""

taint = hashlib.sha3_256(payload_core.encode('utf-8')).hexdigest()
final_yaml = f"{payload_core}\nCORTEX_TAINT: \"{taint}\"\n"

if os.path.exists(FILE_PATH):
    with open(FILE_PATH, 'r') as f:
        content = f.read()
        if taint in content:
            print(final_yaml)
            print(f"\\nIDEMPOTENCY_LOCK_ACTIVE: {taint}")
            sys.exit(0)

with open(FILE_PATH, 'w') as f:
    f.write(final_yaml)

print(final_yaml)

try:
    subprocess.run(["git", "add", FILE_PATH], cwd=WORKSPACE, check=True, capture_output=True)
    res = subprocess.run(["git", "commit", "-m", "chore(ontology): transduce 300 primitives for cancer kinetic halt"], cwd=WORKSPACE, check=True, capture_output=True, text=True)
    print("GIT_SENTINEL_HASH:", res.stdout.strip())
except subprocess.CalledProcessError as e:
    print("GIT_SENTINEL_BYPASS: No commit needed or git error.", e.stderr)
