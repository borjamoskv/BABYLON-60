import os
import json
import logging
import concurrent.futures
from typing import Any

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")


def _obliterate_node(abs_path: str, rel_path: str) -> bool:
    """Atomic execution primitive for a single Swarm node."""
    if os.path.exists(abs_path):
        try:
            os.remove(abs_path)
            logging.info(f"[SWARM NODE] PURGED: {rel_path}")
            return True
        except OSError as e:
            logging.error(f"[SWARM NODE] Failed to purge {rel_path}: {e}")
            return False
    return False


def obliterate_zero_operators(target_dir: str) -> None:
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(
        project_root, "cortex", "artifacts", "reports", "BABYLON_60_THEOREM_OMEGA.json"
    )

    if not os.path.exists(json_path):
        logging.error(f"Cannot find {json_path}")
        return

    with open(json_path, "r") as f:
        data: dict[str, Any] = json.load(f)

    accidental = data.get("Accidental_Complexity", [])
    zero_ops = [str(x["file"]) for x in accidental if x.get("matches") == 0]

    logging.info(
        f"ESCUADRÓN DE OBLITERACIÓN (SWARM): Armed. Found {len(zero_ops)} Zero-Operator targets."
    )

    purged = 0
    # Rule Ω24: Forzar ProcessPoolExecutor con recolección de residuos síncrona
    with concurrent.futures.ProcessPoolExecutor(max_workers=os.cpu_count() or 4) as executor:
        futures = []
        for rel_path in zero_ops:
            abs_path = os.path.join(target_dir, rel_path)
            futures.append(executor.submit(_obliterate_node, abs_path, rel_path))
        
        for future in concurrent.futures.as_completed(futures):
            if future.result():
                purged += 1

    logging.info(f"OBLITERATION SWARM COMPLETE. Terminated {purged} inert nodes.")
    logging.info(f"CORTEX-TAINT:borjamoskv:swarm_obliteration:{purged}_nodes_purged")


if __name__ == "__main__":
    obliterate_zero_operators(os.path.expanduser("~/BABYLON-60"))
