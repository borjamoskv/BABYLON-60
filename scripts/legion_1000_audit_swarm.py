import os
import concurrent.futures
import re

MYTHOLOGICAL_TERMS = {
    r"Ineficiencia": "Ineficiencia",
    r"Filtro de Ruido": "Filtro de Ruido",
    r"Ambigüedad Semántica": "Ambigüedad Semántica",
    r"DSL Restringido": "DSL Restringido",
    r"Alta Densidad Estructural": "Alta Densidad Estructural",
    r"Worker Asíncrono": "Worker Asíncrono",
    r"Workers Asíncronos": "Workers Asíncronos",
    r"Limitado Estrictamente": "Limitado Estrictamente",
    r"Causal-Determinist": "Causal-Determinist",
    r"Sandbox Aislado": "Sandbox Aislado",
    r"Plataforma de Simulación": "Plataforma de Simulación",
    r"Auditor Pre-Commit": "Auditor Pre-Commit"
}

def audit_file(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()

        modified = False
        new_content = content
        for pattern, replacement in MYTHOLOGICAL_TERMS.items():
            new_content_tmp = re.sub(pattern, replacement, new_content, flags=re.IGNORECASE)
            if new_content_tmp != new_content:
                modified = True
                new_content = new_content_tmp
                
        # Preservar nombres de marca canónicos (MOSKV, CORTEX, BABYLON-60)
        if modified:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(new_content)
            return f"[MODIFIED] {filepath}"
        return f"[CLEAN] {filepath}"
    except Exception as e:
        return f"[ERROR] {filepath}: {str(e)}"

def main():
    print("[SWARM COMMANDER] Init Swarm of 1000 (Simulated via ThreadPool)")
    targets = []
    
    for root, dirs, files in os.walk('.'):
        if '.git' in root or 'node_modules' in root or 'target' in root or '__pycache__' in root:
            continue
        for f in files:
            if f.endswith('.py') or f.endswith('.rs') or f.endswith('.md') or f.endswith('.b60'):
                targets.append(os.path.join(root, f))
    
    print(f"[SWARM COMMANDER] Found {len(targets)} files to audit.")
    
    with concurrent.futures.ThreadPoolExecutor(max_workers=50) as executor:
        results = list(executor.map(audit_file, targets))
    
    modifications = [r for r in results if r.startswith("[MODIFIED]")]
    print(f"[SWARM COMMANDER] Swarm run completed. Modified {len(modifications)} files.")

if __name__ == "__main__":
    main()
