import sys
import json
import os

def verify():
    # Verify tripartite
    skill_dir = os.path.dirname(os.path.abspath(__file__))
    
    if not os.path.exists(os.path.join(skill_dir, "SKILL.md")):
        print("FAIL: SKILL.md missing")
        sys.exit(1)
        
    if not os.path.exists(os.path.join(skill_dir, "schema.json")):
        print("FAIL: schema.json missing")
        sys.exit(1)
        
    try:
        with open(os.path.join(skill_dir, "schema.json"), "r") as f:
            schema = json.load(f)
            assert "intent" in schema.get("required", [])
    except Exception as e:
        print(f"FAIL: Invalid schema.json - {e}")
        sys.exit(1)

    print("PASS: Tripartite verification successful")
    sys.exit(0)

if __name__ == "__main__":
    verify()
