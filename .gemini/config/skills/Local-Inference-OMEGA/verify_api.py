#!/usr/bin/env python3
# C5-REAL
import sys, os

def verify():
    d = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(os.path.join(d, "SKILL.md")): sys.exit("ERR: SKILL.md missing")
    if not os.path.exists(os.path.join(d, "schema.json")): sys.exit("ERR: schema.json missing")
    print("OK: Structurally verified")
    sys.exit(0)

if __name__ == "__main__":
    verify()
