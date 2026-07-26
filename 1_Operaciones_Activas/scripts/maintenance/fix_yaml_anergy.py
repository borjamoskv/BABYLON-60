# C5-REAL EXERGY CERTIFIED
import os
import glob
import re

print("Purgando Anergía Sintáctica en YAML...")

def fix_yaml(filepath):
    with open(filepath, "r") as f:
        content = f.read()

    # Fix Claim: [XXX] YYY -> Claim: "[XXX] YYY"
    content = re.sub(r"^(Claim:\s+)(\[.*?\]\s+.*?)$", r'\1"\2"', content, flags=re.MULTILINE)
    # Fix Assertion: [XXX] YYY -> Assertion: "[XXX] YYY"
    content = re.sub(r"^(Assertion:\s+)(\[.*?\]\s+.*?)$", r'\1"\2"', content, flags=re.MULTILINE)

    # Fix Isomorphisms: - "A" -> "B" (YAML doesn't allow -> unquoted if it looks weird, wait, prettier complained about:
    # - "Cordura" -> "Cadena Principal..."
    # If the whole line is unquoted after -, it should be a string, but prettier sees -> and thinks it's a mapping if unquoted?
    # No, it's: - "Cordura" -> "Cadena Principal" ... wait, the quotes are around Cordura, then -> outside quotes!
    # So it parses as: - (string) -> (string). That's invalid YAML. It should be: - '"Cordura" -> "Cadena Principal"'
    content = re.sub(r'^(- \s*)("[^"]+"\s*->\s*"[^"]+")(\s*)$', r"\1'\2'\3", content, flags=re.MULTILINE)

    with open(filepath, "w") as f:
        f.write(content)

yaml_files = glob.glob("**/*.yaml", recursive=True) + glob.glob("**/*.yml", recursive=True)
for yf in yaml_files:
    if os.path.isfile(yf):
        fix_yaml(yf)

# Run prettier again
subprocess_result = os.system("npx --yes prettier --write '**/*.{yaml,yml}'")
if subprocess_result == 0:
    os.system("git add . && git commit -m 'refactor(cortex): fix YAML syntax anergy and re-apply AST pareto (C5-REAL)'")
    os.system("git rev-parse --short HEAD > hash.txt")
