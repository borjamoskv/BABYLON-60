from pathlib import Path

# C5-REAL: Prose Annihilator (Exergy Maximization)

TARGET_EXTS = {'.py', '.go', '.rs', '.js', '.ts', '.yml'}
INVARIANT_MARKERS = {'C5-REAL', 'INV_', 'TODO', 'FIXME', 'noqa', 'pylint', 'type:', 'CORTEX-TAINT', 'pragma'}

def is_redundant_comment(line: str, ext: str) -> bool:
    line_s = line.strip()
    if ext in {'.py', '.yml', '.rs'}:
        if not line_s.startswith('#') and not line_s.startswith('//'):
            return False
    elif ext in {'.go', '.js', '.ts'}:
        if not line_s.startswith('//'):
            return False
    
    for marker in INVARIANT_MARKERS:
        if marker in line_s:
            return False
            
    if line_s.startswith('#!'):
        return False
        
    return True

def annihilate_prose(file_path: Path) -> int:
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
    except Exception:
        return 0

    new_lines = []
    removed_count = 0
    ext = file_path.suffix

    for line in lines:
        if is_redundant_comment(line, ext):
            removed_count += 1
        else:
            new_lines.append(line)

    if removed_count > 0:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

    return removed_count

def main():
    root_dir = Path(__file__).resolve().parent.parent
    total_removed = 0
    files_modified = 0

    for path in root_dir.rglob('*'):
        if path.is_file() and path.suffix in TARGET_EXTS:
            if '.venv' in path.parts or '.git' in path.parts or '__pycache__' in path.parts or 'node_modules' in path.parts:
                continue
            count = annihilate_prose(path)
            if count > 0:
                total_removed += count
                files_modified += 1

    print(f"C5-REAL: Annihilated {total_removed} redundant prose lines across {files_modified} files.")

if __name__ == '__main__':
    main()
