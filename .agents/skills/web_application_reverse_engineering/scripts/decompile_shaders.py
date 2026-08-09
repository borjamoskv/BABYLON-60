# C5-REAL EXERGY CERTIFIED
#!/usr/bin/env python3
"""
Decompile Shaders - Extract & Dissect GLSL Vertex & Fragment Shaders from JS Bundles or HTML
"""

import sys
import re
import os

def extract_shaders(file_path: str):
    if not os.path.exists(file_path):
        print(f"[!] File not found: {file_path}")
        return

    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
        text = f.read()

    print(f"[*] Scanning {file_path} ({len(text)} bytes) for GLSL Shaders...")

    # Pattern for Vertex Shaders
    vertex_shaders = re.findall(r'(?:attribute|in)\s+vec[234]\s+\w+;[^\`]*?void\s+main\s*\(\s*\)\s*\{[^\}]+\}', text, re.DOTALL)

    # Pattern for Fragment Shaders
    fragment_shaders = re.findall(r'(?:uniform|varying|in)\s+sampler2D\s+\w+;[^\`]*?gl_FragColor[^\}]+\}', text, re.DOTALL)

    # General GLSL multiline string literals
    glsl_blocks = re.findall(r'[\"\'\`]\s*(?:#version\s+\d+\s+es|precision\s+(?:highp|mediump|lowp)\s+float;)[^\`\"\'\n]*?gl_Position|gl_FragColor[^\`\"\'\n]*?[\"\'\`]', text, re.DOTALL)

    print(f"[+] Vertex Shaders found: {len(vertex_shaders)}")
    for i, vs in enumerate(vertex_shaders[:5]):
        print(f"\n--- VERTEX SHADER #{i+1} ---")
        print(vs[:300] + ("..." if len(vs) > 300 else ""))

    print(f"\n[+] Fragment Shaders found: {len(fragment_shaders)}")
    for i, fs in enumerate(fragment_shaders[:5]):
        print(f"\n--- FRAGMENT SHADER #{i+1} ---")
        print(fs[:300] + ("..." if len(fs) > 300 else ""))

    print(f"\n[+] GLSL Blocks found: {len(glsl_blocks)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 decompile_shaders.py <path_to_js_or_html>")
        sys.exit(1)
    extract_shaders(sys.argv[1])
