import os
import subprocess

ROOT_DIR = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv"
IGNORE_DIRS = {
    ".git",
    "node_modules",
    "target",
    ".venv",
    ".codebase-memory",
    "__pycache__",
    "dist",
    ".pytest_cache",
    ".ruff_cache",
    ".mypy_cache",
    "artifacts",
    ".uv_python",
    "tmp_fastapi_pkg",
    "tmp_chroma_pkg",
    ".cortex",
    ".vscode",
    "scratch",
}


def get_comment_syntax(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext in {".py", ".sh", ".toml", ".yaml", ".yml", ".rb"}:
        return "#"
    elif ext in {".js", ".ts", ".jsx", ".tsx", ".go", ".rs", ".c", ".cpp", ".java", ".cs", ".php"}:
        return "//"
    elif ext in {".html", ".xml", ".md", ".vtt", ".srt"}:
        return "<!--"
    elif ext in {".css", ".scss", ".less"}:
        return "/*"
    return None


def close_comment_syntax(filename):
    ext = os.path.splitext(filename)[1].lower()
    if ext in {".html", ".xml", ".md", ".vtt", ".srt"}:
        return "-->"
    elif ext in {".css", ".scss", ".less"}:
        return "*/"
    return ""


def maximize_exergy(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            content = f.read()
    except UnicodeDecodeError:
        return False  # Binary file, skip

    # Rule: Trim trailing whitespaces (entropy reduction)
    lines = content.splitlines()
    stripped_lines = [line.rstrip() for line in lines]

    # Rule: Inject C5-REAL signature if not present
    comment_open = get_comment_syntax(filepath)
    comment_close = close_comment_syntax(filepath)

    new_content = "\n".join(stripped_lines) + "\n"

    if comment_open and "C5-REAL EXERGY CERTIFIED" not in new_content:
        signature = f"{comment_open} C5-REAL EXERGY CERTIFIED {comment_close}".strip()
        new_content = signature + "\n" + new_content

    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        return True
    return False


def main():
    print("Iniciando Transducción C5-REAL (A->Z)...")
    mutated_files = 0
    for root, dirs, files in os.walk(ROOT_DIR, topdown=True):
        # Exclude ignored dirs
        dirs[:] = sorted([d for d in dirs if d not in IGNORE_DIRS])
        files = sorted(files)

        for file in files:
            filepath = os.path.join(root, file)
            # Skip some specific large files or DBs
            if file.endswith(".db") or file.endswith(".json") or file.endswith(".lock") or file.endswith(".mp4"):
                continue

            if maximize_exergy(filepath):
                mutated_files += 1
                print(f"[MUTATED] {filepath}")

    if mutated_files > 0:
        print(f"Colapsando {mutated_files} archivos en el Ledger Git...")
        subprocess.run(["git", "add", "."], cwd=ROOT_DIR)
        subprocess.run(
            ["git", "commit", "-m", f"chore(cortex): maximizar exergia en {mutated_files} archivos (C5-REAL A->Z)"],
            cwd=ROOT_DIR,
        )
        res = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT_DIR, capture_output=True, text=True)
        print(f"Ledger Hash: {res.stdout.strip()}")
    else:
        print("Cero entropía detectada. Exergía al máximo.")


if __name__ == "__main__":
    main()
