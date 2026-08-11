#!/usr/bin/env python3
# ============================================================================
# BABYLON-60 v4.0 Sovereign Hardened
# █ AUTOCOGNITION-Ω | STATE: C5-REAL | AESTHETIC: INDUSTRIAL_NOIR_2026
# ============================================================================
import os

MAPPINGS = {
    # Utils
    "babylon60/utils/result.py": "babylon60/primitives/result.py",
    "babylon60/utils/errors.py": "babylon60/primitives/errors.py",
    "babylon60/utils/cache.py": "babylon60/transducers/cache.py",
    "babylon60/utils/base60.py": "babylon60/primitives/base60.py",
    "babylon60/utils/compression.py": "babylon60/transducers/compression.py",
    "babylon60/utils/turboquant.py": "babylon60/transducers/turboquant.py",
    "babylon60/utils/http.py": "babylon60/transducers/http.py",
    "babylon60/utils/i18n.py": "babylon60/transducers/i18n.py",
    "babylon60/utils/hygiene.py": "babylon60/transducers/hygiene.py",
    "babylon60/utils/sandbox.py": "babylon60/primitives/sandbox.py",
    "babylon60/utils/canonical.py": "babylon60/primitives/canonical.py",
    "babylon60/utils/pulmones.py": "babylon60/transducers/pulmones.py",
    "babylon60/utils/pulmones_worker.py": "babylon60/transducers/pulmones_worker.py",
    "babylon60/utils/linguistic_entropy.py": "babylon60/transducers/linguistic_entropy.py",
    "babylon60/utils/export.py": "babylon60/transducers/export.py",
    "babylon60/utils/semantic_heartbeat.py": "babylon60/transducers/semantic_heartbeat.py",
    "babylon60/utils/void_mih.py": "babylon60/transducers/void_mih.py",
    "babylon60/utils/void_vec.py": "babylon60/transducers/void_vec.py",
    "babylon60/utils/landauer.py": "babylon60/transducers/landauer.py",
    # Extensions
    "babylon60/extensions/swarm/manager.py": "babylon60/extensions/swarm/swarm_engine.py",
    "babylon60/extensions/llm/manager.py": "babylon60/extensions/llm/llm_transducer.py",
    "babylon60/extensions/evo/_autocurative_helper.py": "babylon60/extensions/evo/_autocurative_transducer.py",
    "babylon60/extensions/evo/_genome_tree_helper.py": "babylon60/extensions/evo/_genome_tree_transducer.py",
    "babylon60/extensions/daemon/sync_manager.py": "babylon60/extensions/daemon/sync_engine.py",
    "babylon60/extensions/daemon/substack_follower_bot.py": "babylon60/extensions/daemon/substack_follower_actor.py",
    "babylon60/extensions/daemon/substack_publisher_bot.py": "babylon60/extensions/daemon/substack_publisher_actor.py",
}

for d in ["babylon60/primitives", "babylon60/transducers"]:
    os.makedirs(d, exist_ok=True)
    init_file = os.path.join(d, "__init__.py")
    if not os.path.exists(init_file):
        with open(init_file, "w") as f:
            pass

for old_path, new_path in MAPPINGS.items():
    if not os.path.exists(old_path):
        continue

    # 1. Move file
    os.rename(old_path, new_path)

    # 2. Convert old path to import module
    # "babylon60/primitives/result.py" -> "babylon60.primitives.result"
    new_module = new_path.replace("/", ".").replace(".py", "")

    # 3. Create Facade
    with open(old_path, "w") as f:
        f.write("import warnings\n")
        f.write(
            f"warnings.warn('Módulo deprecado (INV_C5_NOMINAL_DENSITY). Usar {new_module} en su lugar.', DeprecationWarning, stacklevel=2)\n"
        )
        f.write(f"from {new_module} import *\n")

print("Façade injection completed.")
