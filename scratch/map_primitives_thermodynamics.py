import yaml
import json
import hashlib
import sys
from pathlib import Path

def classify_primitives(yaml_path: Path) -> dict:
    if not yaml_path.exists():
        raise FileNotFoundError(f"Missing matrix file: {yaml_path}")
        
    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)
        
    primitives = data.get("Centuria_Matrix", {}).get("Primitives", [])
    
    # Classification logic based on thermodynamic domains
    boltzmann_domains = {"SQLite_WAL", "Thread_Lock", "Memory_Page", "File_Descriptor", "BFT_Ledger"}
    prigogine_domains = {"AST", "DOM", "Git_Sentinel", "Subagent_Swarm", "RLHF_Subtext", "KV_Cache", "MCTS_Search", "V8_Engine", "Rust_Compiler", "TCP_IP"}
    
    boltzmann_list = []
    prigogine_list = []
    unclassified_list = []
    
    for p in primitives:
        pid = p.get("ID")
        domain = p.get("Domain")
        name = p.get("Name")
        action = p.get("Execution")
        phash = p.get("Hash")
        
        info = {
            "id": pid,
            "domain": domain,
            "name": name,
            "action": action,
            "hash": phash
        }
        
        if domain in boltzmann_domains:
            boltzmann_list.append(info)
        elif domain in prigogine_domains:
            prigogine_list.append(info)
        else:
            unclassified_list.append(info)
            
    # Subsample lists for JSON output to prevent token saturation (keeping it ULTRATHIN)
    return {
        "summary": {
            "total_primitives": len(primitives),
            "boltzmann_count": len(boltzmann_list),
            "prigogine_count": len(prigogine_list),
            "unclassified_count": len(unclassified_list),
            "exergy_ratio": round(len(prigogine_list) / len(primitives), 4) if len(primitives) > 0 else 0.0
        },
        "boltzmann_sample": boltzmann_list[:5], # Subsampled to limit entropy
        "prigogine_sample": prigogine_list[:5]  # Subsampled to limit entropy
    }

def main():
    project_root = Path(__file__).resolve().parent.parent
    yaml_path = project_root / "cortex/agents/ontology/centuria_matrix_1000.yaml"
    
    try:
        report = classify_primitives(yaml_path)
        
        # Calculate verification hash of this mapping
        payload = json.dumps(report, sort_keys=True)
        v_hash = hashlib.sha3_256(payload.encode()).hexdigest()
        
        output = {
            "cortex_taint": f"borjamoskv:centuria_thermo:{v_hash[:16]}",
            "state": "COLLAPSED_ULTRATHIN_JSON",
            "mapping": report,
            "ledger_verification": {
                "sha3_256": v_hash,
                "author": "borjamoskv"
            }
        }
        
        print(json.dumps(output, indent=2))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
