# C5-REAL
import sys, json, os

def verify():
    d = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(os.path.join(d, "SKILL.md")): sys.exit("FAIL: SKILL.md missing")
    if not os.path.exists(os.path.join(d, "schema.json")): sys.exit("FAIL: schema.json missing")
    try:
        with open(os.path.join(d, "schema.json")) as f: assert "intent" in json.load(f).get("required", [])
    except Exception as e: sys.exit(f"FAIL: Invalid schema - {e}")
    print("PASS: Tripartite verification successful")

if __name__ == "__main__": verify()
