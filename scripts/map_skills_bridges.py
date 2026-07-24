import os
import hashlib
from pathlib import Path

# C5-REAL: Dynamic Skill and Bridge Mapper
# Generates a deterministic map of all agentic extensions.

TARGET_OUTPUT = Path("docs/C5_SKILLS_BRIDGES_MAP.md")
SEARCH_PATHS = [
    Path(os.path.expanduser("~/.gemini/config/plugins")),
    Path(os.path.expanduser("~/.gemini/antigravity/builtin/skills")),
    Path("scripts"),
    Path("ultrathink")
]

KEYWORDS = ['skill', 'bridge', 'ultrathink', 'mcp', 'socket', 'plugin', 'agent']

def hash_file(path: Path) -> str:
    try:
        h = hashlib.sha3_256()
        with open(path, 'rb') as f:
            h.update(f.read())
        return h.hexdigest()[:16]
    except Exception:
        return "ERROR_READING_FILE"

def scan_and_map() -> str:
    mapped_items = []
    
    for base_path in SEARCH_PATHS:
        if not base_path.exists():
            continue
            
        for path in base_path.rglob('*'):
            if path.is_file():
                # Skip massive binary/cache dirs
                if '.git' in path.parts or '__pycache__' in path.parts or 'node_modules' in path.parts:
                    continue
                    
                name = path.name.lower()
                is_match = False
                
                # For plugins dir, include all SKILL.md and metadata
                if 'plugins' in base_path.parts or 'builtin' in base_path.parts:
                    if name in ('skill.md', 'plugin.json') or path.suffix in ('.py', '.sh', '.js', '.ts'):
                        is_match = True
                else:
                    # For local repo scripts/ultrathink, use keyword matching
                    if any(kw in name for kw in KEYWORDS):
                        is_match = True
                        
                if is_match:
                    h = hash_file(path)
                    mapped_items.append({
                        'path': str(path),
                        'size': path.stat().st_size,
                        'hash': h
                    })
                    
    # Sort for deterministic output
    mapped_items.sort(key=lambda x: x['path'])
    
    md = ["# C5-REAL: MAPEO ESTRUCTURAL (SKILLS, ULTRATHINK, PUENTES)"]
    md.append("> **Invariant:** Zero Anergy. Deterministic physical map of all execution vectors.\n")
    
    md.append("## 1. EXTERNAL PLUGINS & SKILLS")
    for item in mapped_items:
        if '.gemini' in item['path']:
            md.append(f"- `[{item['hash']}]` **{item['path']}** ({item['size']} bytes)")
            
    md.append("\n## 2. ULTRATHINK PROTOCOL")
    for item in mapped_items:
        if 'ultrathink' in item['path'].lower() and '.gemini' not in item['path']:
            md.append(f"- `[{item['hash']}]` **{item['path']}** ({item['size']} bytes)")
            
    md.append("\n## 3. BRIDGES (PUENTES) & SOCKETS")
    for item in mapped_items:
        if 'bridge' in item['path'].lower() and '.gemini' not in item['path']:
            md.append(f"- `[{item['hash']}]` **{item['path']}** ({item['size']} bytes)")

    md.append("\n## 4. SWARM AGENTS & ORCHESTRATION")
    for item in mapped_items:
        if 'agent' in item['path'].lower() and '.gemini' not in item['path']:
            md.append(f"- `[{item['hash']}]` **{item['path']}** ({item['size']} bytes)")

    return "\n".join(md)

def main():
    TARGET_OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    content = scan_and_map()
    with open(TARGET_OUTPUT, 'w', encoding='utf-8') as f:
        f.write(content)
    print(f"✅ Mapeo completado y escrito en: {TARGET_OUTPUT}")

if __name__ == '__main__':
    main()
