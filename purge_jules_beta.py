import os
import re
import glob

DIR = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv/artifacts/substack_archive_200/"

def purge():
    files = glob.glob(os.path.join(DIR, "**", "*.md"), recursive=True)
    count = 0
    for f in files:
        with open(f, 'r', encoding='utf-8') as file:
            content = file.read()
        
        orig = content
        
        # pattern 1: | *CORTEX-TAINT:* <anything not |>
        content = re.sub(r'\|\s*\*CORTEX-TAINT:\*\s*[^|\n]+', '', content)
        
        # pattern 2: [CORTEX-TAINT:<anything not ]>]
        content = re.sub(r'\[CORTEX-TAINT:[^\]\n]+\]', '', content)
        
        # cleanup CORTEX_TAINT: prefix if left standalone
        content = re.sub(r'CORTEX_TAINT:\s*\n', '\n', content)
        content = re.sub(r'CORTEX_TAINT:\s*$', '', content, flags=re.MULTILINE)
        content = re.sub(r'CORTEX_TAINT:\s*', '', content)
        
        # cleanup double pipes
        content = re.sub(r'\|\s*\|', '|', content)
        
        if content != orig:
            with open(f, 'w', encoding='utf-8') as file:
                file.write(content)
            count += 1
            
    print(f"Purged {count} files.")

if __name__ == "__main__":
    purge()
