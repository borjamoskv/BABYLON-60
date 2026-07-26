# C5-REAL EXERGY CERTIFIED
import os
import json

def is_ignored(path):
    ignores = ['.git', 'node_modules', '.venv', 'venv', 'dist', 'target', '__pycache__', '.pytest_cache', '.codebase-memory', 'tmp_', '.uv_python', 'scratch', 'artifacts', 'assets', 'fsharp_kernel', 'strike-rs', 'house_remotion_project']
    for ig in ignores:
        if ig in path:
            return True
    return False

def get_tree(startpath):
    tree = {}
    for root, dirs, files in os.walk(startpath):
        dirs[:] = [d for d in dirs if not is_ignored(os.path.join(root, d))]
        for file in sorted(files):
            if is_ignored(file) or file.endswith('.lock') or file.endswith('.whl') or file.endswith('.png') or file.endswith('.pdf'):
                continue
            filepath = os.path.join(root, file)
            rel_path = os.path.relpath(filepath, startpath)

            try:
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read(500) # Read first 500 chars to understand purpose
                    tree[rel_path] = content
            except Exception:
                pass
    return tree

if __name__ == "__main__":
    repo_path = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv"
    tree = get_tree(repo_path)

    # Dump tree keys to understand structure
    print(f"Total files read: {len(tree)}")
    with open("cortex_repo_index.json", "w") as f:
        json.dump(list(tree.keys()), f, indent=2)

    print("Files indexed in cortex_repo_index.json")
