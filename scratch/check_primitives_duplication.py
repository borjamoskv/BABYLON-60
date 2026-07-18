import os

def main():
    root = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv"
    primitives_dir = os.path.join(root, "primitives")
    
    # List files in primitives
    files = [f for f in os.listdir(primitives_dir) if f.endswith(".go") and f != "primitives.go" and not f.endswith("_test.go")]
    print("Individual Go primitive files:")
    for f in files:
        path = os.path.join(primitives_dir, f)
        print(f"  - {f} (size={os.path.getsize(path)} bytes)")
        
    master_path = os.path.join(primitives_dir, "primitives.go")
    if os.path.exists(master_path):
        print(f"\nMaster primitives.go size: {os.path.getsize(master_path)} bytes")
        
        # Check if contents of individual files exist inside master primitives.go
        with open(master_path, 'r', encoding='utf-8', errors='ignore') as master_file:
            master_content = master_file.read()
            
        for f in files:
            path = os.path.join(primitives_dir, f)
            with open(path, 'r', encoding='utf-8', errors='ignore') as individual_file:
                # Read first few lines of helper package implementation (skipping package declaration)
                indiv_content = individual_file.read()
                # strip package declaration
                if "package primitives" in indiv_content:
                    body = indiv_content.split("package primitives", 1)[1].strip()
                    # Check first 500 characters of body
                    sample = body[:500]
                    if sample in master_content:
                        print(f"  [DUP DETECTED] Content of {f} is duplicated inside master primitives.go!")
                    else:
                        print(f"  [OK] Content of {f} is not duplicate (or structured differently) in master primitives.go.")

if __name__ == "__main__":
    main()
