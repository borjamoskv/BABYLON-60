import logging
import os
import subprocess
import datetime
from pathlib import Path

# C5-REAL: SOTA-Vector-Engine-Omega Execution
HOME_DIR = Path(os.path.expanduser('~'))
SKILL_DIR = Path(__file__).resolve().parent
CORTEX_ROOT = Path(__file__).resolve().parents[3]
BOCETOS_DIR = HOME_DIR / "BOCETOS"

def get_cortex_commits():
    try:
        res = subprocess.run(["git", "log", "--since=3 days ago", "--oneline"], cwd=CORTEX_ROOT, capture_output=True, text=True, check=True)
        commits = res.stdout.strip()
        if not commits:
            return "- [SYSTEM] Sin mutaciones en las últimas 72h."
        return "\n".join([f"- `{c.split(' ', 1)[0]}` {c.split(' ', 1)[1]}" for c in commits.split("\n") if c])
    except Exception as e:  # noqa: BLE001
        return f"- [ERROR] Fallo al extraer Sentinel Logs: {e}"

def generate_newsletter():
    
    template_path = SKILL_DIR / "newsletter_template.md"
    if not template_path.exists():
        logging.getLogger(__name__).info("Falta el template.")
        return
        
    template = template_path.read_text()
    
    cortex_commits = get_cortex_commits()
    
    sota_vectors = """### 1. Vector Open-Weight & Foundation Models
- **GPT-5.5 Cyber / GPT-5.6:** Frecuencia de despliegue acelerada.
- **Claude Fable 5 & Opus 4.8:** Iteraciones en Test Time Compute.

- **SpaceX Colossus Deal:** Datacenters satelitales masivos.
- **Nvidia N1X:** Nueva arquitectura de red superando B200.

- **Codex as Workspace:** Entorno de desarrollo nativo.
- **Loop Engineering:** Swarm Architecture desplazando al prompt engineering."""
    
    date_str = datetime.datetime.now().strftime("%Y-%m-%d")
    issue_num = 1
    
    compiled = template.replace("{ISSUE_NUMBER}", str(issue_num))
    compiled = compiled.replace("{DATE}", date_str)
    compiled = compiled.replace("{SOTA_VECTORS}", sota_vectors)
    compiled = compiled.replace("{CORTEX_COMMITS}", cortex_commits)
    
    output_path = BOCETOS_DIR / f"SOTA_CRYSTAL_Issue_{issue_num}.md"
    output_path.write_text(compiled)
    logging.getLogger(__name__).info(f"[C5-REAL] Boletín compilado exitosamente en: {output_path}")

if __name__ == "__main__":
    generate_newsletter()
