#!/usr/bin/env python3
import os
import hashlib
import sys
from collections import defaultdict

def get_sha256(filepath):
    h = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except Exception as e:
        return None

def main():
    root_dir = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv"
    ignore_dirs = {".git", ".venv", ".mypy_cache", ".pytest_cache", ".ruff_cache", "target", "node_modules", "obj", "bin"}
    
    file_hashes = defaultdict(list)
    file_names = defaultdict(list)
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        # prune ignored directories in-place
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(full_path, root_dir)
            
            # Skip symlinks and zero byte files
            if os.path.islink(full_path) or os.path.getsize(full_path) == 0:
                continue
                
            sha = get_sha256(full_path)
            if sha:
                file_hashes[sha].append(rel_path)
            file_names[filename].append(rel_path)
            
    print("=== EXACT DUPLICATES BY HASH ===")
    has_duplicates = False
    for sha, paths in file_hashes.items():
        if len(paths) > 1:
            has_duplicates = True
            print(f"Hash: {sha}")
            for p in paths:
                print(f"  - {p}")
                
    if not has_duplicates:
        print("No exact duplicate files found.")
        
    print("\n=== DUPLICATE FILENAMES IN DIFFERENT PATHS ===")
    has_dup_names = False
    for name, paths in file_names.items():
        if len(paths) > 1:
            # Skip checking if they are the exact same files (which would have been listed above)
            # but list them here to show name collision
            has_dup_names = True
            print(f"Filename: {name}")
            for p in paths:
                print(f"  - {p}")
                
    if not has_dup_names:
        print("No duplicate filenames found.")

if __name__ == "__main__":
    main()
