import os

# Configuration
TARGET_DIR = "/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/targets/exactly-protocol"
OUTPUT_FILE = "/Users/borjafernandezangulo/10_PROJECTS/Teorema-Robinson-Moskv/1_Operaciones_Activas/02_CORTEX_ENGINE/cortex-bounties/hunt/exactly_protocol_10m_context.txt"
EXTENSIONS = {'.sol', '.ts', '.js', '.py', '.json', '.md', '.toml', '.txt'}
EXCLUDE_DIRS = {'.git', 'node_modules', 'venv', '.openzeppelin', '.changeset', 'deployments'}

def ingest():
    print(f"[*] Starting ingestion of {TARGET_DIR}...")
    content_blob = []
    file_count = 0
    
    for root, dirs, files in os.walk(TARGET_DIR):
        # Filter excluded directories
        dirs[:] = [d for d in dirs if d not in EXCLUDE_DIRS]
        
        for file in files:
            ext = os.path.splitext(file)[1]
            if ext in EXTENSIONS:
                file_path = os.path.join(root, file)
                rel_path = os.path.relpath(file_path, TARGET_DIR)
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                        header = f"\n\n{'='*20}\nFILE: {rel_path}\n{'='*20}\n"
                        content_blob.append(header + content)
                        file_count += 1
                except Exception as e:
                    print(f"[!] Error reading {rel_path}: {e}")

    full_blob = "".join(content_blob)
    
    # Token estimation approximation (chars / 4)
    tokens = len(full_blob) // 4
    
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        f.write(full_blob)
    
    print("[+] Ingestion complete.")
    print(f"[+] Files processed: {file_count}")
    print(f"[+] Estimated tokens: {tokens:,}")
    print(f"[+] Output saved to: {OUTPUT_FILE}")

if __name__ == "__main__":
    ingest()
