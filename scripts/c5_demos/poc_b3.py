#!/usr/bin/env python3

import sys
import os
import json
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../01_ORCHESTRATOR")))

from babylon60.compliance_exporter.eu_ai_act import EUAIActComplianceExporter
from babylon60.bft.cortex_persist_ledger import CortexPersistLedger, CortexEvent

def test_b3() -> None:
    # Setup dummy bundle
    bundle_path = "poc_bundle"
    os.makedirs(bundle_path, exist_ok=True)
    with open(os.path.join(bundle_path, "manifest.json"), "w") as f:
        json.dump({"global_hash": "FAKE_HASH_123"}, f)
    
    exporter = EUAIActComplianceExporter(artifact_bundle_path=bundle_path)
    
    print("[*] Test 1: No ledger DB provided (Should FAIL Art 12)")
    cert_no_db = exporter.generate_certificate("SYS-1", "OP-1")
    print(f"Art 12 Status: {cert_no_db['articles_compliance']['Article_12_Record_Keeping_Logging']['status']}")
    
    # Create valid ledger
    db_path = "poc_ledger_b3.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    ledger = CortexPersistLedger(db_path)
    ledger.append_event(CortexEvent(event_type="SYS", payload={"a": 1}, cortex_taint="T0"))
    
    print("\n[*] Test 2: Valid ledger DB provided (Should PASS Art 12)")
    cert_valid_db = exporter.generate_certificate("SYS-1", "OP-1", ledger_path=db_path)
    print(f"Art 12 Status: {cert_valid_db['articles_compliance']['Article_12_Record_Keeping_Logging']['status']}")
    print(f"Global Merkle Root (overwritten by real DB): {cert_valid_db['global_merkle_root']}")

if __name__ == "__main__":
    test_b3()
