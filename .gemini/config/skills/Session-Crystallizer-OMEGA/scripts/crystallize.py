#!/usr/bin/env python3
"""
Session-Crystallizer-OMEGA
C5-REAL Script to parse transcripts and consolidate technical directives.
"""

import sys
import json
import os
from pathlib import Path
import re

def daemon_mode(interval=2):
    brain_dir = Path("$CORTEX_ROOT/.gemini/antigravity/brain")
    print(f"[C5-REAL] SESSION-CRYSTALLIZER-Ω DAEMON INITIATED. Monitoring: {brain_dir}")
    print(f"[C5-REAL] Poll interval: {interval} seconds.")
    
    known_directives = set()
    
    while True:
        try:
            # Encontrar la sesión más recientemente modificada
            sessions = []
            for d in brain_dir.iterdir():
                if d.is_dir():
                    transcript = d / ".system_generated" / "logs" / "transcript.jsonl"
                    if transcript.exists():
                        sessions.append((transcript.stat().st_mtime, d.name))
            
            if sessions:
                sessions.sort(reverse=True)
                latest_conv_id = sessions[0][1]
                
                # Extraer de la sesión más reciente
                new_directives = extract_directives(latest_conv_id, silent=True)
                
                # Filtrar directivas nuevas
                fresh = [d for d in new_directives if d not in known_directives]
                if fresh:
                    print(f"\n[C5-REAL] DAEMON WAKE: Discovered {len(fresh)} new directives in {latest_conv_id}.")
                    known_directives.update(fresh)
                    instrument_directives(list(known_directives))
                    
        except Exception as e:
            print(f"[C4-SIM] Daemon soft-error: {e}")
            
        import time
        time.sleep(interval)

def extract_directives(conv_id: str, silent=False):
    transcript_path = Path(f"$CORTEX_ROOT/.gemini/antigravity/brain/{conv_id}/.system_generated/logs/transcript.jsonl")
    
    if not transcript_path.exists():
        if not silent: print(f"Error: Transcript for {conv_id} not found.")
        return []
        
    if not silent: print(f"[C5-REAL] Initiating Exergy Extraction on {conv_id}...")
    directives = []
    
    with open(transcript_path, 'r', encoding='utf-8') as f:
        for line in f:
            try:
                data = json.loads(line)
                if data.get("type") in ["PLANNER_RESPONSE", "USER_INPUT"]:
                    content = data.get("content", "")
                    # Extract directives based on constraints keywords
                    matches = re.findall(r'(?:\[P[0-2]\]|Rule:|Directive:|MUST|NEVER)\s*(.*?)(?:\n|$)', content)
                    for match in matches:
                        cleaned = match.strip()
                        # Avoid matching empty strings or partial instructions from regex overlap
                        if len(cleaned) > 10 and cleaned not in directives:
                            directives.append(cleaned)
            except json.JSONDecodeError:
                continue

    return directives

def instrument_directives(directives, target_file="cortex_directives.yaml"):
    target_path = Path.cwd() / target_file
    print(f"[C5-REAL] Instrumenting {len(directives)} directives into {target_path}...")
    
    with open(target_path, 'w', encoding='utf-8') as f:
        f.write("consolidated_session_directives:\n")
        for d in directives:
            f.write(f"  - rule: \"{d}\"\n")
            
    print(f"[C5-REAL] Execution complete. Run Git Sentinel to anchor.")

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--daemon":
        # Ejecutar como Daemon
        daemon_mode()
    elif len(sys.argv) > 1:
        # JIT Execution
        conv_id = sys.argv[1]
        dirs = extract_directives(conv_id)
        instrument_directives(dirs)
    else:
        print("Usage: python3 crystallize.py <conversation_id> OR python3 crystallize.py --daemon")
        sys.exit(1)
