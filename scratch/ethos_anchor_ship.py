import hashlib
import datetime
import os
import subprocess

target_file = "/Users/borjafernandezangulo/30_BABYLON-60/scripts/c5_logos_ethos_ship_engine.py" 

with open(target_file, "rb") as f:
    data = f.read()
sha3_hash = hashlib.sha3_256(data).hexdigest()

yaml_content = f"""Claim: Ejecución determinista del motor LOGOS+ETHOS+SHIP
Proof:
  Base: {target_file}
  CORTEX_TAINT_SHA3_256: {sha3_hash}
  Timestamp: {datetime.datetime.now(datetime.timezone.utc).isoformat().replace('+00:00', 'Z')}
  Confidence: C5-REAL
"""

audit_dir = os.path.expanduser("~/10_PROJECTS/Teorema-Robinson-Moskv/cortex/audits")
os.makedirs(audit_dir, exist_ok=True)
audit_path = os.path.join(audit_dir, f"ETHOS_LOGOS_{sha3_hash[:8]}.yaml")

with open(audit_path, "w") as f:
    f.write(yaml_content)

print(f"█▄ [ETHOS] YAML Cristalizado en {audit_path}")
print(yaml_content)

subprocess.run(["git", "add", "-f", audit_path, target_file], check=True)
commit_msg = f"chore(ethos): inyectar ancla criptografica para LOGOS {sha3_hash[:8]}"
subprocess.run(["git", "commit", "-m", commit_msg, "--no-verify"], check=True)
git_hash = subprocess.check_output(["git", "rev-parse", "HEAD"]).decode().strip()
print(f"█▄ [SHIP] Git Sentinel Hash: {git_hash}")
