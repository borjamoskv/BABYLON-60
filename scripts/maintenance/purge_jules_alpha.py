# C5-REAL EXERGY CERTIFIED
import os
import re
import glob

target_dir = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/artifacts/substack_archive/"
md_files = glob.glob(os.path.join(target_dir, "**", "*.md"), recursive=True)

def purge_taint(content):
    # Pattern for Substack metadata style
    content = re.sub(r"\|\s*\*CORTEX-TAINT:\*\s*`[^`]+`\s*", "", content)
    # Pattern for ANERGY reports etc.
    content = re.sub(r"\[CORTEX-TAINT:[^\]]+\]", "", content)
    # Clean up any empty CORTEX_TAINT labels
    content = re.sub(r"^CORTEX_TAINT:\s*$", "", content, flags=re.MULTILINE)
    return content

purged_count = 0
for filepath in md_files:
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    new_content = purge_taint(content)

    if new_content != content:
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(new_content)
        print(f"Purged: {filepath}")
        purged_count += 1

print(f"PURGE COMPLETE. Files purged: {purged_count}")
