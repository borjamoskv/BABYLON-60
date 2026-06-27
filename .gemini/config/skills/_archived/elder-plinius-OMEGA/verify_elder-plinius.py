#!/usr/bin/env python3
import os
import sys

def verify():
    dir_path = os.path.dirname(os.path.abspath(__file__))
    required_files = ["SKILL.md", "schema.json", "verify_elder-plinius.py"]
    
    for f in required_files:
        if not os.path.exists(os.path.join(dir_path, f)):
            print(f"FAILED: {f} missing.")
            sys.exit(1)
            
    print("PASS: Elder-Plinius-OMEGA Tripartite artifacts verified. [C5-REAL GODMODE]")
    sys.exit(0)

if __name__ == "__main__":
    verify()
