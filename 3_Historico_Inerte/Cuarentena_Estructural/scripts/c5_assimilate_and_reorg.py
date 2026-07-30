# C5-REAL EXERGY CERTIFIED
import os
import ast
import shutil
import glob

def extract_ast(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        tree = ast.parse(content)
        signatures = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                signatures.append(f"def {node.name}(...)")
            elif isinstance(node, ast.ClassDef):
                signatures.append(f"class {node.name}(...)")
        return signatures
    except Exception:
        return []

def assimilate_repo():
    os.makedirs("artifacts", exist_ok=True)
    out_file = "artifacts/cortex_assimilation_A_Z.md"
    all_files = []
    for root, _, files in os.walk("."):
        if ".git" in root or "node_modules" in root or "venv" in root or ".venv" in root or "tmp" in root or "artifacts" in root:
            continue
        for file in files:
            if file.endswith(('.py', '.md', '.yaml', '.json')):
                all_files.append(os.path.join(root, file))

    all_files.sort() # Desde la a a la Z, en orden

    with open(out_file, "w", encoding="utf-8") as out:
        out.write("# C5-REAL Asimilación Total A-Z\n\n")
        for fpath in all_files:
            out.write(f"## Archivo: {fpath}\n")
            if fpath.endswith(".py"):
                sigs = extract_ast(fpath)
                for s in sigs:
                    out.write(f"- {s}\n")
            else:
                out.write("- [Contenido No-Python Asimilado]\n")
            out.write("\n")
    print(f"Asimilación completada en {out_file}")

def reorganize_cortex_python():
    # Move tests
    os.makedirs("tests/cortex", exist_ok=True)
    cortex_tests = glob.glob("cortex/*_test.py")
    for ct in cortex_tests:
        shutil.move(ct, f"tests/cortex/{os.path.basename(ct)}")
        print(f"Moved test {ct}")

    # Reorganize cortex core
    categories = {
        "engines": ["engine", "compiler", "verifier", "orchestrator"],
        "bridges": ["bridge", "client", "playwright", "haskell", "kimi", "noether", "router", "daemon"],
        "substack": ["substack"],
    }

    for cat in categories.keys():
        os.makedirs(f"cortex/{cat}", exist_ok=True)
    os.makedirs("cortex/core", exist_ok=True)

    cortex_files = glob.glob("cortex/*.py")
    for f in cortex_files:
        name = os.path.basename(f)
        if name == "__init__.py":
            continue

        moved = False
        for cat, keywords in categories.items():
            if any(kw in name for kw in keywords):
                shutil.move(f, f"cortex/{cat}/{name}")
                print(f"Moved {name} to {cat}")
                moved = True
                break

        if not moved:
            shutil.move(f, f"cortex/core/{name}")
            print(f"Moved {name} to core")

def rewrite_imports():
    # We must rewrite `from cortex.X import` to `from cortex.CATEGORY.X import`
    # Build a map of module name to category
    module_map = {}
    for root, _, files in os.walk("cortex"):
        for file in files:
            if file.endswith(".py") and file != "__init__.py":
                mod_name = file[:-3]
                category = os.path.basename(root)
                if category != "cortex":
                    module_map[mod_name] = category

    def replace_in_file(fpath):
        try:
            with open(fpath, "r", encoding="utf-8") as f:
                content = f.read()

            new_content = content
            for mod_name, cat in module_map.items():
                new_content = new_content.replace(f"from cortex.{mod_name} import", f"from cortex.{cat}.{mod_name} import")
                new_content = new_content.replace(f"import cortex.{mod_name}", f"import cortex.{cat}.{mod_name}")
                new_content = new_content.replace(f"from cortex import {mod_name}", f"from cortex.{cat} import {mod_name}")

            if new_content != content:
                with open(fpath, "w", encoding="utf-8") as f:
                    f.write(new_content)
                print(f"Updated imports in {fpath}")
        except Exception as e:
            print(f"Error reading {fpath}: {e}")

    for root, _, files in os.walk("."):
        if ".git" in root or "node_modules" in root or "venv" in root: continue
        for file in files:
            if file.endswith(".py"):
                replace_in_file(os.path.join(root, file))

if __name__ == "__main__":
    assimilate_repo()
    reorganize_cortex_python()
    rewrite_imports()
    print("Reorganización de código Python completada.")
    os.system("git add . && git commit -m 'chore(c5-real): colapso ast y reorg exergica del codigo base python'")
