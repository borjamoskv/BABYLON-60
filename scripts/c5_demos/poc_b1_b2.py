#!/usr/bin/env python3

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../01_ORCHESTRATOR")))

from babylon60.bft.cortex_persist_ledger import CortexPersistLedger, CortexEvent

def test_b1_b2() -> None:
    db_path = "poc_ledger.db"
    if os.path.exists(db_path):
        os.remove(db_path)
        
    ledger = CortexPersistLedger(db_path)
    
    # Create an initial event
    ev1 = CortexEvent(
        event_type="SYS_INIT",
        payload={"msg": "hello"},
        cortex_taint="T0",
        agent_id="agent1",
        domain="core"
    )
    
    print("[*] Inserting EV1 via append_batch")
    ledger.append_batch([ev1])
    
    if not ledger.verify_integrity():
        print("[-] Initial integrity failed")
        return
        
    print("[+] Initial integrity OK")
    
    ev1_5 = CortexEvent(
        event_type="SYS_INTER",
        payload={"msg": "inter"},
        cortex_taint="T0.5",
        agent_id="agent1",
        domain="core"
    )
    ledger.append_batch([ev1_5])

    # B-1: Mix duplicate (ev1) + new event (ev2)
    ev2 = CortexEvent(
        event_type="SYS_NEW",
        payload={"msg": "world"},
        cortex_taint="T1",
        agent_id="agent1",
        domain="core"
    )
    
    print("\n[*] Testing B-1 (Hash Poisoning): Sending batch [EV1 (dup), EV2 (new)]")
    ledger.append_batch([ev1, ev2])
    
    if not ledger.verify_integrity():
        print("[-] B-1 Falsified! Integrity broken. Hash chain poisoned.")
    else:
        print("[+] Integrity OK (B-1 not reproduced?)")
        
    # B-2: Duplicates in same batch
    ev3 = CortexEvent(
        event_type="SYS_DUP",
        payload={"msg": "same"},
        cortex_taint="T2",
        agent_id="agent1",
        domain="core"
    )
    
    print("\n[*] Testing B-2 (In-Batch Duplicates): Sending batch [EV3, EV3]")
    try:
        ledger.append_batch([ev3, ev3])
        print("[+] B-2 not reproduced?")
    except Exception as e:
        print(f"[-] B-2 Falsified! Crash occurred: {type(e).__name__}: {e}")

if __name__ == "__main__":
    test_b1_b2()
