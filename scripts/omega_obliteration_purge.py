import os
import json
import logging

logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def obliterate_zero_operators(target_dir):
    json_path = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/cortex/artifacts/reports/BABYLON_60_THEOREM_OMEGA.json"
    
    if not os.path.exists(json_path):
        logging.error(f"Cannot find {json_path}")
        return

    with open(json_path, 'r') as f:
        data = json.load(f)

    accidental = data.get("Accidental_Complexity", [])
    zero_ops = [x["file"] for x in accidental if x["matches"] == 0]
    
    logging.info(f"OBLITERATOR-OMEGA-NODE: Armed. Found {len(zero_ops)} Zero-Operator targets.")
    
    purged = 0
    for rel_path in zero_ops:
        abs_path = os.path.join(target_dir, rel_path)
        if os.path.exists(abs_path):
            try:
                os.remove(abs_path)
                logging.info(f"PURGED: {rel_path}")
                purged += 1
            except Exception as e:
                logging.error(f"Failed to purge {rel_path}: {e}")

    logging.info(f"OBLITERATION COMPLETE. Terminated {purged} inert nodes.")

if __name__ == "__main__":
    obliterate_zero_operators("/Users/borjafernandezangulo/BABYLON-60")
