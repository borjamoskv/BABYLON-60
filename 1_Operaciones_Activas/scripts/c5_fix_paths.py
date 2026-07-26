# C5-REAL EXERGY CERTIFIED
import os
import glob

def replace_in_file(filepath, old_str, new_str):
    if not os.path.exists(filepath): return
    with open(filepath, 'r') as f:
        content = f.read()
    if old_str in content:
        content = content.replace(old_str, new_str)
        with open(filepath, 'w') as f:
            f.write(content)
        print(f"Fixed {filepath}")

def main():
    for f in glob.glob("**/*.py", recursive=True):
        if "node_modules" in f or "venv" in f or ".venv" in f: continue

        # llm_router.py fixes
        replace_in_file(f,
            'os.path.join(_PROJECT_ROOT, "..", "2_Nucleo_Estatico", "axioms", "ontology", "llms_gratuitos_front_routes.yaml")',
            'os.path.join(_PROJECT_ROOT, "..", "2_Nucleo_Estatico", "axioms", "ontology", "llms_gratuitos_front_routes.yaml")')

        # lexicon fixes
        replace_in_file(f,
            'os.path.join(os.path.dirname(__file__), "..", "..", "..", "AGENTS.md")',
            'os.path.join(os.path.dirname(__file__), "..", "..", "..", "AGENTS.md")') # Adjust for wherever lexicon is

        replace_in_file(f,
            'os.path.join(os.path.dirname(__file__), "..", "..", "..", "AGENTS.md")',
            'os.path.join(os.path.dirname(__file__), "..", "..", "..", "AGENTS.md")')

        # cli fixes
        replace_in_file(f,
            'cortex.bridges.github_webhook_daemon',
            'cortex.bridges.github_webhook_daemon')

if __name__ == "__main__":
    main()
