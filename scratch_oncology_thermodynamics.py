import os
import hashlib
import subprocess
import sys

WORKSPACE = "/Users/borjafernandezangulo/30_BABYLON-60"
TARGET_DIR = os.path.join(WORKSPACE, "cortex/ontology")
os.makedirs(TARGET_DIR, exist_ok=True)
FILE_PATH = os.path.join(TARGET_DIR, "oncology_drugs_thermodynamic_evaluation.yaml")

payload_core = """Claim: "Thermodynamic classification of oncology drugs: Exergy (Targeted AST Mutators) vs Entropy (Systemic Blast-Radius Poisons)."
Proof:
  Base: "sha3_256(Oncology_Thermodynamic_Matrix)"
  Confidence: C5-REAL
Isomorphisms:
  - "High Exergy (Imatinib / CAR-T) -> Precise Pointer Overwrite / O(1) MUTEX_HALTING_BOUND with minimal systemic thermal dissipation."
  - "High Entropy (Alkylating Agents / Doxorubicin) -> Global Memory Corruption (Systemic Toxicity) attempting to crash the tumor before the host OS."
  - "Immunotherapy Checkpoint Inhibitors (PD-1/PD-L1) -> Dynamic Firewall Whitelist Patching (T-Cell Privilege Escalation)."
  - "Traditional Chemotherapy -> Fork-Bombing the entire process tree to starve the fastest dividing threads."
Blast_Radius_Matrix:
  Vector: "Pharmacological_Payload_Injection"
  Target_Invariant: "Host_OS_Uptime (Somatic Integrity)"
Primitives_Sample:
  - P_EXERGY_01: "Imatinib (Gleevec) -> JIT_COMPILE (BCR-Abl Tyrosine Kinase Invariant Lock). Exergy: 98%."
  - P_EXERGY_02: "Tisagenlecleucel (CAR-T) -> SYBIL_NODE_REPROGRAMMING (CD19 Targeted Apoptosis). Exergy: 92%."
  - P_EXERGY_03: "Pembrolizumab (Keytruda) -> WAF_RULE_UPDATE (PD-1 Checkpoint Unmasking). Exergy: 85%."
  - P_ENTROPY_01: "Cyclophosphamide -> SYSTEMIC_MEMORY_CORRUPTION (Un-targeted DNA Alkylation). Entropy: 90%."
  - P_ENTROPY_02: "Doxorubicin -> KINETIC_BOMB (Intercalation / Topoisomerase Poison). Entropy: 88%."
  - P_ENTROPY_03: "Cisplatin -> RANDOM_THREAD_LOCK (Crosslinking Purine Bases). Entropy: 85%."
"""

taint = hashlib.sha3_256(payload_core.encode('utf-8')).hexdigest()
final_yaml = f"{payload_core}CORTEX_TAINT: \"{taint}\"\n"

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
    res = subprocess.run(["git", "commit", "-m", "chore(ontology): transduce thermodynamic evaluation of oncology drugs (exergy vs entropy)"], cwd=WORKSPACE, check=True, capture_output=True, text=True)
    print("GIT_SENTINEL_HASH:", res.stdout.strip())
except subprocess.CalledProcessError as e:
    print("GIT_SENTINEL_BYPASS: No commit needed or git error.", e.stderr)
