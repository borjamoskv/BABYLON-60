import json
import sys
import os

def verify():
    # 1. Verify schema existence
    schema_path = os.path.join(os.path.dirname(__file__), "schema.json")
    if not os.path.exists(schema_path):
        print("Verification Failed: schema.json missing.")
        sys.exit(1)
        
    # 2. Verify schema validity
    with open(schema_path, "r") as f:
        try:
            schema = json.load(f)
            if "$schema" not in schema:
                sys.exit(1)
        except json.JSONDecodeError:
            print("Verification Failed: Invalid JSON schema.")
            sys.exit(1)
            
    # 3. Verify SKILL.md
    skill_path = os.path.join(os.path.dirname(__file__), "SKILL.md")
    if not os.path.exists(skill_path):
        print("Verification Failed: SKILL.md missing.")
        sys.exit(1)
        
    print("Tripartite Verification: PASS. C5-REAL execution ready.")
    sys.exit(0)

if __name__ == "__main__":
    verify()
