import os

def main():
    root = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv"
    target = os.path.join(root, "cortex/artifacts/reports/ANERGY_TOKEN_PURGE_REPORT.md")
    source = "../../ANERGY_TOKEN_PURGE_REPORT.md"
    
    # 1. Symlink ANERGY_TOKEN_PURGE_REPORT
    if os.path.exists(target):
        if os.path.islink(target):
            print(f"Symlink already exists at {target}")
        else:
            os.remove(target)
            os.symlink(source, target)
            print(f"Replaced file with relative symlink: {target} -> {source}")
    else:
        os.symlink(source, target)
        print(f"Created relative symlink: {target} -> {source}")

if __name__ == "__main__":
    main()
