#!/usr/bin/env python3
import os
import hashlib
import sys
import difflib
from collections import defaultdict

def get_sha256(filepath):
    h = hashlib.sha256()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(8192):
                h.update(chunk)
        return h.hexdigest()
    except Exception:
        return None

def get_text_content(filepath):
    try:
        with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    except Exception:
        return None

def check_db_states(root_dir):
    dbs = ["cortex.db", ".cortex/cortex.db", "agent_memory.db", "cognitive_state.db"]
    db_info = []
    for db in dbs:
        path = os.path.join(root_dir, db)
        if os.path.exists(path):
            stat = os.stat(path)
            db_info.append({
                "path": db,
                "size": stat.st_size,
                "mtime": stat.st_mtime
            })
    return db_info

def main():
    root_dir = "/Users/borjafernandezangulo/borjamoskv/Teorema-Robinson-Moskv"
    ignore_dirs = {".git", ".venv", ".mypy_cache", ".pytest_cache", ".ruff_cache", "target", "node_modules", "obj", "bin"}
    
    all_files = []
    file_hashes = defaultdict(list)
    
    for dirpath, dirnames, filenames in os.walk(root_dir):
        dirnames[:] = [d for d in dirnames if d not in ignore_dirs]
        for filename in filenames:
            full_path = os.path.join(dirpath, filename)
            rel_path = os.path.relpath(full_path, root_dir)
            if os.path.islink(full_path) or os.path.getsize(full_path) == 0:
                continue
            all_files.append(rel_path)
            sha = get_sha256(full_path)
            if sha:
                file_hashes[sha].append(rel_path)
                
    # 1. Exact duplicates
    exact_duplicates = []
    for sha, paths in file_hashes.items():
        if len(paths) > 1:
            exact_duplicates.append(paths)
            
    # 2. Near duplicates (focusing on code & text files)
    text_files = [f for f in all_files if f.endswith(('.py', '.go', '.rs', '.hs', '.md', '.yaml', '.yml', '.json', '.pl', '.lean'))]
    near_duplicates = []
    
    # We compare pairs of text files with the same base name first (most common case for copy-paste)
    by_basename = defaultdict(list)
    for f in text_files:
        by_basename[os.path.basename(f)].append(f)
        
    for basename, paths in by_basename.items():
        if len(paths) > 1:
            # Compare contents of each pair
            for i in range(len(paths)):
                for j in range(i+1, len(paths)):
                    p1 = os.path.join(root_dir, paths[i])
                    p2 = os.path.join(root_dir, paths[j])
                    c1 = get_text_content(p1)
                    c2 = get_text_content(p2)
                    if c1 and c2:
                        # compute simple ratio
                        ratio = difflib.SequenceMatcher(None, c1, c2).real_quick_ratio()
                        if ratio > 0.8:
                            # compute exact ratio
                            ratio = difflib.SequenceMatcher(None, c1, c2).ratio()
                            if ratio > 0.8:
                                near_duplicates.append((paths[i], paths[j], round(ratio, 4)))
                                
    # 3. Database status check
    db_status = check_db_states(root_dir)
    
    # Output report in YAML format
    print("---")
    print("redundancy_audit_report:")
    print("  exact_duplicates:")
    if exact_duplicates:
        for group in exact_duplicates:
            print("    - paths:")
            for p in group:
                print(f"        - {p}")
    else:
        print("    []")
        
    print("  near_duplicates:")
    if near_duplicates:
        for p1, p2, ratio in near_duplicates:
            print("    - file_1:", p1)
            print("      file_2:", p2)
            print("      similarity_ratio:", ratio)
    else:
        print("    []")
        
    print("  database_instances:")
    for db in db_status:
        print(f"    - path: {db['path']}")
        print(f"      size_bytes: {db['size']}")
        print(f"      last_modified: {db['mtime']}")
    print("...")

if __name__ == "__main__":
    main()
