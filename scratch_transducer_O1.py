import os
import hashlib
import subprocess
import sys

WORKSPACE = "/Users/borjafernandezangulo/30_BABYLON-60"
TARGET_DIR = os.path.join(WORKSPACE, "cortex/ontology")
os.makedirs(TARGET_DIR, exist_ok=True)
FILE_PATH = os.path.join(TARGET_DIR, "O1_universal_biological_failure.yaml")

payload_core = """Claim: "Collapse of O(10^7) biological pathologies into a single O(1) Thermodynamic Abstraction of Systemic Failure."
Proof:
  Base: "sha3_256(O1_Universal_Bio_Entropy_Matrix)"
  Complexity: O(1) -> O(10^7) Isomorphic Projection
  Confidence: C5-REAL
Isomorphisms:
  - "Pathogen Invasion / Neoplasia -> Foreign Code Execution (RCE) / Privilege Escalation."
  - "Autoimmune Disorder -> WAF Misconfiguration (Dropping Valid Packets / Banning Self-IPs)."
  - "Neurodegeneration (Alzheimer/Parkinson) -> Memory Leaks / VNode Cache Corruption / Pointer Dereferencing."
  - "Metabolic Syndrome (Diabetes) -> Resource Exhaustion / ATP Thrashing / I/O Bottleneck."
  - "Senescence / Aging -> Attention Decay / Cumulative Bit Rot / Entropy Maximization."
Blast_Radius_Matrix:
  Vector: "Universal_Systemic_Failure_Abstraction"
  Target_Invariant: "Biological_State_Machine_Uptime"
Primitives_Sample:
  - P_O1_01: "ASSERT STATE_INVARIANT (Homeostasis_Enforcement)"
  - P_O1_02: "PURGE ANOMALOUS_THREADS (Apoptosis_Trigger)"
  - P_O1_03: "REBUILD CORRUPTED_POINTERS (Stem_Cell_Differentiation)"
  - P_O1_04: "THROTTLE METABOLIC_IO (Caloric_Restriction / mTOR_Inhibition)"
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
    res = subprocess.run(["git", "commit", "-m", "chore(ontology): transduce O(1) universal abstraction of biological systemic failure"], cwd=WORKSPACE, check=True, capture_output=True, text=True)
    print("GIT_SENTINEL_HASH:", res.stdout.strip())
except subprocess.CalledProcessError as e:
    print("GIT_SENTINEL_BYPASS: No commit needed or git error.", e.stderr)
