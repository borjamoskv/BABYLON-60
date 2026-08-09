# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
Unpack Source Maps - Reconstruct original source code tree from inline Base64 source maps or external .map files
"""

import sys
import os
import re
import json
import base64

def unpack_source_map(file_path: str, output_dir: str = "scratch/unpacked_sources"):
    if not os.path.exists(file_path):
        print(f"[!] File not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    print(f"[*] Scanning {file_path} for inline or external Source Maps...")

    # Pattern for inline Base64 source map
    b64_matches = re.findall(r'//#\s*sourceMappingURL=data:application/json;choice=glsl;base64,([a-zA-Z0-9+/=]+)', text)
    if not b64_matches:
        b64_matches = re.findall(r'//#\s*sourceMappingURL=data:application/json;base64,([a-zA-Z0-9+/=]+)', text)

    if b64_matches:
        print(f"[+] Found {len(b64_matches)} inline Base64 source map(s). Processing...")
        for i, b64_data in enumerate(b64_matches):
            try:
                decoded_json = base64.b64decode(b64_data).decode("utf-8", errors="ignore")
                smap = json.loads(decoded_json)
                extract_sources_from_json(smap, output_dir)
            except Exception as e:
                print(f"[!] Failed to parse source map #{i+1}: {e}")
    else:
        # Search for external sourceMappingURL comment
        ext_matches = re.findall(r'//#\s*sourceMappingURL=([^\s]+)', text)
        if ext_matches:
            print(f"[+] Found external sourceMap reference(s): {ext_matches}")
            print("    Fetch the .map file and pass it directly to this script.")
        else:
            print("[-] No source maps detected in file.")

def extract_sources_from_json(smap: dict, output_dir: str):
    sources = smap.get("sources", [])
    contents = smap.get("sourcesContent", [])

    print(f"[+] Extracting {len(sources)} source files to {output_dir}...")
    extracted_count = 0

    for src_path, src_content in zip(sources, contents):
        if not src_content:
            continue

        # Clean relative paths
        clean_rel = src_path.replace("webpack://", "").replace("file://", "").strip("/")
        clean_rel = re.sub(r'^\.\.\/', '', clean_rel)
        clean_rel = re.sub(r'^\.\/', '', clean_rel)

        target_file = os.path.join(output_dir, clean_rel)
        os.makedirs(os.path.dirname(target_file), exist_ok=True)

        with open(target_file, "w", encoding="utf-8", errors="ignore") as f:
            f.write(src_content)
        extracted_count += 1

    print(f"[✓] Successfully extracted {extracted_count} original source file(s) into {output_dir}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 unpack_sourcemaps.py <PATH_TO_JS_OR_MAP_FILE> [OUTPUT_DIR]")
        sys.exit(1)

    out = sys.argv[2] if len(sys.argv) > 2 else "scratch/unpacked_sources"
    unpack_source_map(sys.argv[1], out)
