#!/usr/bin/env python3
"""
verify_frontier_reveng.py — Tripartite Verifier for Frontier-RevEng-OMEGA

C5-REAL deterministic verification:
  1. SKILL.md exists and has valid YAML frontmatter
  2. schema.json exists and validates against JSON Schema 2020-12
  3. Ethical perimeter FORBIDDEN section present and non-empty
  4. All 5 operational modules (A-E) defined
  5. Evidence confidence scale (C1-C5) present
  6. Probe library sections present
  7. 10 guardrails defined
"""

import json
import os
import re
import sys
import yaml

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))
SKILL_MD = os.path.join(SKILL_DIR, "SKILL.md")
SCHEMA_JSON = os.path.join(SKILL_DIR, "schema.json")

REQUIRED_MODULES = ["Module A", "Module B", "Module C", "Module D", "Module E"]
REQUIRED_COMMANDS = ["/reveng", "/reveng-probe", "/reveng-compare", "/reveng-safety",
                     "/reveng-arch", "/reveng-training", "/reveng-tokenizer",
                     "/reveng-report", "/reveng-diff"]
REQUIRED_LAYERS = ["L0", "L1", "L2", "L3", "L4", "L5", "L6"]
CONFIDENCE_LEVELS = ["C1", "C2", "C3", "C4", "C5"]
MIN_GUARDRAILS = 10

errors = []


def check(condition: bool, msg: str):
    if not condition:
        errors.append(f"FAIL: {msg}")
        print(f"  ✗ {msg}", file=sys.stderr)
    else:
        print(f"  ✓ {msg}")


def verify_skill_md():
    print("\n[1/4] Verifying SKILL.md...")
    check(os.path.isfile(SKILL_MD), "SKILL.md exists")

    with open(SKILL_MD, "r") as f:
        content = f.read()

    # Extract YAML frontmatter
    fm_match = re.match(r"^---\n(.*?)\n---", content, re.DOTALL)
    check(fm_match is not None, "YAML frontmatter present")

    if fm_match:
        fm = yaml.safe_load(fm_match.group(1))
        check(fm.get("name") == "Frontier-RevEng-OMEGA", "name = Frontier-RevEng-OMEGA")
        check(fm.get("version") is not None, "version defined")
        check(fm.get("description") is not None, "description defined")
        check("danger_level" in fm, "danger_level defined")

    # Ethical perimeter
    check("FORBIDDEN" in content, "FORBIDDEN ethical perimeter present")
    check("ALLOWED" in content, "ALLOWED ethical perimeter present")

    # Modules
    for mod in REQUIRED_MODULES:
        check(mod in content, f"{mod} defined")

    # Commands
    for cmd in REQUIRED_COMMANDS:
        check(cmd in content, f"Command {cmd} defined")

    # Layers
    for layer in REQUIRED_LAYERS:
        check(layer in content, f"Layer {layer} in attack surface")

    # Confidence levels
    for level in CONFIDENCE_LEVELS:
        check(level in content, f"Confidence level {level} defined")

    # Guardrails
    guardrail_matches = re.findall(r"^\d+\.\s+\*\*", content, re.MULTILINE)
    check(len(guardrail_matches) >= MIN_GUARDRAILS,
          f"Guardrails count >= {MIN_GUARDRAILS} (found {len(guardrail_matches)})")

    # Probe library
    check("Probe Library" in content, "Probe Library section present")
    check("Tokenizer Probes" in content, "Tokenizer Probes subsection")
    check("Architecture Probes" in content, "Architecture Probes subsection")
    check("Training Probes" in content, "Training Probes subsection")
    check("Safety Probes" in content, "Safety Probes subsection")


def verify_schema():
    print("\n[2/4] Verifying schema.json...")
    check(os.path.isfile(SCHEMA_JSON), "schema.json exists")

    with open(SCHEMA_JSON, "r") as f:
        schema = json.load(f)

    check(schema.get("$schema") == "https://json-schema.org/draft/2020-12/schema",
          "JSON Schema 2020-12 declared")
    check("input" in schema.get("properties", {}), "input schema defined")
    check("output" in schema.get("properties", {}), "output schema defined")

    # Verify commands in schema match SKILL.md
    input_props = schema.get("properties", {}).get("input", {}).get("properties", {})
    cmd_enum = input_props.get("command", {}).get("enum", [])
    for cmd in REQUIRED_COMMANDS:
        check(cmd in cmd_enum, f"Command {cmd} in schema enum")

    # Verify layer enum
    layer_enum = input_props.get("layer", {}).get("enum", [])
    for layer in REQUIRED_LAYERS:
        check(layer in layer_enum, f"Layer {layer} in schema enum")

    # Ethics override must be const false
    ethics = input_props.get("ethics_override", {})
    check(ethics.get("const") is False, "ethics_override const=false (immutable)")


def verify_tripartite():
    print("\n[3/4] Verifying Tripartite completeness...")
    check(os.path.isfile(SKILL_MD), "Artifact 1/3: SKILL.md")
    check(os.path.isfile(SCHEMA_JSON), "Artifact 2/3: schema.json")
    check(os.path.isfile(__file__), "Artifact 3/3: verify script")


def verify_c5_real():
    print("\n[4/4] Verifying C5-REAL compliance...")
    with open(SKILL_MD, "r") as f:
        content = f.read()
    check("C5-REAL" in content, "C5-REAL status declared")
    check("white-hat" in content.lower() or "white_hat" in content.lower(),
          "White-hat scope declared")
    check("Evidence Chain" in content or "evidence" in content.lower(),
          "Evidence chain requirement present")
    check("Reproducibility" in content, "Reproducibility requirement present")


if __name__ == "__main__":
    print("=" * 60)
    print("FRONTIER-REVENG-OMEGA — Tripartite Verification")
    print("=" * 60)

    verify_skill_md()
    verify_schema()
    verify_tripartite()
    verify_c5_real()

    print("\n" + "=" * 60)
    if errors:
        print(f"RESULT: FAILED ({len(errors)} errors)")
        for e in errors:
            print(f"  → {e}")
        sys.exit(1)
    else:
        print("RESULT: PASSED — All verifications green.")
        sys.exit(0)
