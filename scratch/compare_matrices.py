import os
import difflib

def main():
    root = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv"
    paths = [
        "axioms/ddd/matrix.md",
        "axioms/autoreferential/matrix.md",
        "axioms/semantics/matrix.md",
        "axioms/ontology/matrix.md"
    ]
    
    contents = {}
    for p in paths:
        full_p = os.path.join(root, p)
        if os.path.exists(full_p):
            with open(full_p, 'r', encoding='utf-8') as f:
                contents[p] = f.read()
        else:
            print(f"Path not found: {p}")
            
    for i in range(len(paths)):
        for j in range(i+1, len(paths)):
            p1 = paths[i]
            p2 = paths[j]
            if p1 in contents and p2 in contents:
                ratio = difflib.SequenceMatcher(None, contents[p1], contents[p2]).ratio()
                print(f"{p1} vs {p2}: {ratio:.4f}")

if __name__ == "__main__":
    main()
