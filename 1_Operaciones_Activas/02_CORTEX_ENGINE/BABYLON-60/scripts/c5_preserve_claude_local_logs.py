# C5-REAL EXERGY CERTIFIED
import shutil
import hashlib
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SOURCE_CLAUDE_DIR = Path.home() / '.claude' / 'projects'
TARGET_LOGS_DIR = REPO_ROOT / 'cortex/legal_dossier/claude_code_local_logs'
INDEX_FILE = TARGET_LOGS_DIR / 'C5_CATALOGO_LOGS_LOCALES_CLAUDE_CODE.md'

def compute_hashes(filepath: Path) -> tuple[str, str]:
    sha256 = hashlib.sha256()
    sha3 = hashlib.sha3_256()
    with open(filepath, 'rb') as f:
        while (chunk := f.read(65536)):
            sha256.update(chunk)
            sha3.update(chunk)
    return (sha256.hexdigest(), sha3.hexdigest())

def harvest_logs() -> None:
    print('[*] ULTRATHINK P0: Harvesting local Claude Code CLI session logs from ~/.claude/projects/...')
    TARGET_LOGS_DIR.mkdir(parents=True, exist_ok=True)
    if not SOURCE_CLAUDE_DIR.exists():
        print('[-] Source directory ~/.claude/projects does not exist.')
        return

    jsonl_files = list(SOURCE_CLAUDE_DIR.rglob('*.jsonl'))
    print(f'[+] Found {len(jsonl_files)} local Claude Code session logs.')
    if not jsonl_files:
        return

    catalog_entries = []
    for i, file_path in enumerate(sorted(jsonl_files), 1):
        rel_proj = file_path.parent.name
        dest_filename = f'claude_local_log_{i:02d}_{rel_proj}_{file_path.name}'
        dest_path = TARGET_LOGS_DIR / dest_filename

        # Copy to custody directory
        shutil.copy2(file_path, dest_path)
        sha256_hash, sha3_hash = compute_hashes(dest_path)
        size_kb = dest_path.stat().st_size / 1024.0

        catalog_entries.append({
            'id': f'LOG-LOCAL-#{i:02d}',
            'original_path': str(file_path),
            'dest_name': dest_filename,
            'size_kb': f'{size_kb:.2f} KB',
            'sha256': sha256_hash,
            'sha3': sha3_hash
        })

    md_lines = [
        '# CATÁLOGO PERICIAL Y CUSTODIA DE LOGS LOCALES DE `CLAUDE CODE`',
        '',
        '> **Documento de Custodia Forense e Identificación Criptográfica (`CORTEX-PERSIST`)**  ',
        '> **Titular de Propiedad Intelectual:** Don CORTEX Core Dev (`borjamoskv`)  ',
        '> **Objeto:** Custodia física, sellado hash inmutable (`SHA256 / SHA3-256`) e indexación de los historiales locales y sesiones `.jsonl` ejecutados en silicio soberano Apple Silicon (`~/.claude/projects/`). Acredita de forma incontestable el historial, el pensamiento y las trazas de análisis técnico de `Claude Code` en local.',
        '',
        '---',
        '',
        '## 1. CUADRO RESUMEN DE SESIONES LOCALES EN DISCO (`C5-REAL`)',
        '',
        '| ID | Archivo de Log Preservado en Silicio | Tamaño | SHA256 (Hash de Integridad) | SHA3-256 (Attestation) | Ruta Original en Apple Silicon |',
        '| :---: | :--- | :---: | :--- | :--- | :--- |'
    ]

    for entry in catalog_entries:
        row = f"| **`{entry['id']}`** | `{entry['dest_name']}` | `{entry['size_kb']}` | `{entry['sha256']}` | `{entry['sha3']}` | `{entry['original_path']}` |"
        md_lines.append(row)

    md_lines.extend([
        '',
        '---',
        '',
        '## 2. VALOR PROBATORIO Y FORENSE',
        '',
        '1. **Acreditación de Trazabilidad e Historial:** Estos registros demuestran empíricamente el trabajo, los *prompts*, las lecturas de archivo (`FileRead`) y el análisis arquitectónico ejecutados en silicio Apple Silicon antes del bloqueo, constituyendo una prueba de anterioridad fehaciente (*Prior Art*).',
        '2. **Inmutabilidad Criptográfica:** El sellado dual con funciones de hash (`SHA256` y `SHA3-256`) previene cualquier impugnación de manipulación posterior del texto logueado.',
        '',
        '---',
        '*Catálogo sellado por el autómata MOSKV-1 APEX / BABILONIA 60. Nivel de Certeza: C5-REAL.*',
        ''
    ])

    with open(INDEX_FILE, 'w', encoding='utf-8') as f:
        f.write('\n'.join(md_lines))

    print(f'[+] Successfully harvested and indexed {len(catalog_entries)} local Claude Code logs.')
    print(f'[+] Index created at: {INDEX_FILE}')

if __name__ == '__main__':
    harvest_logs()
