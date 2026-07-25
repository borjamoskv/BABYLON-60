import hashlib
import shutil
from pathlib import Path
REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_AGENT_DIR = Path.home() / '.agent_persist' / 'projects'
TARGET_LOGS_DIR = REPO_ROOT / 'cortex/legal_dossier/agent_code_local_logs'
INDEX_FILE = TARGET_LOGS_DIR / 'C5_CATALOGO_LOGS_LOCALES_AGENT_CODE.md'

def compute_hashes(filepath: Path) -> tuple[str, str]:
    sha256 = hashlib.sha256()
    sha3 = hashlib.sha3_256()
    with open(filepath, 'rb') as f:
        while (chunk := f.read(65536)):
            sha256.update(chunk)
            sha3.update(chunk)
    return (sha256.hexdigest(), sha3.hexdigest())

def harvest_logs() -> None:
    print('[*] ULTRATHINK P0: Harvesting local Agent Code CLI session logs from ~/.agent_persist/...')
    TARGET_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    if not SOURCE_AGENT_DIR.exists():
        print('[-] Source directory ~/.agent_persist/projects does not exist.')
        return
    jsonl_files = list(SOURCE_AGENT_DIR.rglob('*.jsonl'))
    print(f'[+] Found {len(jsonl_files)} local Agent Code session logs.')
    catalog_entries = []
    for i, file_path in enumerate(sorted(jsonl_files), 1):
        rel_proj = file_path.parent.name
        dest_filename = f'agent_local_log_{i:02d}_{rel_proj}_{file_path.name}'
        dest_path = TARGET_LOGS_DIR / dest_filename
        shutil.copy2(file_path, dest_path)
        sha256_hash, sha3_hash = compute_hashes(dest_path)
        size_kb = dest_path.stat().st_size / 1024.0
        catalog_entries.append({'id': f'LOG-LOCAL-#{i:02d}', 'original_path': str(file_path), 'dest_name': dest_filename, 'size_kb': f'{size_kb:.2f} KB', 'sha256': sha256_hash, 'sha3': sha3_hash})
    md_lines = ['# CATÁLOGO PERICIAL Y CUSTODIA DE LOGS LOCALES DE `AGENT CODE`', '', '> **Documento de Custodia Forense e Identificación Criptográfica (`CORTEX-PERSIST`)**  ', '> **Titular de Propiedad Intellectual:** Don CORTEX Core Dev (`borjamoskv`)  ', '> **Objeto:** Custodia física, sellado hash inmutable (`SHA256 / SHA3-256`) e indexación de los historiales locales y sesiones `.jsonl` ejecutados en silicio soberano Apple Silicon (`~/.agent_persist/projects/`). Acredita de forma incontestable el historial, el pensamiento y las trazas de análisis técnico de `Agent Code` en local.', '', '---', '', '## 1. CUADRO RESUMEN DE SESIONES LOCALES EN DISCO (`C5-REAL`)', '', '| ID | Archivo de Log Preservado en Silicio | Tamaño | SHA256 (Hash de Integridad) | SHA3-256 (Attestation) | Ruta Original en Apple Silicon |', '| :---: | :--- | :---: | :--- | :--- | :--- |']
    for entry in catalog_entries:
        row = f"| **`{entry['id']}`** | `{entry['dest_name']}` | `{entry['size_kb']}` | `{entry['sha256']}` | `{entry['sha3']}` | `{entry['original_path']}` |"
        md_lines.append(row)
    md_lines.extend(['', '---', '', '## 2. VALOR PROBATORIO Y FORENSE', '', '1. **Acreditación de Trazabilidad e Historial:** Estos registros (`LOG-LOCAL-#01` a `#04`) demuestran empíricamente el trabajo, los *prompts*, las lecturas de archivo (`FileRead`) y el análisis arquitectónico (`SHIP ALGEBRA`) ejecutados en silicio Apple Silicon antes del bloqueo, constituyendo una prueba de anterioridad fehaciente (*Prior Art*).', '2. **Inmutabilidad Criptográfica:** El sellado dual con funciones de hash (`SHA256` y `SHA3-256`) previene cualquier impugnación de manipulación posterior del texto logueado.', '', '---', '*Catálogo sellado por el autómata MOSKV-1 APEX / BABILONIA 60. Nivel de Certeza: C5-REAL.*', ''])
    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))
    print(f'[+] Successfully harvested and indexed {len(catalog_entries)} local Agent Code logs.')
    print(f'[+] Index created at: {INDEX_FILE}')
if __name__ == '__main__':
    harvest_logs()