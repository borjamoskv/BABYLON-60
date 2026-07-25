import sys
from pathlib import Path


def validate_luhmann_post() -> None:
    project_root = Path(__file__).resolve().parent.parent
    target_file = project_root / "docs" / "substack_luhmann.md"
    if not target_file.exists():
        print(f"[-] Validation Failed: File {target_file} does not exist.")
        sys.exit(1)
    with open(target_file, encoding="utf-8") as f:
        content = f.read()
    print(f"[🔍] Auditing: {target_file}")
    if "|" in content:
        lines = content.splitlines()
        for i, line in enumerate(lines):
            if "|" in line and ("--" in line or ":" in line):
                print(f"[-] Validation Failed: Found markdown table on line {i + 1}: '{line}'")
                sys.exit(1)
    keywords = [
        "exergía",
        "anergía",
        "activo",
        "ip",
        "gatekeeper",
        "entropía",
        "isomorfismo",
        "espacio latente",
        "autopoiesis",
    ]
    content_lower = content.lower()
    for word in keywords:
        if word not in content_lower:
            print(f"[-] Validation Failed: Missing mandatory keyword '{word}'")
            sys.exit(1)
    footer_header = "⚡ [CORTEX C5-REAL] Sinergias de Exergía Máxima (Top 99.99):"
    if footer_header not in content:
        print("[-] Validation Failed: Missing exact footer header")
        sys.exit(1)
    mandatory_link = "- [Un hombre blanco y heterosexual](https://substack.com/home/post/p-204785962)"
    if mandatory_link not in content:
        print("[-] Validation Failed: Missing mandatory link to 'Un hombre blanco y heterosexual'")
        sys.exit(1)
    print(
        "[🟢] C5-REAL: Substack Article Validated 100%. Zero tables, all keywords and footer links match the OMEGA doctrine."
    )
    sys.exit(0)


if __name__ == "__main__":
    validate_luhmann_post()
