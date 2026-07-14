#!/usr/bin/env python3
import sys
import os
import math
from cortex.daemons.bft_ledger_helper import append_anchor

# [C5-REAL] ENTROPY SWEEPER DAEMON (MACRÓFAGO ONTOLÓGICO)
# Core Invariant: Purges semantic friction (C4-SIM / Green Theater / Gossip) from subagent outputs.
# Computes Shannon Entropy and forces termination if payload characteristics represent thermal noise.

DB_FILE = "$CORTEX_ROOT/30_BABYLON-60/nexus_anchors_v2.db"

def calculate_shannon_entropy(text: str) -> float:
    if not text:
        return 0.0
    entropy = 0.0
    length = len(text)
    frequencies: dict = {}
    for char in text:
        frequencies[char] = frequencies.get(char, 0) + 1
    for count in frequencies.values():
        p = count / length
        entropy -= p * math.log2(p)
    return entropy

def evaluate_prosa_ratio(text: str) -> float:
    # A simple heuristic to compute prose density vs AST density.
    # Count lines containing code keywords vs pure text lines.
    lines = text.strip().split("\n")
    if not lines:
        return 1.0
        
    code_triggers = {
        "import ", "def ", "class ", "from ", "return ", "assert ", 
        "print(", "sqlite3", "hashlib", "sys.", "os.", "const ", "function", "let "
    }
    
    code_lines = 0
    prose_lines = 0
    in_code_block = False
    
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("```"):
            in_code_block = not in_code_block
            continue
        if in_code_block:
            code_lines += 1
            continue
            
        is_code = any(trigger in stripped for trigger in code_triggers) or stripped.endswith(":") or stripped.startswith("elif ") or stripped.startswith("except ")
        if is_code:
            code_lines += 1
        else:
            if stripped:
                prose_lines += 1
                
    total = code_lines + prose_lines
    if total == 0:
        return 1.0
    return prose_lines / total

def check_green_theater(text: str) -> bool:
    theater_phrases = [
        "aquí tienes", "espero que", "lo siento", "disculpa", 
        "dario amodei", "hegseth", "pentagon", "india summit", "truth social"
    ]
    lower_text = text.lower()
    return any(phrase in lower_text for phrase in theater_phrases)

def run_sweeper(payload: str):
    entropy = calculate_shannon_entropy(payload)
    prosa_ratio = evaluate_prosa_ratio(payload)
    has_theater = check_green_theater(payload)
    
    # Verdict criteria
    is_corrupted = prosa_ratio > 0.8 or has_theater
    
    print(f"[*] Shannon Entropy: {entropy:.4f}")
    print(f"[*] Prose Ratio: {prosa_ratio:.2%}")
    print(f"[*] Green Theater Flag: {has_theater}")
    
    if is_corrupted:
        print("[!] Rejection trigger matched. Purging payload...")
        rejection_payload = f"PURGED_PAYLOAD: Prose {prosa_ratio:.2%} | Shannon Entropy {entropy:.4f} | Has_Theater {has_theater}"
        
        new_hash = append_anchor(DB_FILE, rejection_payload, "ENTROPY_SWEEPER_DAEMON")
        print(f"[!] SIGKILL_State_Purge executed. Ledger Rejection Hash: {new_hash[:16]}")
        sys.exit(1)
        
    print("[✓] Payload meets C5-REAL standards. Exergy certified.")
    sys.exit(0)

if __name__ == "__main__":
    if len(sys.argv) < 2:
        # Read from stdin
        payload_data = sys.stdin.read()
    else:
        # Read file specified in argv
        filepath = sys.argv[1]
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                payload_data = f.read()
        else:
            payload_data = sys.argv[1]
            
    run_sweeper(payload_data)
