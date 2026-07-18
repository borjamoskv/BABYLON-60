import os
import difflib

def print_diff(title, f1, f2):
    print(f"=== DIFF: {title} ===")
    if not os.path.exists(f1) or not os.path.exists(f2):
        print("One of the files does not exist.")
        return
    with open(f1, 'r', encoding='utf-8', errors='ignore') as file1:
        lines1 = file1.readlines()
    with open(f2, 'r', encoding='utf-8', errors='ignore') as file2:
        lines2 = file2.readlines()
    
    diff = difflib.unified_diff(lines1, lines2, fromfile=f1, tofile=f2, n=2)
    for line in diff:
        print(line, end='')
    print("\n")

def main():
    root = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv"
    
    print_diff(
        "Root package.json vs cortex/audits/codex/package.json",
        os.path.join(root, "package.json"),
        os.path.join(root, "cortex/audits/codex/package.json")
    )
    
    print_diff(
        "Root ANERGY_TOKEN_PURGE_REPORT.md vs cortex/artifacts/reports/ANERGY_TOKEN_PURGE_REPORT.md",
        os.path.join(root, "ANERGY_TOKEN_PURGE_REPORT.md"),
        os.path.join(root, "cortex/artifacts/reports/ANERGY_TOKEN_PURGE_REPORT.md")
    )
    
    print_diff(
        "claude_new/package.json vs app_source/package.json",
        os.path.join(root, "cortex/audits/claude_new/package.json"),
        os.path.join(root, "cortex/audits/claude_v1.21459.3/app_source/package.json")
    )

if __name__ == "__main__":
    main()
