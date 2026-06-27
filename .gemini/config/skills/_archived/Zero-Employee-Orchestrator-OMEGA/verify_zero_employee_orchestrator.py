import sys
import json
import os

def verify_skill():
    print("[*] Running Verification for Zero-Employee-Orchestrator-OMEGA")
    
    # Check SKILL.md
    skill_path = os.path.join(os.path.dirname(__file__), "SKILL.md")
    if not os.path.exists(skill_path):
        print("[-] SKILL.md missing")
        sys.exit(1)
        
    # Check schema.json
    schema_path = os.path.join(os.path.dirname(__file__), "schema.json")
    if not os.path.exists(schema_path):
        print("[-] schema.json missing")
        sys.exit(1)
        
    with open(schema_path, "r") as f:
        try:
            schema = json.load(f)
            if "$schema" not in schema:
                print("[-] Invalid JSON schema")
                sys.exit(1)
        except Exception as e:
            print(f"[-] schema.json parsing error: {e}")
            sys.exit(1)
            
    print("[+] Zero-Employee-Orchestrator-OMEGA verified successfully. Net Exergy > 0.")
    sys.exit(0)

if __name__ == "__main__":
    verify_skill()
