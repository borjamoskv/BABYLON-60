import json
import os
import hashlib
from datetime import datetime

LEDGER_PATH = "/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/ouroboros_strike_ledger.jsonl"
BACKUP_PATH = LEDGER_PATH + ".bak"

def generate_id(entry):
    content = f"{entry.get('target', entry.get('target_name'))}{entry.get('timestamp')}"
    return f"OUROBOROS-STRIKE-{hashlib.sha256(content.encode()).hexdigest()[:8].upper()}"

def harden_ledger():
    if not os.path.exists(LEDGER_PATH):
        print(f"Error: Ledger not found at {LEDGER_PATH}")
        return

    # Backup
    with open(LEDGER_PATH, 'r') as f:
        lines = f.readlines()
    
    with open(BACKUP_PATH, 'w') as f:
        f.writelines(lines)

    hardened_entries = []
    for line in lines:
        if not line.strip():
            continue
        try:
            entry = json.loads(line)
            
            # Standardize fields
            target = entry.get('target', entry.get('target_name', 'Unknown'))
            strike_id = entry.get('id', entry.get('issue_id', generate_id(entry)))
            
            hardened = {
                "id": strike_id,
                "intent_id": entry.get('intent_id', f"INTENT-{strike_id}"),
                "chain_id": entry.get('chain_id', "unknown-evm"), # Default to unknown
                "target": target,
                "severity": entry.get('severity', 'Medium'),
                "platform": entry.get('platform', 'immunefi'),
                "title": entry.get('title', 'Untitled Strike'),
                "report_path": entry.get('report_path', ''),
                "status": entry.get('status', 'DRAFT'),
                "timestamp": entry.get('timestamp', datetime.utcnow().isoformat() + 'Z'),
                "confidence": entry.get('confidence', 'C4-Simulated'),
                "pdr_hash": entry.get('pdr_hash', hashlib.sha256(line.encode()).hexdigest()),
                "evidence": entry.get('evidence', [])
            }
            
            # Special handling for known targets
            if "K2" in target:
                hardened["chain_id"] = "stellar-pubnet" if "Stellar" in target else "kinetic-evm"
            if "Exactly" in target:
                hardened["chain_id"] = "optimism-mainnet"
            if "Firedancer" in target:
                hardened["chain_id"] = "solana-mainnet-beta"
            if "SSV" in target:
                hardened["chain_id"] = "eth-mainnet"
            if "Sky" in target:
                hardened["chain_id"] = "eth-mainnet"

            hardened_entries.append(hardened)
        except Exception as e:
            print(f"Error processing line: {line}\nException: {e}")

    with open(LEDGER_PATH, 'w') as f:
        for entry in hardened_entries:
            f.write(json.dumps(entry) + '\n')

    print(f"Successfully hardened {len(hardened_entries)} entries in {LEDGER_PATH}")

if __name__ == "__main__":
    harden_ledger()
