# C5-REAL: Verifies markdown file formats, structural tables, and references inside the ontology registry.
import os
import re
import sys
import glob

ONTOLOGY_DIR: str = os.path.dirname(os.path.abspath(__file__))
FILES_TO_CHECK: list[str] = [
    os.path.basename(f) for f in glob.glob(os.path.join(ONTOLOGY_DIR, "*.md"))
]


def validate_file(filename: str, all_ids: set[str]) -> bool:
    filepath: str = os.path.join(ONTOLOGY_DIR, filename)
    assert os.path.exists(filepath), f"El archivo de ontología debe existir: {filename}"

    with open(filepath, "r", encoding="utf-8") as f:
        content: str = f.read()

    errors: int = 0
    sys.stdout.write(f"[*] Auditing {filename}...\n")

    if not content.strip():
        sys.stdout.write("  [ERROR] File is empty.\n")
        return False

    if "borjamoskv" in content.lower() or "borja moskv" in content.lower():
        sys.stdout.write("  [OK] Creator signature verified.\n")
    else:
        sys.stdout.write("  [ERROR] Missing creator signature (Rule Γ1).\n")
        errors += 1

    table_declarations: list[str] = re.findall(
        r"\|\s*([A-Z]+(?:-CAT)?-\d{3})\s*\|", content
    )
    list_declarations: list[str] = re.findall(
        r"\*\s*\*\*\[([A-Z]+(?:-CAT)?-\d{3})\]\*\*", content
    )
    declarations: list[str] = table_declarations + list_declarations

    declarations = [d for d in declarations if d != "ID"]

    for item_id in declarations:
        if item_id in all_ids:
            sys.stdout.write(f"  [ERROR] Duplicate definition of ID: {item_id}\n")
            errors += 1
        else:
            all_ids.add(item_id)

    link_pattern: re.Pattern = re.compile(r"\[.*?\]\(([^)]+)\)")
    links: list[str] = link_pattern.findall(content)
    for link in links:
        clean_path: str = link.replace("file://", "").split("#")[0]

        if not os.path.isabs(clean_path):
            clean_path = os.path.join(ONTOLOGY_DIR, clean_path)

        if not os.path.exists(clean_path):
            sys.stdout.write(f"  [ERROR] Link path does not exist: {clean_path}\n")
            errors += 1

    return errors == 0


def main() -> None:
    success: bool = True
    all_ids: set[str] = set()
    for f in FILES_TO_CHECK:
        success_file: bool = validate_file(f, all_ids)
        if not success_file:
            success = False

    if not success:
        sys.stdout.write("[-] Ontology audit failed.\n")
        sys.exit(1)

    sys.stdout.write(
        f"[+] All core ontology documents successfully verified. Integrity = 1.0 (Checked {len(all_ids)} declared IDs)\n"
    )


if __name__ == "__main__":
    main()
