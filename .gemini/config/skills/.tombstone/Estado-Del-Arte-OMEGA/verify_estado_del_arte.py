#!/usr/bin/env python3
# C5-REAL
import os, json

DIR = os.path.dirname(os.path.abspath(__file__))

def verify():
    assert os.path.exists(os.path.join(DIR, "SKILL.md")), "Missing SKILL.md"
    assert os.path.exists(os.path.join(DIR, "schema.json")), "Missing schema.json"
    with open(os.path.join(DIR, "schema.json")) as f:
        assert json.load(f).get("title") == "Estado-Del-Arte-OMEGA I/O Contract", "Invalid schema title"
    with open(os.path.join(DIR, "SKILL.md")) as f:
        content = f.read()
        assert "C5-REAL" in content, "Missing C5-REAL tag"
        assert "omega_2_thermodynamic" in content, "Missing axiom omega_2_thermodynamic"
    print("C5-REAL: VERIFIED")
    return 0

if __name__ == "__main__":
    exit(verify())
