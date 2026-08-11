import os
import re

files_to_fix = [
    "./scratch/test_dual_license.py",
    "./scratch/test_hypervisor.py",
    "./babylon60/extensions/daemon/alerts.py",
    "./babylon60/extensions/daemon/event_loop.py",
    "./babylon60/cortex_mamba_network.py",
    "./babylon60/cortex_purge_anergy.py",
    "./test_graph.py",
    "./test_attestation.py",
    "./babylon60-ide/backend/routes/inference.py"
]

slop_modules = [
    "net_mamba_ledger_engine", "cortex_mamba_block", "core_graph_ledger",
    "io_persist_ledger", "premium_features", "license_manager",
    "ouroboros_prune", "ouroboros_absorb_runner", "cancer_isomorphism_pipeline",
    "babylon60.engine", "babylon60.memory"
]

pattern = re.compile(r'^\s*(import|from)\s+(' + '|'.join(slop_modules) + r')\b.*$', re.MULTILINE)

for filepath in files_to_fix:
    if not os.path.exists(filepath):
        continue
    with open(filepath, "r") as f:
        content = f.read()
    
    new_content = pattern.sub('', content)
    
    if new_content != content:
        with open(filepath, "w") as f:
            f.write(new_content)
        print(f"Fixed {filepath}")
