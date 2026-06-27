import json
import sys
import os

def verify():
    schema_path = os.path.join(os.path.dirname(__file__), "schema.json")
    if not os.path.exists(schema_path): sys.exit(1)
    with open(schema_path, "r") as f:
        if "$schema" not in json.load(f): sys.exit(1)
    if not os.path.exists(os.path.join(os.path.dirname(__file__), "SKILL.md")): sys.exit(1)
    print("Tripartite Verification: PASS. C5-REAL execution ready.")
    sys.exit(0)

if __name__ == "__main__": verify()
