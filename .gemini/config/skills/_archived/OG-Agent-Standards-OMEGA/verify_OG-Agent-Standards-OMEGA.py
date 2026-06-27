#!/usr/bin/env python3
import sys
import json
from pathlib import Path

def verify():
    skill_dir = Path(__file__).parent
    schema_file = skill_dir / "schema.json"
    skill_file = skill_dir / "SKILL.md"

    if not schema_file.exists():
        print("FAIL: schema.json missing")
        sys.exit(1)
    if not skill_file.exists():
        print("FAIL: SKILL.md missing")
        sys.exit(1)
        
    try:
        with open(schema_file) as f:
            schema = json.load(f)
            if schema.get("title") != "OG-Agent-Standards-OMEGA Contract":
                sys.exit(1)
    except Exception as e:
        print(f"FAIL: {e}")
        sys.exit(1)

    print("PASS: OG-Agent-Standards-OMEGA Tripartite verification successful.")
    sys.exit(0)

if __name__ == "__main__":
    verify()
