import os
import glob

def main():
    root = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv"
    
    # Check for empty directories, tmp files, old caches, and duplicate reports
    print("=== UNUSED SCRIPTS / TEMPORARY FILES ===")
    tmp_files = glob.glob(os.path.join(root, "scratch/*"))
    for f in tmp_files:
        rel = os.path.relpath(f, root)
        # check size and extension
        print(f"  - {rel} ({os.path.getsize(f)} bytes)")
        
    print("\n=== PYCACHE / CACHE CHECK ===")
    # Find all __pycache__ folders or .pyc files
    pyc_files = []
    for r, d, files in os.walk(root):
        for f in files:
            if f.endswith(".pyc"):
                pyc_files.append(os.path.relpath(os.path.join(r, f), root))
    print(f"Total compiled python files (.pyc) found: {len(pyc_files)}")
    if pyc_files:
        print("First 5:")
        for f in pyc_files[:5]:
            print(f"  - {f}")

if __name__ == "__main__":
    main()
