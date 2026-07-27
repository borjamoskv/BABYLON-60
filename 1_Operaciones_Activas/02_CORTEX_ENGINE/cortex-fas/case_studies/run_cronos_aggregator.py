#!/usr/bin/env python3
"""
FAS v24 — CRONOS L5 Aggregator
Reality level: C5-REAL
Aesthetics: Industrial Noir 2026

Ingests the massive bizkaia_cronos_ledger.jsonl and outputs a 
structural summary of the fiscal evasion detected during the background run.
"""
import json
import os
import sys

def main():
    ledger_path = os.path.join(os.path.dirname(__file__), "bizkaia_cronos_ledger.jsonl")
    if not os.path.exists(ledger_path):
        print("[-] CRONOS Ledger not found.")
        sys.exit(1)
        
    records = []
    with open(ledger_path, 'r') as f:
        for line in f:
            if line.strip():
                try:
                    records.append(json.loads(line))
                except Exception:
                    pass
                
    if not records:
        print("[-] No records in CRONOS ledger.")
        sys.exit(0)
        
    total_evasion = sum(r.get("financials", {}).get("total_due_eur", 0) for r in records)
    total_volume = sum(r.get("financials", {}).get("synthetic_volume_eur", 0) for r in records)
    avg_jef = sum(r.get("forensics", {}).get("jef_score", 0) for r in records) / len(records)
    
    # Get top 5 by debt
    sorted_records = sorted(records, key=lambda x: x.get("financials", {}).get("total_due_eur", 0), reverse=True)
    top_5 = sorted_records[:5]
    
    print("="*50)
    print(" CRONOS L5 BATCH AGGREGATION REPORT ")
    print("="*50)
    print(f"Total Cases Generated : {len(records)}")
    print(f"Total Synthetic Volume : €{total_volume:,.2f}")
    print(f"Total Fiscal Recovery Expected : €{total_evasion:,.2f}")
    print(f"Average JEF Score (Obfuscation): {avg_jef:.4f}")
    print("-" * 50)
    print("TOP 5 HIGH-VALUE TARGETS:")
    for i, r in enumerate(top_5, 1):
        t = r.get("target", {})
        f = r.get("financials", {})
        print(f"{i}. {t.get('taxpayer')} | {t.get('blockchain')} | {t.get('wallet_address')[:12]}...")
        print(f"   Vector: {t.get('risk_vector')}")
        print(f"   Total Due: €{f.get('total_due_eur', 0):,.2f} | JEF: {r.get('forensics', {}).get('jef_score', 0):.4f}")
    print("="*50)
    
if __name__ == "__main__":
    main()
